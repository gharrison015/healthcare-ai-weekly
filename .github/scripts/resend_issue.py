#!/usr/bin/env python3
"""Re-render a published issue through the current template and send to
every active Supabase subscriber.

One-shot production tool for when the template has changed mid-week and
new subscribers (or existing ones) need the updated format. Uses the
exact same SMTP + unsubscribe-token mechanics as send_newsletter.py.

Usage: resend_issue.py YYYY-MM-DD

Env vars (required):
  SMTP_USER, SMTP_PASSWORD
  SUPABASE_URL, SUPABASE_KEY
"""

from __future__ import annotations

import json
import os
import smtplib
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PIPELINE_DIR = REPO_ROOT / "pipeline"
CONTENT_DIR = REPO_ROOT / "content"

sys.path.insert(0, str(PIPELINE_DIR))
from generator.email_generator import render_email, LANDING_PAGE_URL, format_subject_line

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
FROM_DISPLAY_NAME = "Healthcare AI Weekly"
SITE_URL = "https://healthcareaibrief.com"


def compute_week_range(date_str: str) -> str:
    end = datetime.strptime(date_str, "%Y-%m-%d")
    start = end - timedelta(days=7)
    return f"{start.strftime('%B %d')} - {end.strftime('%B %d, %Y')}"


def fetch_subscribers(supabase_url: str, supabase_key: str) -> list[dict]:
    url = f"{supabase_url}/rest/v1/subscribers?active=eq.true&select=email,unsubscribe_token"
    req = urllib.request.Request(url, headers={
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def build_email(subject, from_addr, to_addr, html_body, unsub_token=None):
    body = html_body
    if unsub_token and "Unsubscribe" not in body:
        unsub_url = f"{SITE_URL}/api/unsubscribe?token={unsub_token}"
        body = body.replace(
            "</body>",
            f'<div style="text-align:center;padding:12px;font-size:12px;color:#94a3b8;">'
            f'<a href="{unsub_url}" style="color:#94a3b8;text-decoration:underline;">Unsubscribe</a></div></body>',
        )
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{FROM_DISPLAY_NAME} <{from_addr}>"
    msg["To"] = to_addr
    if unsub_token:
        msg["List-Unsubscribe"] = f"<{SITE_URL}/api/unsubscribe?token={unsub_token}>"
    msg.attach(MIMEText("This email is best viewed in an HTML-capable email client.", "plain"))
    msg.attach(MIMEText(body, "html"))
    return msg


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: resend_issue.py YYYY-MM-DD", file=sys.stderr)
        return 2
    date_str = sys.argv[1]

    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    missing = [k for k, v in {
        "SMTP_USER": user, "SMTP_PASSWORD": password,
        "SUPABASE_URL": supabase_url, "SUPABASE_KEY": supabase_key,
    }.items() if not v]
    if missing:
        print(f"error: missing env vars: {', '.join(missing)}", file=sys.stderr)
        return 1

    data_path = CONTENT_DIR / "issues" / date_str / "data.json"
    if not data_path.exists():
        print(f"error: {data_path} not found", file=sys.stderr)
        return 1

    curated = json.loads(data_path.read_text())
    week_range = curated.get("week_range") or compute_week_range(date_str)
    curated["week_range"] = week_range

    landing = f"{LANDING_PAGE_URL}?issue={date_str}"
    deep = f"{LANDING_PAGE_URL}/news/{date_str}"
    html = render_email(curated, landing_url=landing, deep_dive_url=deep)
    subject = format_subject_line(week_range)

    subs = fetch_subscribers(supabase_url, supabase_key)
    if not subs:
        print("no active subscribers — nothing to send", file=sys.stderr)
        return 1

    print(f"re-sending {date_str} to {len(subs)} active subscriber(s):")
    sent = 0
    failed = 0
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        server.login(user, password)
        for sub in subs:
            addr = sub["email"]
            try:
                msg = build_email(subject, user, addr, html, sub.get("unsubscribe_token"))
                server.sendmail(user, [addr], msg.as_string())
                sent += 1
                print(f"  sent -> {addr}")
            except Exception as e:
                failed += 1
                print(f"  FAILED -> {addr}: {e}")

    print(f"done: {sent} sent, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Re-render a published issue through the current template and send to
every active Supabase subscriber.

One-shot production tool for when the template has changed mid-week and
new subscribers (or existing ones) need the updated format. Uses the
exact same Resend + unsubscribe-token mechanics as send_newsletter.py.

Usage: resend_issue.py YYYY-MM-DD

Env vars (required):
  RESEND_API_KEY
  SUPABASE_URL, SUPABASE_KEY
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PIPELINE_DIR = REPO_ROOT / "pipeline"
CONTENT_DIR = REPO_ROOT / "content"

sys.path.insert(0, str(PIPELINE_DIR))
from generator.email_generator import render_email, LANDING_PAGE_URL, format_subject_line

FROM_ADDRESS = "newsletter@healthcareaibrief.com"
FROM_DISPLAY_NAME = "Healthcare AI Weekly"
SITE_URL = "https://healthcareaibrief.com"
RESEND_URL = "https://api.resend.com/emails"
SEND_DELAY_SECONDS = 0.6


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


def inject_unsubscribe(html_body: str, unsub_token: str | None) -> str:
    if not unsub_token or "Unsubscribe" in html_body:
        return html_body
    unsub_url = f"{SITE_URL}/api/unsubscribe?token={unsub_token}"
    footer = (
        f'<div style="text-align:center;padding:12px;font-size:12px;color:#94a3b8;">'
        f'<a href="{unsub_url}" style="color:#94a3b8;text-decoration:underline;">Unsubscribe</a></div>'
    )
    if "</body>" in html_body:
        return html_body.replace("</body>", footer + "</body>")
    return html_body + footer


def send_via_resend(api_key: str, to_addr: str, subject: str, html: str, unsub_token: str | None) -> None:
    body = {
        "from": f"{FROM_DISPLAY_NAME} <{FROM_ADDRESS}>",
        "to": [to_addr],
        "subject": subject,
        "html": html,
    }
    if unsub_token:
        body["headers"] = {
            "List-Unsubscribe": f"<{SITE_URL}/api/unsubscribe?token={unsub_token}>",
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
        }
    req = urllib.request.Request(
        RESEND_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "healthcare-ai-weekly/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        resp.read()


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: resend_issue.py YYYY-MM-DD", file=sys.stderr)
        return 2
    date_str = sys.argv[1]

    api_key = os.environ.get("RESEND_API_KEY")
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    missing = [k for k, v in {
        "RESEND_API_KEY": api_key,
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
    for sub in subs:
        addr = sub["email"]
        token = sub.get("unsubscribe_token")
        try:
            personalized = inject_unsubscribe(html, token)
            send_via_resend(api_key, addr, subject, personalized, token)
            sent += 1
            print(f"  sent -> {addr}")
        except urllib.error.HTTPError as e:
            failed += 1
            detail = e.read().decode("utf-8", errors="replace")
            print(f"  FAILED -> {addr}: {e.code} {detail}")
        except Exception as e:
            failed += 1
            print(f"  FAILED -> {addr}: {e}")
        time.sleep(SEND_DELAY_SECONDS)

    print(f"done: {sent} sent, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

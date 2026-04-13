#!/usr/bin/env python3
"""Send the weekly newsletter to all active subscribers via Gmail SMTP.

Usage: send_newsletter.py YYYY-MM-DD

Env vars (required):
  SMTP_USER          Sending Gmail address
  SMTP_PASSWORD      Gmail App Password (16 chars, no spaces)
  SUPABASE_URL       Supabase project URL
  SUPABASE_KEY       Supabase service role key (reads subscribers table)

Env vars (optional):
  SMTP_TO            Fallback recipient if no subscribers (default: gharrison@guidehouse.com)

Reads pipeline/data/issues/<date>/email.html, fetches active subscribers
from Supabase, and sends a personalized email (with unsubscribe link) to each.
"""

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

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
DEFAULT_TO = "gharrison@guidehouse.com"
FROM_DISPLAY_NAME = "Healthcare AI Weekly"
SITE_URL = "https://healthcareaibrief.com"


def format_subject(date_str: str) -> str:
    end = datetime.strptime(date_str, "%Y-%m-%d")
    start = end - timedelta(days=7)
    display = f"{start.strftime('%B %d')} - {end.strftime('%B %d, %Y')}"
    return f"Healthcare AI Weekly: Week of {display}"


def fetch_subscribers(supabase_url: str, supabase_key: str) -> list[dict]:
    """Fetch active subscribers from Supabase REST API (no SDK needed)."""
    url = f"{supabase_url}/rest/v1/subscribers?active=eq.true&select=email,unsubscribe_token"
    req = urllib.request.Request(url, headers={
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as e:
        print(f"warning: failed to fetch subscribers: {e}")
        return []


def build_email(subject: str, from_addr: str, to_addr: str, html_body: str, unsub_token: str | None = None) -> MIMEMultipart:
    """Build a personalized email with optional unsubscribe link."""
    body = html_body
    if unsub_token:
        unsub_url = f"{SITE_URL}/api/unsubscribe?token={unsub_token}"
        body = html_body.replace("</body>", "")  # let the template handle it via Jinja
        # If the template already has the unsubscribe placeholder, it's handled.
        # Otherwise, inject before closing body tag as fallback.
        if unsub_url not in body and "Unsubscribe" not in body:
            body += f'<div style="text-align:center;padding:12px;font-size:12px;color:#94a3b8;"><a href="{unsub_url}" style="color:#94a3b8;text-decoration:underline;">Unsubscribe</a></div>'
            body += "</body>"
        elif "</body>" not in body:
            body += "</body>"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{FROM_DISPLAY_NAME} <{from_addr}>"
    msg["To"] = to_addr
    msg["List-Unsubscribe"] = f"<{SITE_URL}/api/unsubscribe?token={unsub_token}>" if unsub_token else ""
    msg.attach(MIMEText("This email is best viewed in an HTML-capable email client.", "plain"))
    msg.attach(MIMEText(body, "html"))
    return msg


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: send_newsletter.py YYYY-MM-DD", file=sys.stderr)
        return 2
    date_str = sys.argv[1]

    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    if not user or not password:
        print("error: SMTP_USER and SMTP_PASSWORD must be set", file=sys.stderr)
        return 1

    email_html_path = PIPELINE_DIR / "data" / "issues" / date_str / "email.html"
    if not email_html_path.exists():
        print(f"error: {email_html_path} not found", file=sys.stderr)
        return 1

    html_body = email_html_path.read_text(encoding="utf-8")
    subject = format_subject(date_str)

    # Build recipient list: Supabase subscribers + always include Greg
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_KEY", "")
    fallback_to = os.environ.get("SMTP_TO", DEFAULT_TO)

    recipients: list[dict] = []
    if supabase_url and supabase_key:
        subscribers = fetch_subscribers(supabase_url, supabase_key)
        for sub in subscribers:
            recipients.append({"email": sub["email"], "token": sub.get("unsubscribe_token")})
        print(f"fetched {len(subscribers)} active subscribers from Supabase")

    # Always send to Greg (no unsubscribe link for him)
    greg_emails = {r["email"] for r in recipients}
    if fallback_to not in greg_emails:
        recipients.append({"email": fallback_to, "token": None})

    if not recipients:
        print("error: no recipients", file=sys.stderr)
        return 1

    # Send to all recipients
    sent = 0
    failed = 0
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        server.login(user, password)
        for recipient in recipients:
            addr = recipient["email"]
            try:
                msg = build_email(subject, user, addr, html_body, recipient.get("token"))
                server.sendmail(user, [addr], msg.as_string())
                sent += 1
            except Exception as e:
                print(f"warning: failed to send to {addr}: {e}")
                failed += 1

    print(f"sent {sent} emails, {failed} failures ({len(recipients)} total recipients)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

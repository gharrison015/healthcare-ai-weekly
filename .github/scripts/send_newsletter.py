#!/usr/bin/env python3
"""Send the weekly newsletter to all active subscribers via Resend.

Usage: send_newsletter.py YYYY-MM-DD

Env vars (required):
  RESEND_API_KEY     Resend API key (account with healthcareaibrief.com verified)
  SUPABASE_URL       Supabase project URL
  SUPABASE_KEY       Supabase service role key (reads subscribers table)

Env vars (optional):
  SMTP_TO            Fallback recipient if no subscribers (default: gharrison@guidehouse.com)

Reads pipeline/data/issues/<date>/email.html, fetches active subscribers
from Supabase, and sends a personalized email (with unsubscribe link) to each.
"""

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

FROM_ADDRESS = "newsletter@healthcareaibrief.com"
FROM_DISPLAY_NAME = "Healthcare AI Weekly"
DEFAULT_TO = "gharrison@guidehouse.com"
SITE_URL = "https://healthcareaibrief.com"
RESEND_URL = "https://api.resend.com/emails"
SEND_DELAY_SECONDS = 0.6  # stay under Resend free-tier 2 req/s


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


def inject_unsubscribe(html_body: str, unsub_token: str | None) -> str:
    if not unsub_token:
        return html_body
    unsub_url = f"{SITE_URL}/api/unsubscribe?token={unsub_token}"
    if unsub_url in html_body or "Unsubscribe" in html_body:
        return html_body
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
        resp.read()  # drain


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: send_newsletter.py YYYY-MM-DD", file=sys.stderr)
        return 2
    date_str = sys.argv[1]

    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        print("error: RESEND_API_KEY must be set", file=sys.stderr)
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

    sent = 0
    failed = 0
    for recipient in recipients:
        addr = recipient["email"]
        token = recipient.get("token")
        try:
            personalized = inject_unsubscribe(html_body, token)
            send_via_resend(api_key, addr, subject, personalized, token)
            sent += 1
        except urllib.error.HTTPError as e:
            failed += 1
            detail = e.read().decode("utf-8", errors="replace")
            print(f"warning: failed to send to {addr}: {e.code} {detail}")
        except Exception as e:
            failed += 1
            print(f"warning: failed to send to {addr}: {e}")
        time.sleep(SEND_DELAY_SECONDS)

    print(f"sent {sent} emails, {failed} failures ({len(recipients)} total recipients)")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

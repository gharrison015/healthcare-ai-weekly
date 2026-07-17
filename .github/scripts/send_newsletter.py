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


def claim_send(supabase_url: str, supabase_key: str, date_str: str) -> str:
    """Atomically claim this issue_date so it can never be sent twice.

    Inserts one row into newsletter_sends keyed by issue_date (PRIMARY KEY).
    Returns:
      "claimed"      -> we own the send; caller MUST proceed to send.
      "already"      -> a prior run already claimed/sent this date; caller MUST
                        skip sending (the workflow still publishes the page).
      "unavailable"  -> the ledger is missing/unreachable after retries. We fail
                        OPEN (caller sends anyway, loudly) because a broken guard
                        must NEVER cause a missed Friday, delivery is the higher
                        priority. A duplicate here is far less likely than a miss:
                        the 409 dedup only fails to fire if the ledger is actually
                        down, and the stacked runs are serialized by the
                        concurrency group. This branch should be effectively dead
                        once the newsletter_sends table exists.
    """
    url = f"{supabase_url}/rest/v1/newsletter_sends"
    payload = json.dumps({"issue_date": date_str, "status": "claimed"}).encode("utf-8")

    last_detail = ""
    for attempt in range(1, 4):  # 3 tries for transient blips
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp.read()
            print(f"claimed send for {date_str} (newsletter_sends row created)")
            return "claimed"
        except urllib.error.HTTPError as e:
            if e.code == 409:
                print(f"send for {date_str} was already claimed by an earlier run, skipping send.")
                return "already"
            last_detail = f"{e.code} {e.read().decode('utf-8', errors='replace')}"
            # 4xx other than 409 (e.g. 404 missing table) won't fix on retry.
            if 400 <= e.code < 500:
                break
        except urllib.error.URLError as e:
            last_detail = str(e)
        if attempt < 3:
            time.sleep(3)

    print(
        f"WARNING: could not claim send guard for {date_str} after retries "
        f"({last_detail}). DOUBLE-SEND GUARD UNAVAILABLE, sending anyway to "
        f"honor the Friday delivery guarantee. Investigate the newsletter_sends table."
    )
    return "unavailable"


def finalize_send(supabase_url: str, supabase_key: str, date_str: str, sent_count: int) -> None:
    """Mark the claim as fully sent, recording how many emails went out."""
    url = f"{supabase_url}/rest/v1/newsletter_sends?issue_date=eq.{date_str}"
    payload = json.dumps({"status": "sent", "sent_count": sent_count}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
        method="PATCH",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
    except urllib.error.URLError as e:
        # Non-fatal: the row already guards against a resend; this is bookkeeping.
        print(f"warning: could not mark {date_str} as sent: {e}")


def release_claim(supabase_url: str, supabase_key: str, date_str: str) -> None:
    """Delete the claim so a later attempt can retry, used only when ZERO
    emails went out (total send failure), so we never strand the issue."""
    url = f"{supabase_url}/rest/v1/newsletter_sends?issue_date=eq.{date_str}"
    req = urllib.request.Request(
        url,
        headers={
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Prefer": "return=minimal",
        },
        method="DELETE",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
        print(f"released claim for {date_str} (0 emails sent) so a retry can re-send.")
    except urllib.error.URLError as e:
        print(f"warning: could not release claim for {date_str}: {e}")


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

    # DOUBLE-SEND GUARD: atomically claim this issue_date in Supabase BEFORE
    # sending a single email. This marker is durable and independent of the
    # git push (whose failure caused the 2026-07-17 double send). If the date
    # is already claimed, a prior run already sent it, skip and let the
    # workflow still publish the page (self-heals a send-ok/push-failed run).
    guard_claimed = False
    if supabase_url and supabase_key:
        outcome = claim_send(supabase_url, supabase_key, date_str)
        if outcome == "already":
            print(f"issue {date_str} already sent, no emails sent this run.")
            return 0
        guard_claimed = (outcome == "claimed")
    else:
        print("WARNING: no Supabase creds, DOUBLE-SEND GUARD DISABLED for this run.")

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

    # Finalize the durable guard. If ZERO emails went out (total failure),
    # release the claim so a later attempt can retry, otherwise the issue
    # would be stranded, claimed-but-never-delivered. If at least one email
    # went out, KEEP the claim so no run ever re-blasts the list; record it.
    if guard_claimed:
        if sent == 0:
            release_claim(supabase_url, supabase_key, date_str)
        else:
            finalize_send(supabase_url, supabase_key, date_str, sent)

    return 0 if sent > 0 else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Re-render the weekly email from published content and send ONLY to Greg.

Usage: send_test_email.py YYYY-MM-DD [recipient]

Reads `content/issues/<date>/data.json` (already-published curated data),
re-renders `email.html` through the current template (picking up any
template changes since the original send), and emails it to the single
test recipient. Never touches Supabase. Never commits anything.
"""

import json
import os
import sys
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
FROM_DISPLAY_NAME = "Healthcare AI Weekly (Test)"
DEFAULT_RECIPIENT = "gharrison@guidehouse.com"
RESEND_URL = "https://api.resend.com/emails"

# Hard-coded test allowlist. See CLAUDE.md "Test Email Policy".
# Never test-send to real subscribers — use only Greg's own addresses.
ALLOWED_TEST_RECIPIENTS = {
    "gharrison@guidehouse.com",
    "gharrison015@gmail.com",
}


def compute_week_range(date_str):
    end = datetime.strptime(date_str, "%Y-%m-%d")
    start = end - timedelta(days=7)
    return f"{start.strftime('%B %d')} - {end.strftime('%B %d, %Y')}"


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: send_test_email.py YYYY-MM-DD [recipient]", file=sys.stderr)
        return 2
    date_str = sys.argv[1]
    recipient = (sys.argv[2] if len(sys.argv) >= 3 else DEFAULT_RECIPIENT).strip().lower()

    if recipient not in ALLOWED_TEST_RECIPIENTS:
        allowed = ", ".join(sorted(ALLOWED_TEST_RECIPIENTS))
        print(
            f"error: recipient {recipient!r} not allowed. "
            f"Test sends must go to one of: {allowed}. See CLAUDE.md.",
            file=sys.stderr,
        )
        return 2

    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        print("error: RESEND_API_KEY must be set", file=sys.stderr)
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

    # Timestamp in subject so Outlook/Gmail don't thread consecutive tests.
    stamp = datetime.now().strftime("%H:%M")
    subject = f"[TEST {stamp}Z] {format_subject_line(week_range)}"

    body = {
        "from": f"{FROM_DISPLAY_NAME} <{FROM_ADDRESS}>",
        "to": [recipient],
        "subject": subject,
        "html": html,
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
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        print(f"error: Resend returned {e.code}: {detail}", file=sys.stderr)
        return 1

    print(f"sent test email for {date_str} -> {recipient} ({len(html)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

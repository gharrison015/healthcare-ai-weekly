#!/usr/bin/env python3
"""Re-render the weekly email from published content and send ONLY to Greg.

Usage: send_test_email.py YYYY-MM-DD [recipient]

Reads `content/issues/<date>/data.json` (already-published curated data),
re-renders `email.html` through the current template (picking up any
template changes since the original send), and emails it to the single
test recipient. Never touches Supabase. Never commits anything.
"""

import os
import smtplib
import sys
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PIPELINE_DIR = REPO_ROOT / "pipeline"
CONTENT_DIR = REPO_ROOT / "content"

# Make pipeline imports work
sys.path.insert(0, str(PIPELINE_DIR))
import json
from generator.email_generator import render_email, LANDING_PAGE_URL, format_subject_line

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
DEFAULT_RECIPIENT = "gharrison@guidehouse.com"
FROM_DISPLAY_NAME = "Healthcare AI Weekly (Test)"

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

    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    if not user or not password:
        print("error: SMTP_USER and SMTP_PASSWORD must be set", file=sys.stderr)
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

    subject = f"[TEST] {format_subject_line(week_range)}"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{FROM_DISPLAY_NAME} <{user}>"
    msg["To"] = recipient
    msg.attach(MIMEText("Test email — best viewed in HTML.", "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        server.login(user, password)
        server.sendmail(user, [recipient], msg.as_string())

    print(f"sent test email for {date_str} -> {recipient} ({len(html)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

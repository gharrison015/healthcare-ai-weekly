#!/usr/bin/env python3
"""Send the weekly newsletter via Gmail SMTP.

Usage: send_newsletter.py YYYY-MM-DD

Env vars:
  SMTP_USER       Sending Gmail address (e.g. gharrison015@gmail.com)
  SMTP_PASSWORD   Gmail App Password (16 chars, no spaces)
  SMTP_TO         Optional; defaults to gharrison@guidehouse.com

Reads pipeline/data/issues/<date>/email.html and sends it as a
multipart/alternative (plain + html) message over SMTP_SSL:465.

Note: Gmail ignores a spoofed From address, so the envelope From
is always the authenticated SMTP_USER. Only the display name is set.
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

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
DEFAULT_TO = "gharrison@guidehouse.com"
FROM_DISPLAY_NAME = "Healthcare AI Weekly"


def format_subject(date_str: str) -> str:
    # Mirrors pipeline/generator/email_generator.py::format_subject_line
    # but uses a colon instead of em dash, per the project's no-em-dash rule.
    end = datetime.strptime(date_str, "%Y-%m-%d")
    start = end - timedelta(days=7)
    display = f"{start.strftime('%B %d')} - {end.strftime('%B %d, %Y')}"
    return f"Healthcare AI Weekly: Week of {display}"


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: send_newsletter.py YYYY-MM-DD", file=sys.stderr)
        return 2
    date_str = sys.argv[1]

    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    to = os.environ.get("SMTP_TO", DEFAULT_TO)
    if not user or not password:
        print("error: SMTP_USER and SMTP_PASSWORD must be set", file=sys.stderr)
        return 1

    email_html_path = PIPELINE_DIR / "data" / "issues" / date_str / "email.html"
    if not email_html_path.exists():
        print(f"error: {email_html_path} not found", file=sys.stderr)
        return 1

    html_body = email_html_path.read_text(encoding="utf-8")
    plain_fallback = "This email is best viewed in an HTML-capable email client."

    msg = MIMEMultipart("alternative")
    msg["Subject"] = format_subject(date_str)
    msg["From"] = f"{FROM_DISPLAY_NAME} <{user}>"
    msg["To"] = to
    msg.attach(MIMEText(plain_fallback, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        server.login(user, password)
        server.sendmail(user, [to], msg.as_string())

    print(f"sent newsletter for {date_str} to {to}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Send a failure alert email via Resend when the weekly workflow fails.

Called from the workflow's `if: failure()` step. Sends to Greg's two
allowlisted addresses with a link to the failed run.

Env vars (required):
  RESEND_API_KEY
  GITHUB_REPOSITORY  (auto-set by Actions)
  GITHUB_RUN_ID      (auto-set by Actions)
  ISSUE_DATE         (the YYYY-MM-DD the run was for)
  TRIGGER_EVENT      (schedule | workflow_dispatch)
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
import urllib.error

ALERT_RECIPIENTS = ["gharrison@guidehouse.com", "gharrison015@gmail.com"]
RESEND_URL = "https://api.resend.com/emails"
FROM = "Healthcare AI Weekly <newsletter@healthcareaibrief.com>"


def main() -> int:
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        print("notify_failure: RESEND_API_KEY missing, cannot alert", file=sys.stderr)
        return 0

    repo = os.environ.get("GITHUB_REPOSITORY", "?")
    run_id = os.environ.get("GITHUB_RUN_ID", "?")
    issue_date = os.environ.get("ISSUE_DATE", "?")
    trigger = os.environ.get("TRIGGER_EVENT", "?")
    run_url = f"https://github.com/{repo}/actions/runs/{run_id}"

    subject = f"[ALERT] Healthcare AI Weekly workflow failed ({issue_date})"
    html = f"""
    <p><b>Weekly newsletter workflow failed.</b></p>
    <ul>
      <li>Issue date: {issue_date}</li>
      <li>Trigger: {trigger}</li>
      <li>Run: <a href="{run_url}">{run_url}</a></li>
    </ul>
    <p>The backup cron (Fri 13:00 UTC) will retry automatically if this
    is the primary 09:00 UTC run. If the backup also fails, manually
    dispatch the workflow with dry_run unchecked.</p>
    """.strip()

    body = json.dumps({
        "from": FROM,
        "to": ALERT_RECIPIENTS,
        "subject": subject,
        "html": html,
    }).encode("utf-8")

    req = urllib.request.Request(
        RESEND_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
        print(f"notify_failure: alert sent to {ALERT_RECIPIENTS}")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        print(f"notify_failure: Resend rejected alert: {e.code} {detail}", file=sys.stderr)
    except Exception as e:
        print(f"notify_failure: alert send failed: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())

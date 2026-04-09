import base64
import json
import subprocess
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def build_gws_send_command(to, subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["To"] = to
    msg["Subject"] = subject

    plain_text = "This email is best viewed in an HTML-capable email client."
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    body_json = json.dumps({"raw": raw})

    cmd = (
        f'gws gmail users messages send'
        f' --to "{to}"'
        f' --subject "{subject}"'
        f' --params \'{{"userId": "me"}}\''
        f' --json \'{body_json}\''
    )
    return cmd

def send_email(to, subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["To"] = to
    msg["Subject"] = subject

    plain_text = "This email is best viewed in an HTML-capable email client."
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    body_json = json.dumps({"raw": raw})
    params_json = json.dumps({"userId": "me"})

    result = subprocess.run(
        ["gws", "gmail", "users", "messages", "send",
         "--params", params_json,
         "--json", body_json],
        capture_output=True, text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"gws email send failed: {result.stderr}")

    print(f"Email sent to {to}")
    return result.stdout

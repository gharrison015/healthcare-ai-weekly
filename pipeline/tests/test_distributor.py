from distributor.send_email import build_gws_send_command
from distributor.publish_html import build_issue_path

def test_build_gws_send_command():
    cmd = build_gws_send_command(
        to="gharrison@guidehouse.com",
        subject="Healthcare AI Weekly — Week of April 4, 2026",
        html_body="<html><body>Test</body></html>",
    )
    assert "gws" in cmd
    assert "gharrison@guidehouse.com" in cmd
    assert "Healthcare AI Weekly" in cmd

def test_build_issue_path():
    path = build_issue_path("2026-04-04")
    assert path == "issues/2026-04-04"

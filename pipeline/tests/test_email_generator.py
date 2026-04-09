from generator.email_generator import render_email, format_subject_line

def test_format_subject_line():
    result = format_subject_line("April 4, 2026")
    assert result == "Healthcare AI Weekly — Week of April 4, 2026"

def test_render_email_contains_all_sections():
    curated = {
        "issue_date": "2026-04-04",
        "week_range": "March 30 - April 4, 2026",
        "editorial_summary": "Big week for clinical AI.",
        "sections": {
            "top_stories": [{
                "headline": "Epic Launches AI Agent",
                "priority": "act_now",
                "email_summary": "Epic just changed the game.",
                "source_article": {"url": "https://example.com", "source": "STAT"},
            }],
            "vbc_watch": [{
                "headline": "CMS Updates VBC Scoring",
                "email_summary": "New quality measures incoming.",
                "source_article": {"url": "https://example.com/vbc", "source": "CMS"},
            }],
            "deal_flow": [{
                "headline": "Abridge Acquired for $3B",
                "email_summary": "Ambient AI consolidation continues.",
                "source_article": {"url": "https://example.com/deal", "source": "Rock Health"},
            }],
            "did_you_know": [{
                "headline": "Claude 4 Can Read Medical Images",
                "one_liner": "Anthropic's latest model handles radiology.",
            }],
        },
        "trend_watch": {"emerging_signal": None},
    }
    html = render_email(curated)
    assert "Epic Launches AI Agent" in html
    assert "act_now" in html.lower() or "Act Now" in html
    assert "VBC" in html or "CMS Updates" in html
    assert "Abridge" in html
    assert "Claude 4" in html
    assert "Big week" in html

def test_render_email_is_valid_html():
    curated = {
        "issue_date": "2026-04-04",
        "week_range": "March 30 - April 4, 2026",
        "editorial_summary": "Test week.",
        "sections": {
            "top_stories": [{"headline": "Test", "priority": "watch_this", "email_summary": "Test.", "source_article": {"url": "#", "source": "Test"}}],
            "vbc_watch": [],
            "deal_flow": [],
            "did_you_know": [],
        },
        "trend_watch": {"emerging_signal": None},
    }
    html = render_email(curated)
    assert html.strip().startswith("<!DOCTYPE html") or html.strip().startswith("<html")
    assert "</html>" in html

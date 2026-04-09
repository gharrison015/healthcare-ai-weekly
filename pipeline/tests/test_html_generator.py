from generator.html_generator import render_deep_dive

def test_render_deep_dive_contains_all_sections():
    curated = {
        "issue_date": "2026-04-04",
        "week_range": "March 30 - April 4, 2026",
        "editorial_summary": "Big week.",
        "sections": {
            "top_stories": [{
                "headline": "Epic AI Agent",
                "priority": "act_now",
                "so_what": "Changes everything.",
                "deep_dive_notes": "Extended analysis of the Epic announcement and what it means for clinical workflows.",
                "risk_angle": "Integration costs could be brutal.",
                "source_article": {"url": "https://example.com", "source": "STAT", "title": "Epic Launches AI"},
                "connections": [],
            }],
            "vbc_watch": [{
                "headline": "CMS VBC Update",
                "so_what": "New measures.",
                "deep_dive_notes": "Deep analysis of CMS changes.",
                "source_article": {"url": "#", "source": "CMS", "title": "CMS Update"},
            }],
            "ma_partnerships": [{
                "headline": "Abridge Acquired",
                "so_what": "Consolidation.",
                "deep_dive_notes": "What the Abridge deal means.",
                "source_article": {"url": "#", "source": "Rock Health", "title": "Abridge Deal"},
            }],
            "did_you_know": [{
                "headline": "Claude 4 Reads X-rays",
                "explainer": "Detailed explanation of how Claude 4 handles medical imaging.",
            }],
        },
        "trend_watch": {"emerging_signal": "Ambient AI scribes appeared 4 of last 6 weeks."},
    }
    all_articles = [{"title": "Article 1", "source": "Test", "url": "#"}]

    html = render_deep_dive(curated, all_articles)
    assert "Epic AI Agent" in html
    assert "Extended analysis" in html
    assert "CMS VBC Update" in html
    assert "Abridge Acquired" in html
    assert "Claude 4" in html
    assert "Ambient AI scribes" in html
    assert "Article 1" in html

def test_render_deep_dive_has_toc():
    curated = {
        "issue_date": "2026-04-04",
        "week_range": "March 30 - April 4, 2026",
        "editorial_summary": "Test.",
        "sections": {
            "top_stories": [{"headline": "Test Story", "priority": "act_now", "deep_dive_notes": "Notes.", "source_article": {"url": "#", "source": "T", "title": "T"}}],
            "vbc_watch": [], "ma_partnerships": [], "did_you_know": [],
        },
        "trend_watch": {"emerging_signal": None},
    }
    html = render_deep_dive(curated, [])
    assert 'id="top-stories"' in html or 'id="toc"' in html

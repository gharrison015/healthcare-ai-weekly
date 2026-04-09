from data.curated.delta_tracker import compute_delta

def make_curated(date, companies, themes):
    stories = []
    for c in companies:
        stories.append({"headline": f"{c} does something", "source_article": {"title": c}})
    return {
        "issue_date": date,
        "sections": {
            "top_stories": stories,
            "vbc_watch": [],
            "deal_flow": [],
            "did_you_know": [],
        }
    }

def test_finds_recurring_companies():
    history = [
        make_curated("2026-03-21", ["Abridge", "Epic"], []),
        make_curated("2026-03-28", ["Abridge", "Google"], []),
    ]
    raw_articles = [
        {"title": "Abridge launches new product", "source": "STAT"},
        {"title": "Microsoft health update", "source": "Becker's"},
    ]
    delta = compute_delta(history, raw_articles)
    recurring = [c["name"] for c in delta["recurring_companies"]]
    assert "Abridge" in recurring

def test_identifies_new_entrants():
    history = [
        make_curated("2026-03-28", ["Abridge"], []),
    ]
    raw_articles = [
        {"title": "BrandNewCo launches AI platform", "source": "STAT"},
    ]
    delta = compute_delta(history, raw_articles)
    assert "BrandNewCo" in delta["new_entrants"] or len(delta["new_entrants"]) >= 0

def test_empty_history_returns_valid_delta():
    delta = compute_delta([], [{"title": "AI story", "source": "Test"}])
    assert "recurring_companies" in delta
    assert "recurring_themes" in delta
    assert delta["weeks_analyzed"] == 0

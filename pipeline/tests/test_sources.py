import json
import os

def test_sources_json_is_valid():
    path = os.path.join(os.path.dirname(__file__), "..", "collector", "sources.json")
    with open(path) as f:
        data = json.load(f)
    assert "feeds" in data
    assert "google_news_queries" in data
    assert "keywords" in data
    for feed in data["feeds"]:
        assert "name" in feed
        assert "url" in feed
        assert "tier" in feed
        assert "category" in feed

def test_sources_have_required_tiers():
    path = os.path.join(os.path.dirname(__file__), "..", "collector", "sources.json")
    with open(path) as f:
        data = json.load(f)
    tiers = {f["tier"] for f in data["feeds"]}
    assert "core" in tiers
    assert "policy" in tiers
    assert "general_ai" in tiers

def test_keywords_list_not_empty():
    path = os.path.join(os.path.dirname(__file__), "..", "collector", "sources.json")
    with open(path) as f:
        data = json.load(f)
    assert len(data["keywords"]) >= 5

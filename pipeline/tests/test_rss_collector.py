from unittest.mock import MagicMock
from collector.rss_collector import parse_feed_entry, build_google_news_url

def test_parse_feed_entry_extracts_fields():
    entry = MagicMock()
    entry.title = "Epic launches AI-powered clinical agent"
    entry.link = "https://example.com/article"
    entry.get.return_value = "Epic announced a new clinical AI agent today."
    entry.published_parsed = (2026, 4, 2, 10, 0, 0, 2, 92, 0)

    source = {"name": "Fierce Healthcare", "tier": "core", "category": "core"}
    keywords = ["AI", "clinical"]

    result = parse_feed_entry(entry, source, keywords)
    assert result is not None
    assert result["title"] == "Epic launches AI-powered clinical agent"
    assert result["source"] == "Fierce Healthcare"
    assert result["source_tier"] == "core"
    assert result["category"] == "core"
    assert result["url"] == "https://example.com/article"
    assert "AI" in result["keywords_matched"]
    assert "id" in result

def test_parse_feed_entry_returns_none_when_no_keyword_match():
    entry = MagicMock()
    entry.title = "Hospital cafeteria menu updated"
    entry.link = "https://example.com/food"
    entry.get.return_value = "New salad bar options available."
    entry.published_parsed = (2026, 4, 2, 10, 0, 0, 2, 92, 0)

    source = {"name": "Becker's", "tier": "core", "category": "core"}
    keywords = ["AI", "machine learning"]

    result = parse_feed_entry(entry, source, keywords)
    assert result is None

def test_parse_feed_entry_filters_old_articles():
    entry = MagicMock()
    entry.title = "AI in healthcare roundup"
    entry.link = "https://example.com/old"
    entry.get.return_value = "Old AI news."
    entry.published_parsed = (2026, 1, 1, 10, 0, 0, 2, 1, 0)

    source = {"name": "STAT News", "tier": "core", "category": "core"}
    keywords = ["AI"]

    result = parse_feed_entry(entry, source, keywords, max_age_days=7)
    assert result is None

def test_build_google_news_url():
    query = '"artificial intelligence" AND "healthcare"'
    url = build_google_news_url(query)
    assert "news.google.com/rss/search" in url
    assert "healthcare" in url

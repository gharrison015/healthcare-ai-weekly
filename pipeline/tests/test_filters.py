from collector.filters import deduplicate_articles, fuzzy_title_match

def test_deduplicate_by_url():
    articles = [
        {"id": "1", "url": "https://example.com/a", "title": "AI story", "source": "A", "source_tier": "core"},
        {"id": "2", "url": "https://example.com/a", "title": "AI story dupe", "source": "B", "source_tier": "core"},
        {"id": "3", "url": "https://example.com/b", "title": "Different story", "source": "C", "source_tier": "core"},
    ]
    result = deduplicate_articles(articles)
    assert len(result) == 2
    urls = [a["url"] for a in result]
    assert "https://example.com/a" in urls
    assert "https://example.com/b" in urls

def test_fuzzy_title_match_catches_similar():
    assert fuzzy_title_match(
        "OpenAI partners with Mayo Clinic on clinical AI",
        "OpenAI and Mayo Clinic announce clinical AI partnership"
    ) is True

def test_fuzzy_title_match_rejects_different():
    assert fuzzy_title_match(
        "OpenAI partners with Mayo Clinic",
        "Google launches new Pixel phone"
    ) is False

def test_deduplicate_prefers_higher_tier():
    articles = [
        {"id": "1", "url": "https://a.com/1", "title": "AI scribe saves time in clinics", "source": "Random Blog", "source_tier": "catch_all"},
        {"id": "2", "url": "https://b.com/2", "title": "AI scribe saves clinician time in clinics", "source": "STAT News", "source_tier": "core"},
    ]
    result = deduplicate_articles(articles)
    assert len(result) == 1
    assert result[0]["source"] == "STAT News"

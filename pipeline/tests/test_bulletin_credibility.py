from bulletin.credibility_checker import classify_source, check_credibility
from unittest.mock import patch


def test_classify_primary_source():
    article = {"link": "https://www.anthropic.com/blog/new-release", "source": "Anthropic", "title": "Anthropic Blog"}
    assert classify_source(article) == "primary"


def test_classify_tier1_source():
    article = {"link": "https://www.statnews.com/article", "source": "STAT News", "title": "STAT coverage"}
    assert classify_source(article) == "tier1"


def test_classify_tier2_source():
    article = {"link": "https://www.beckershospitalreview.com/article", "source": "Becker's", "title": "Becker update"}
    assert classify_source(article) == "tier2"


def test_classify_unknown_source():
    article = {"link": "https://randomblog.com/post", "source": "Random Blog", "title": "Some post"}
    assert classify_source(article) == "unknown"


def test_classify_fda_primary():
    article = {"link": "https://www.fda.gov/news-events/press-announcements/ai-clearance", "source": "FDA", "title": "FDA Clearance"}
    assert classify_source(article) == "primary"


def test_classify_google_primary():
    article = {"link": "https://blog.google.com/health-ai", "source": "Google", "title": "Google Blog"}
    assert classify_source(article) == "primary"


def test_classify_wsj_tier1():
    article = {"link": "https://wsj.com/articles/health", "source": "Wall Street Journal", "title": "WSJ article"}
    assert classify_source(article) == "tier1"


def test_classify_techcrunch_tier1():
    article = {"link": "https://techcrunch.com/post", "source": "TechCrunch", "title": "TC post"}
    assert classify_source(article) == "tier1"


def test_classify_healthcare_it_news_tier2():
    article = {"link": "https://healthcareitnews.com/post", "source": "Healthcare IT News", "title": "HIT article"}
    assert classify_source(article) == "tier2"


def _make_topic(platforms=3, authors=7, has_news=True):
    """Build a topic dict compatible with the new multi-source credibility checker."""
    return {
        "topic_key": "anthropic",
        "velocity_score": 80,
        "metrics": {
            "unique_platforms": platforms,
            "unique_authors": authors,
            "platforms": ["bluesky", "hackernews", "reddit"][:platforms],
            "has_news_coverage": has_news,
            "total_engagement": 5000,
        },
        "is_big_ticket": True,
        "representative_items": [
            {"text": "Anthropic releases new clinical model", "author": "test", "url": "https://example.com/1"},
        ],
    }


def test_decision_auto_publish():
    """2+ platforms + 5+ authors + news = auto_publish."""
    topic = _make_topic(platforms=3, authors=7, has_news=True)

    mock_articles = [
        {"title": "Anthropic healthcare AI", "link": "https://anthropic.com/blog", "source": "Anthropic", "published": ""},
        {"title": "Anthropic news", "link": "https://statnews.com/anthropic", "source": "STAT News", "published": ""},
    ]

    with patch("bulletin.credibility_checker.search_google_news", return_value=mock_articles):
        result = check_credibility(topic)

    assert result["decision"] == "auto_publish"
    assert result["credible_count"] >= 1


def test_decision_flag_for_review():
    """2+ platforms + 3+ authors + no news = flag_for_review."""
    topic = _make_topic(platforms=2, authors=4, has_news=False)

    with patch("bulletin.credibility_checker.search_google_news", return_value=[]):
        result = check_credibility(topic)

    assert result["decision"] == "flag_for_review"


def test_decision_skip_single_platform():
    """1 platform = skip regardless of authors or news."""
    topic = _make_topic(platforms=1, authors=20, has_news=True)

    with patch("bulletin.credibility_checker.search_google_news", return_value=[]):
        result = check_credibility(topic)

    assert result["decision"] == "skip"


def test_decision_skip_single_author():
    """1 author cross-posting = skip."""
    topic = _make_topic(platforms=3, authors=1, has_news=True)

    with patch("bulletin.credibility_checker.search_google_news", return_value=[]):
        result = check_credibility(topic)

    assert result["decision"] == "skip"


def test_decision_queue_for_weekly():
    """2 platforms + 2 authors (below threshold) = queue_for_weekly."""
    topic = _make_topic(platforms=2, authors=2, has_news=False)

    with patch("bulletin.credibility_checker.search_google_news", return_value=[]):
        result = check_credibility(topic)

    assert result["decision"] == "queue_for_weekly"


def test_credibility_result_structure():
    """Verify the result dict has all expected keys."""
    topic = _make_topic(platforms=2, authors=5, has_news=False)

    with patch("bulletin.credibility_checker.search_google_news", return_value=[]):
        result = check_credibility(topic)

    assert "decision" in result
    assert "sources" in result
    assert "primary_source" in result
    assert "credible_count" in result
    assert "reason" in result
    assert "source_platforms" in result
    assert "unique_authors" in result
    assert "news_coverage" in result
    assert result["decision"] in ("auto_publish", "flag_for_review", "skip", "queue_for_weekly")

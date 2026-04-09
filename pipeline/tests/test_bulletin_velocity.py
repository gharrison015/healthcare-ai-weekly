import json
import os
import tempfile
from datetime import datetime, timezone, timedelta

from bulletin.velocity_detector import (
    extract_entities,
    cluster_results,
    compute_velocity,
    detect_spikes,
    is_duplicate,
    bulletins_published_today,
)


def _make_item(title="Test", text=None, author="testuser", engagement_score=1000,
               created_minutes_ago=30, source_platform="bluesky", url=None):
    created = (datetime.now(timezone.utc) - timedelta(minutes=created_minutes_ago)).isoformat()
    return {
        "title": title,
        "text": text or title,
        "timestamp": created,
        "author": author,
        "source_platform": source_platform,
        "engagement_score": engagement_score,
        "url": url or f"https://example.com/{author}/{hash(title) % 10000}",
    }


def test_extract_entities_finds_known_companies():
    entities = extract_entities("Anthropic just released Claude 4 for healthcare")
    assert "anthropic" in entities
    assert "claude" in entities


def test_extract_entities_finds_hashtags():
    entities = extract_entities("Big news for #healthcareAI today")
    assert "healthcareai" in entities


def test_extract_entities_handles_empty():
    entities = extract_entities("")
    assert isinstance(entities, set)


def test_extract_entities_finds_government():
    entities = extract_entities("FDA just cleared a new AI diagnostic tool")
    assert "fda" in entities


def test_extract_entities_finds_consulting_firms():
    entities = extract_entities("Deloitte acquires healthcare AI startup")
    assert "deloitte" in entities


def test_extract_entities_finds_multiple():
    entities = extract_entities("Microsoft and Epic partner on clinical AI")
    assert "microsoft" in entities
    assert "epic" in entities


def test_cluster_results_groups_by_entity():
    items = [
        _make_item(title="Anthropic launches Claude for clinical use", author="a"),
        _make_item(title="Claude is now available in Epic EHR", author="b"),
        _make_item(title="OpenAI partners with Mayo Clinic", author="c"),
        _make_item(title="OpenAI healthcare strategy revealed", author="d"),
    ]
    clusters = cluster_results(items)
    assert len(clusters) >= 1


def test_cluster_results_single_item():
    items = [_make_item(title="Random standalone item about nothing recognizable")]
    clusters = cluster_results(items)
    assert len(clusters) >= 1


def test_cluster_results_empty():
    clusters = cluster_results([])
    assert clusters == {}


def test_compute_velocity_basic():
    items = [
        _make_item(title="Test story", author="user1", engagement_score=10000, created_minutes_ago=60),
        _make_item(title="Test story continues", author="user2", engagement_score=15000, created_minutes_ago=30),
    ]
    metrics = compute_velocity(items)
    assert metrics["total_engagement"] == 25000
    assert metrics["unique_authors"] == 2
    assert metrics["item_count"] == 2
    assert metrics["velocity"] > 0


def test_compute_velocity_handles_single_item():
    items = [_make_item(title="Solo item", engagement_score=50000, created_minutes_ago=10)]
    metrics = compute_velocity(items)
    assert metrics["total_engagement"] == 50000
    assert metrics["velocity"] > 0


def test_compute_velocity_aggregates_engagement():
    items = [
        _make_item(title="A", author="a", engagement_score=5000, created_minutes_ago=60),
        _make_item(title="B", author="b", engagement_score=3000, created_minutes_ago=30),
    ]
    metrics = compute_velocity(items)
    assert metrics["total_engagement"] == 8000


def test_compute_velocity_acceleration():
    items = [
        _make_item(title="Breaking", author="a", engagement_score=20000, created_minutes_ago=10),
        _make_item(title="More", author="b", engagement_score=15000, created_minutes_ago=5),
    ]
    metrics = compute_velocity(items)
    assert "acceleration" in metrics
    assert "is_accelerating" in metrics


def test_compute_velocity_hours_elapsed():
    items = [
        _make_item(title="Old", author="a", engagement_score=5000, created_minutes_ago=120),
        _make_item(title="New", author="b", engagement_score=5000, created_minutes_ago=10),
    ]
    metrics = compute_velocity(items)
    assert metrics["hours_elapsed"] >= 1.5


def test_is_duplicate_catches_recent():
    published = [
        {
            "slug": "anthropic-healthcare",
            "tags": ["anthropic", "healthcare"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "headline": "Anthropic Enters Healthcare",
        }
    ]
    assert is_duplicate("anthropic", published, cooldown_hours=6) is True


def test_is_duplicate_allows_old():
    old_time = (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat()
    published = [
        {
            "slug": "anthropic-healthcare",
            "tags": ["anthropic", "healthcare"],
            "timestamp": old_time,
            "headline": "Anthropic Enters Healthcare",
        }
    ]
    assert is_duplicate("anthropic", published, cooldown_hours=6) is False


def test_is_duplicate_allows_different_topic():
    published = [
        {
            "slug": "openai-fda",
            "tags": ["openai", "fda"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "headline": "OpenAI Gets FDA Nod",
        }
    ]
    assert is_duplicate("anthropic", published, cooldown_hours=6) is False


def test_bulletins_published_today_counts():
    with tempfile.TemporaryDirectory() as tmpdir:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        for i in range(2):
            path = os.path.join(tmpdir, f"{today}-{i:02d}-test.json")
            with open(path, "w") as f:
                json.dump({"slug": f"test-{i}"}, f)
        assert bulletins_published_today(tmpdir) == 2


def test_bulletins_published_today_ignores_old():
    with tempfile.TemporaryDirectory() as tmpdir:
        old_date = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
        path = os.path.join(tmpdir, f"{old_date}-00-old.json")
        with open(path, "w") as f:
            json.dump({"slug": "old"}, f)
        assert bulletins_published_today(tmpdir) == 0


def test_bulletins_published_today_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        assert bulletins_published_today(tmpdir) == 0


def test_detect_spikes_respects_daily_limit():
    """When daily limit is reached, detect_spikes returns empty."""
    with tempfile.TemporaryDirectory() as tmpdir:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        for i in range(3):
            path = os.path.join(tmpdir, f"{today}-{i:02d}-test.json")
            with open(path, "w") as f:
                json.dump({"slug": f"test-{i}"}, f)

        items = [_make_item(title="Big Anthropic news", engagement_score=100000)]
        result = detect_spikes(items, bulletins_dir=tmpdir)
        assert result == []

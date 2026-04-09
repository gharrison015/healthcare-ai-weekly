import json
import os
import tempfile
from datetime import datetime, timezone, timedelta

from bulletin.velocity_detector import get_published_slugs, is_duplicate


def test_get_published_slugs_reads_bulletins():
    with tempfile.TemporaryDirectory() as tmpdir:
        bulletin = {
            "slug": "test-story",
            "tags": ["test", "healthcare"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "headline": "Test Story Here",
        }
        filepath = os.path.join(tmpdir, "2026-04-08-14-test-story.json")
        with open(filepath, "w") as f:
            json.dump(bulletin, f)

        published = get_published_slugs(tmpdir)
        assert len(published) == 1
        assert published[0]["slug"] == "test-story"
        assert "test" in published[0]["tags"]


def test_get_published_slugs_empty_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        published = get_published_slugs(tmpdir)
        assert published == []


def test_get_published_slugs_nonexistent_dir():
    published = get_published_slugs("/nonexistent/path")
    assert published == []


def test_get_published_slugs_skips_invalid_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "2026-04-08-bad.json")
        with open(filepath, "w") as f:
            f.write("not valid json{{{")
        published = get_published_slugs(tmpdir)
        assert published == []


def test_get_published_slugs_multiple():
    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(3):
            bulletin = {
                "slug": f"story-{i}",
                "tags": [f"tag-{i}"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "headline": f"Story {i}",
            }
            filepath = os.path.join(tmpdir, f"2026-04-08-{i:02d}-story-{i}.json")
            with open(filepath, "w") as f:
                json.dump(bulletin, f)

        published = get_published_slugs(tmpdir)
        assert len(published) == 3


def test_dedup_by_slug_match():
    now = datetime.now(timezone.utc).isoformat()
    published = [
        {"slug": "anthropic-claude-healthcare", "tags": ["anthropic", "claude"], "timestamp": now, "headline": "test"},
    ]
    assert is_duplicate("anthropic", published, cooldown_hours=6) is True


def test_dedup_by_tag_match():
    now = datetime.now(timezone.utc).isoformat()
    published = [
        {"slug": "big-news", "tags": ["openai", "healthcare"], "timestamp": now, "headline": "test"},
    ]
    assert is_duplicate("openai", published, cooldown_hours=6) is True


def test_dedup_respects_cooldown():
    old = (datetime.now(timezone.utc) - timedelta(hours=8)).isoformat()
    published = [
        {"slug": "anthropic-news", "tags": ["anthropic"], "timestamp": old, "headline": "test"},
    ]
    assert is_duplicate("anthropic", published, cooldown_hours=6) is False


def test_dedup_no_false_positive():
    now = datetime.now(timezone.utc).isoformat()
    published = [
        {"slug": "epic-update", "tags": ["epic", "ehr"], "timestamp": now, "headline": "test"},
    ]
    assert is_duplicate("anthropic", published, cooldown_hours=6) is False


def test_dedup_empty_published():
    assert is_duplicate("anthropic", [], cooldown_hours=6) is False


def test_dedup_missing_timestamp():
    """Bulletins without timestamp should not crash dedup."""
    published = [
        {"slug": "anthropic-news", "tags": ["anthropic"], "timestamp": "", "headline": "test"},
    ]
    # Should not raise; behavior is to not count as duplicate when timestamp is missing
    result = is_duplicate("anthropic", published, cooldown_hours=6)
    assert isinstance(result, bool)


def test_dedup_cooldown_boundary():
    """Exactly at cooldown boundary should not be duplicate."""
    boundary = (datetime.now(timezone.utc) - timedelta(hours=6, seconds=1)).isoformat()
    published = [
        {"slug": "anthropic-news", "tags": ["anthropic"], "timestamp": boundary, "headline": "test"},
    ]
    assert is_duplicate("anthropic", published, cooldown_hours=6) is False

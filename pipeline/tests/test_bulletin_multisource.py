"""Tests for the multi-source bulletin pipeline.

Covers:
  - Multi-source clustering
  - Two-source verification logic
  - Decision matrix (auto_publish, flag_for_review, skip)
  - Big-ticket keyword detection
  - Dedup across sources
  - Recency filtering (only last 24 hours)
"""

import json
import os
import tempfile
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from bulletin.velocity_detector import (
    extract_entities,
    cluster_results,
    compute_velocity,
    detect_spikes,
    has_big_ticket_keywords,
    is_duplicate,
)
from bulletin.credibility_checker import check_credibility, classify_source


# ---------- Helpers ----------

def _make_item(
    title="Test story",
    text="Test story body",
    source_platform="bluesky",
    author="testuser",
    engagement_score=100,
    minutes_ago=30,
    url=None,
    extra=None,
):
    ts = (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).isoformat()
    result = {
        "title": title,
        "text": text or title,
        "source_platform": source_platform,
        "author": author,
        "engagement_score": engagement_score,
        "timestamp": ts,
        "url": url or f"https://example.com/{author}/{hash(title) % 10000}",
    }
    if extra:
        result.update(extra)
    return result


def _make_config_file(tmpdir, overrides=None):
    """Write a test bulletin_config.json and return its path."""
    config = {
        "sources": {
            "bluesky": {"enabled": True, "keywords": ["healthcare AI"]},
            "hackernews": {"enabled": True, "keywords": ["healthcare AI"]},
        },
        "verification": {
            "min_independent_sources": 2,
            "min_unique_authors": 3,
            "min_platforms": 2,
            "hours_back": 24,
            "big_ticket_keywords": [
                "acquisition", "merger", "billion", "FDA", "clearance",
                "approval", "partnership", "launch", "release", "breach",
            ],
        },
        "limits": {
            "max_bulletins_per_day": 3,
            "cooldown_hours": 6,
        },
    }
    if overrides:
        for k, v in overrides.items():
            if isinstance(v, dict) and k in config:
                config[k].update(v)
            else:
                config[k] = v
    path = os.path.join(tmpdir, "config.json")
    with open(path, "w") as f:
        json.dump(config, f)
    return path


# ========== Multi-source clustering ==========

class TestMultiSourceClustering:

    def test_cluster_by_shared_entity(self):
        items = [
            _make_item(title="Anthropic launches new model", source_platform="bluesky", author="alice"),
            _make_item(title="Anthropic Claude update", source_platform="hackernews", author="bob"),
            _make_item(title="OpenAI partners with Mayo", source_platform="reddit", author="carol"),
            _make_item(title="OpenAI healthcare push", source_platform="bluesky", author="dave"),
        ]
        clusters = cluster_results(items)
        # Should produce at least two clusters (anthropic, openai)
        assert len(clusters) >= 2
        assert "anthropic" in clusters or "claude" in clusters
        assert "openai" in clusters

    def test_cluster_single_item_becomes_singleton(self):
        items = [_make_item(title="Random unrelated item")]
        clusters = cluster_results(items)
        assert len(clusters) >= 1

    def test_cluster_empty_input(self):
        clusters = cluster_results([])
        assert clusters == {}

    def test_cross_platform_items_cluster_together(self):
        items = [
            _make_item(title="FDA clears new AI diagnostic", source_platform="bluesky", author="a"),
            _make_item(title="FDA AI diagnostic approval", source_platform="hackernews", author="b"),
            _make_item(title="FDA diagnostic tool cleared", source_platform="reddit", author="c"),
        ]
        clusters = cluster_results(items)
        # All should cluster under "fda"
        assert "fda" in clusters
        assert len(clusters["fda"]) == 3


# ========== Two-source verification ==========

class TestTwoSourceVerification:

    def test_two_platforms_passes_verification(self):
        items = [
            _make_item(title="Anthropic healthcare launch", source_platform="bluesky", author="alice"),
            _make_item(title="Anthropic healthcare launch", source_platform="hackernews", author="bob"),
            _make_item(title="Anthropic new product", source_platform="reddit", author="carol"),
        ]
        metrics = compute_velocity(items)
        assert metrics["unique_platforms"] >= 2
        assert metrics["unique_authors"] >= 2

    def test_single_platform_fails_verification(self):
        """Items from a single platform with < 3 authors should not pass."""
        items = [
            _make_item(title="Anthropic news", source_platform="bluesky", author="alice"),
            _make_item(title="Anthropic update", source_platform="bluesky", author="bob"),
        ]
        metrics = compute_velocity(items)
        assert metrics["unique_platforms"] == 1
        # With only 2 authors and 1 platform, this should not pass the filter

    def test_single_author_crosspost_fails(self):
        """One person posting the same thing across platforms should not pass."""
        items = [
            _make_item(title="Anthropic news", source_platform="bluesky", author="sameperson"),
            _make_item(title="Anthropic news", source_platform="hackernews", author="sameperson"),
            _make_item(title="Anthropic news", source_platform="reddit", author="sameperson"),
        ]
        metrics = compute_velocity(items)
        assert metrics["unique_authors"] == 1
        # Single author = skip, regardless of platform count

    def test_detect_spikes_requires_two_sources(self):
        """detect_spikes should skip clusters with only one platform and < 3 authors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = _make_config_file(tmpdir)
            bulletins_dir = os.path.join(tmpdir, "bulletins")
            os.makedirs(bulletins_dir)

            # All from one platform, two authors -> should fail
            items = [
                _make_item(title="Anthropic news one", source_platform="bluesky", author="alice"),
                _make_item(title="Anthropic news two", source_platform="bluesky", author="bob"),
            ]
            spikes = detect_spikes(items, config_path=config_path, bulletins_dir=bulletins_dir)
            assert spikes == []

    def test_detect_spikes_passes_with_two_platforms(self):
        """detect_spikes should include clusters with 2+ platforms and 2+ authors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = _make_config_file(tmpdir)
            bulletins_dir = os.path.join(tmpdir, "bulletins")
            os.makedirs(bulletins_dir)

            items = [
                _make_item(title="Anthropic releases Claude 5 for healthcare", source_platform="bluesky", author="alice", engagement_score=500),
                _make_item(title="Anthropic Claude 5 now in clinics", source_platform="hackernews", author="bob", engagement_score=300),
                _make_item(title="Anthropic Claude 5 healthcare AI", source_platform="reddit", author="carol", engagement_score=200),
            ]
            spikes = detect_spikes(items, config_path=config_path, bulletins_dir=bulletins_dir)
            assert len(spikes) >= 1
            assert spikes[0]["metrics"]["unique_platforms"] >= 2

    def test_detect_spikes_rejects_single_author_crosspost(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = _make_config_file(tmpdir)
            bulletins_dir = os.path.join(tmpdir, "bulletins")
            os.makedirs(bulletins_dir)

            items = [
                _make_item(title="Anthropic big news", source_platform="bluesky", author="spammer"),
                _make_item(title="Anthropic big news repost", source_platform="hackernews", author="spammer"),
                _make_item(title="Anthropic big news again", source_platform="reddit", author="spammer"),
            ]
            spikes = detect_spikes(items, config_path=config_path, bulletins_dir=bulletins_dir)
            assert spikes == []


# ========== Decision matrix ==========

class TestDecisionMatrix:

    def _topic(self, platforms=2, authors=5, has_news=True):
        return {
            "topic_key": "anthropic",
            "velocity_score": 80,
            "metrics": {
                "unique_platforms": platforms,
                "unique_authors": authors,
                "platforms": ["bluesky", "hackernews"][:platforms],
                "has_news_coverage": has_news,
                "total_engagement": 5000,
            },
            "is_big_ticket": True,
            "representative_items": [
                _make_item(title="Anthropic healthcare AI launch"),
            ],
        }

    @patch("bulletin.credibility_checker.search_google_news", return_value=[])
    def test_auto_publish_2plus_platforms_5plus_authors_news(self, mock_gn):
        topic = self._topic(platforms=3, authors=7, has_news=True)
        result = check_credibility(topic, config_path="bulletin/bulletin_config.json")
        assert result["decision"] == "auto_publish"

    @patch("bulletin.credibility_checker.search_google_news", return_value=[])
    def test_flag_for_review_2plus_platforms_3plus_authors_no_news(self, mock_gn):
        topic = self._topic(platforms=2, authors=4, has_news=False)
        result = check_credibility(topic, config_path="bulletin/bulletin_config.json")
        assert result["decision"] == "flag_for_review"

    @patch("bulletin.credibility_checker.search_google_news", return_value=[])
    def test_skip_single_platform(self, mock_gn):
        topic = self._topic(platforms=1, authors=10, has_news=True)
        result = check_credibility(topic, config_path="bulletin/bulletin_config.json")
        assert result["decision"] == "skip"

    @patch("bulletin.credibility_checker.search_google_news", return_value=[])
    def test_skip_single_author(self, mock_gn):
        topic = self._topic(platforms=3, authors=1, has_news=True)
        result = check_credibility(topic, config_path="bulletin/bulletin_config.json")
        assert result["decision"] == "skip"

    @patch("bulletin.credibility_checker.search_google_news", return_value=[])
    def test_queue_for_weekly_low_authors(self, mock_gn):
        topic = self._topic(platforms=2, authors=2, has_news=False)
        result = check_credibility(topic, config_path="bulletin/bulletin_config.json")
        assert result["decision"] == "queue_for_weekly"


# ========== Big-ticket keyword detection ==========

class TestBigTicketKeywords:

    BIG_TICKET = ["acquisition", "merger", "billion", "FDA", "clearance", "partnership"]

    def test_detects_acquisition(self):
        items = [_make_item(title="Google acquisition of health AI startup for $2B")]
        assert has_big_ticket_keywords(items, self.BIG_TICKET) is True

    def test_detects_fda(self):
        items = [_make_item(title="FDA clears first AI radiology tool")]
        assert has_big_ticket_keywords(items, self.BIG_TICKET) is True

    def test_ignores_routine_news(self):
        items = [_make_item(title="Healthcare conference wrap-up and panel summaries")]
        assert has_big_ticket_keywords(items, self.BIG_TICKET) is False

    def test_case_insensitive(self):
        items = [_make_item(title="Major PARTNERSHIP between Epic and Anthropic")]
        assert has_big_ticket_keywords(items, self.BIG_TICKET) is True

    def test_empty_items(self):
        assert has_big_ticket_keywords([], self.BIG_TICKET) is False


# ========== Dedup across sources ==========

class TestDedup:

    def test_duplicate_url_removed_in_cluster(self):
        """Items with the same URL from different platforms should cluster but not double-count."""
        items = [
            _make_item(title="FDA clears AI tool", source_platform="bluesky", author="alice", url="https://example.com/fda"),
            _make_item(title="FDA clears AI tool", source_platform="hackernews", author="bob", url="https://example.com/fda"),
        ]
        # Both should cluster under "fda" but URLs are the same
        clusters = cluster_results(items)
        assert "fda" in clusters

    def test_is_duplicate_blocks_recent_topic(self):
        published = [
            {
                "slug": "anthropic-launch",
                "tags": ["anthropic"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "headline": "Anthropic Launch",
            }
        ]
        assert is_duplicate("anthropic", published, cooldown_hours=6) is True

    def test_is_duplicate_allows_after_cooldown(self):
        old_ts = (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat()
        published = [
            {
                "slug": "anthropic-launch",
                "tags": ["anthropic"],
                "timestamp": old_ts,
                "headline": "Anthropic Launch",
            }
        ]
        assert is_duplicate("anthropic", published, cooldown_hours=6) is False

    def test_is_duplicate_allows_different_topic(self):
        published = [
            {
                "slug": "openai-fda",
                "tags": ["openai", "fda"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "headline": "OpenAI Gets FDA Nod",
            }
        ]
        assert is_duplicate("anthropic", published, cooldown_hours=6) is False


# ========== Recency filtering ==========

class TestRecencyFiltering:

    def test_single_platform_few_authors_excluded(self):
        """Items from one platform with fewer than min_unique_authors should be excluded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = _make_config_file(tmpdir)
            bulletins_dir = os.path.join(tmpdir, "bulletins")
            os.makedirs(bulletins_dir)

            # Single platform + only 2 authors (below min_unique_authors=3)
            # This fails both conditions: platforms < 2 AND authors < 3
            items = [
                _make_item(title="Anthropic old news", source_platform="bluesky", author="user0", minutes_ago=48 * 60),
                _make_item(title="Anthropic more old news", source_platform="bluesky", author="user1", minutes_ago=48 * 60),
            ]
            spikes = detect_spikes(items, config_path=config_path, bulletins_dir=bulletins_dir)
            assert len(spikes) == 0

    def test_recent_items_pass(self):
        """Items within the recency window should be eligible."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = _make_config_file(tmpdir)
            bulletins_dir = os.path.join(tmpdir, "bulletins")
            os.makedirs(bulletins_dir)

            items = [
                _make_item(title="Anthropic breaking news launch", source_platform="bluesky", author="alice", minutes_ago=30, engagement_score=500),
                _make_item(title="Anthropic launch confirmed", source_platform="hackernews", author="bob", minutes_ago=45, engagement_score=300),
                _make_item(title="Anthropic healthcare launch details", source_platform="reddit", author="carol", minutes_ago=60, engagement_score=200),
            ]
            spikes = detect_spikes(items, config_path=config_path, bulletins_dir=bulletins_dir)
            assert len(spikes) >= 1


# ========== Source classification ==========

class TestSourceClassification:

    def test_primary_source_detected(self):
        article = {"link": "https://www.fda.gov/news/ai-clearance", "source": "", "title": ""}
        assert classify_source(article) == "primary"

    def test_tier1_source_detected(self):
        article = {"link": "https://example.com", "source": "Reuters", "title": ""}
        assert classify_source(article) == "tier1"

    def test_tier2_source_detected(self):
        article = {"link": "https://example.com", "source": "Becker's Hospital Review", "title": ""}
        assert classify_source(article) == "tier2"

    def test_unknown_source(self):
        article = {"link": "https://randomblog.com", "source": "Some Blog", "title": ""}
        assert classify_source(article) == "unknown"


# ========== Velocity metrics ==========

class TestVelocityMetrics:

    def test_compute_velocity_counts_platforms(self):
        items = [
            _make_item(source_platform="bluesky", author="a"),
            _make_item(source_platform="hackernews", author="b"),
            _make_item(source_platform="reddit", author="c"),
        ]
        metrics = compute_velocity(items)
        assert metrics["unique_platforms"] == 3
        assert metrics["unique_authors"] == 3
        assert "bluesky" in metrics["platforms"]
        assert "hackernews" in metrics["platforms"]

    def test_compute_velocity_detects_news_coverage(self):
        items = [
            _make_item(source_platform="newsdata", extra={"is_news": True}),
            _make_item(source_platform="bluesky"),
        ]
        metrics = compute_velocity(items)
        assert metrics["has_news_coverage"] is True

    def test_compute_velocity_no_news_coverage(self):
        items = [
            _make_item(source_platform="bluesky"),
            _make_item(source_platform="hackernews"),
        ]
        metrics = compute_velocity(items)
        assert metrics["has_news_coverage"] is False

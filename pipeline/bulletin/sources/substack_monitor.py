"""Substack RSS monitor. Free, no auth, no rate limits.

Monitors healthcare AI thought leader newsletters via their public RSS feeds.
Every Substack has a feed at [name].substack.com/feed.
"""

import logging
from datetime import datetime, timezone, timedelta

import feedparser

from bulletin.sources.base import BaseMonitor

logger = logging.getLogger(__name__)

# Healthcare AI Substacks to monitor
DEFAULT_FEEDS = [
    {"name": "Ground Truths (Eric Topol)", "url": "https://erictopol.substack.com/feed"},
    {"name": "The Batch (Andrew Ng)", "url": "https://www.deeplearning.ai/the-batch/feed"},
    {"name": "Import AI", "url": "https://importai.substack.com/feed"},
    {"name": "AI Tidbits", "url": "https://aitidbits.substack.com/feed"},
    {"name": "Gradient Flow", "url": "https://gradientflow.substack.com/feed"},
    {"name": "The Algorithmic Bridge", "url": "https://thealgorithmicbridge.substack.com/feed"},
    {"name": "Healthcare Strategy", "url": "https://healthcarestrategy.substack.com/feed"},
    {"name": "Elad Gil", "url": "https://blog.eladgil.com/feed"},
    {"name": "One Useful Thing (Ethan Mollick)", "url": "https://www.oneusefulthing.org/feed"},
]


class SubstackMonitor(BaseMonitor):
    source_platform = "substack"

    def __init__(self, feeds=None):
        self.feeds = feeds or DEFAULT_FEEDS

    def search(self, keywords: list[str], hours_back: int = 24) -> list[dict]:
        results = []

        for feed_info in self.feeds:
            feed_name = feed_info["name"]
            feed_url = feed_info["url"]

            try:
                parsed = feedparser.parse(feed_url)
            except Exception as e:
                logger.warning("Substack feed '%s' failed: %s", feed_name, e)
                continue

            for entry in parsed.entries[:10]:
                # Check recency
                published = entry.get("published", "")
                updated = entry.get("updated", published)
                timestamp = updated or published

                if timestamp and not self._is_recent_rss(timestamp, hours_back):
                    continue

                title = entry.get("title", "")
                link = entry.get("link", "")
                summary = entry.get("summary", "")
                content = entry.get("content", [{}])
                full_text = content[0].get("value", summary) if content else summary

                # Check if any keyword matches in title or content
                text_lower = (title + " " + full_text).lower()
                if not any(kw.lower() in text_lower for kw in keywords):
                    continue

                author = entry.get("author", feed_name)

                results.append(self._make_result(
                    title=title,
                    url=link,
                    author=author,
                    timestamp=self._parse_rss_date(timestamp),
                    engagement_score=0,
                    text=full_text[:2000],
                    extra={
                        "feed_name": feed_name,
                        "is_newsletter": True,
                    },
                ))

        # Deduplicate by URL
        seen = set()
        deduped = []
        for r in results:
            if r["url"] not in seen:
                seen.add(r["url"])
                deduped.append(r)

        logger.info("Substack: found %d results from %d feeds", len(deduped), len(self.feeds))
        return deduped

    def _is_recent_rss(self, date_str: str, hours_back: int) -> bool:
        """Check if an RSS date string is within the recency window."""
        import email.utils
        try:
            parsed = email.utils.parsedate_to_datetime(date_str)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)
            return parsed >= cutoff
        except (ValueError, TypeError):
            # If we can't parse the date, try the base class method
            return self.is_recent(date_str, hours_back)

    def _parse_rss_date(self, date_str: str) -> str:
        """Convert RSS date to ISO format string."""
        import email.utils
        try:
            parsed = email.utils.parsedate_to_datetime(date_str)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.isoformat()
        except (ValueError, TypeError):
            return date_str

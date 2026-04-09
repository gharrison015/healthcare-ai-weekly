"""Base monitor interface for all source monitors."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from typing import Optional


class BaseMonitor(ABC):
    """Abstract base class that all source monitors must implement."""

    source_platform: str = "unknown"

    @abstractmethod
    def search(self, keywords: list[str], hours_back: int = 24) -> list[dict]:
        """Search this source for recent mentions of the given keywords.

        Args:
            keywords: list of search terms
            hours_back: only return results from the last N hours

        Returns:
            List of dicts, each with at minimum:
                - title: str (headline or first line of post)
                - url: str (link to original)
                - source_platform: str (e.g. 'x', 'bluesky', 'reddit')
                - author: str (username or outlet name)
                - timestamp: str (ISO 8601)
                - engagement_score: int (likes + shares + comments, normalized)
                - text: str (full text of the post/article)
        """
        raise NotImplementedError

    def is_recent(self, timestamp_str: str, hours_back: int = 24) -> bool:
        """Check if a timestamp string is within the recency window."""
        try:
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        except (ValueError, AttributeError):
            return False
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        return dt >= cutoff

    def _make_result(
        self,
        title: str,
        url: str,
        author: str,
        timestamp: str,
        engagement_score: int,
        text: str,
        extra: Optional[dict] = None,
    ) -> dict:
        """Build a standardized result dict."""
        result = {
            "title": title,
            "url": url,
            "source_platform": self.source_platform,
            "author": author,
            "timestamp": timestamp,
            "engagement_score": engagement_score,
            "text": text,
        }
        if extra:
            result.update(extra)
        return result

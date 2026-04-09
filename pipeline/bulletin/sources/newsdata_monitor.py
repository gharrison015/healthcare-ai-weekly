"""Newsdata.io monitor using the free API tier (200 credits/day).

Requires NEWSDATA_API_KEY in the environment.
Gracefully skips if the key is missing.
"""

import logging
import os
from datetime import datetime, timezone, timedelta

import requests

from bulletin.sources.base import BaseMonitor

logger = logging.getLogger(__name__)

API_URL = "https://newsdata.io/api/1/latest"


class NewsdataMonitor(BaseMonitor):
    source_platform = "newsdata"

    def __init__(self):
        self.api_key = os.getenv("NEWSDATA_API_KEY", "")

    def _has_credentials(self) -> bool:
        return bool(self.api_key and "PASTE" not in self.api_key)

    def search(self, keywords: list[str], hours_back: int = 24) -> list[dict]:
        if not self._has_credentials():
            logger.warning(
                "Newsdata monitor skipped: NEWSDATA_API_KEY not configured. "
                "Get a free key at https://newsdata.io and add to pipeline/.env"
            )
            return []

        results = []

        for keyword in keywords:
            try:
                resp = requests.get(
                    API_URL,
                    params={
                        "apikey": self.api_key,
                        "q": keyword,
                        "language": "en",
                        "category": "health,technology",
                        "size": 25,
                    },
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.warning("Newsdata search failed for '%s': %s", keyword, e)
                continue

            for article in data.get("results", []):
                pubdate = article.get("pubDate", "")
                if pubdate and not self.is_recent(pubdate, hours_back):
                    continue

                title = article.get("title", "")
                link = article.get("link", "")
                source_name = article.get("source_name", "unknown")
                description = article.get("description", "") or ""
                content = article.get("content", "") or description

                results.append(self._make_result(
                    title=title,
                    url=link,
                    author=source_name,
                    timestamp=pubdate,
                    engagement_score=0,  # News articles don't have engagement metrics
                    text=content[:2000],
                    extra={
                        "source_name": source_name,
                        "category": article.get("category", []),
                        "is_news": True,
                    },
                ))

        # Deduplicate by URL
        seen = set()
        deduped = []
        for r in results:
            if r["url"] not in seen:
                seen.add(r["url"])
                deduped.append(r)

        logger.info("Newsdata: found %d results for %d keywords", len(deduped), len(keywords))
        return deduped

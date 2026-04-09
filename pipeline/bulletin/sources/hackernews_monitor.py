"""Hacker News monitor using the free Algolia HN Search API. No auth required."""

import logging
from datetime import datetime, timezone, timedelta

import requests

from bulletin.sources.base import BaseMonitor

logger = logging.getLogger(__name__)

SEARCH_URL = "https://hn.algolia.com/api/v1/search"


class HackerNewsMonitor(BaseMonitor):
    source_platform = "hackernews"

    def search(self, keywords: list[str], hours_back: int = 24) -> list[dict]:
        results = []
        cutoff_ts = int((datetime.now(timezone.utc) - timedelta(hours=hours_back)).timestamp())

        for keyword in keywords:
            try:
                resp = requests.get(
                    SEARCH_URL,
                    params={
                        "query": keyword,
                        "tags": "story",
                        "numericFilters": f"created_at_i>{cutoff_ts}",
                        "hitsPerPage": 50,
                    },
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.warning("HN search failed for '%s': %s", keyword, e)
                continue

            for hit in data.get("hits", []):
                created_at_i = hit.get("created_at_i", 0)
                created_at = datetime.fromtimestamp(created_at_i, tz=timezone.utc).isoformat()

                title = hit.get("title", "")
                url = hit.get("url", "")
                story_url = f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
                author = hit.get("author", "unknown")
                points = hit.get("points", 0) or 0
                num_comments = hit.get("num_comments", 0) or 0

                results.append(self._make_result(
                    title=title,
                    url=url or story_url,
                    author=author,
                    timestamp=created_at,
                    engagement_score=points + num_comments,
                    text=title,  # HN stories are title-only
                    extra={
                        "points": points,
                        "num_comments": num_comments,
                        "hn_url": story_url,
                    },
                ))

        # Deduplicate by URL
        seen = set()
        deduped = []
        for r in results:
            if r["url"] not in seen:
                seen.add(r["url"])
                deduped.append(r)

        logger.info("HackerNews: found %d results for %d keywords", len(deduped), len(keywords))
        return deduped

"""Bluesky monitor using the AT Protocol API. Falls back gracefully if search is unavailable."""

import logging
from datetime import datetime, timezone, timedelta

import requests

from bulletin.sources.base import BaseMonitor

logger = logging.getLogger(__name__)

SEARCH_URL = "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"


class BlueskyMonitor(BaseMonitor):
    source_platform = "bluesky"

    def search(self, keywords: list[str], hours_back: int = 24) -> list[dict]:
        results = []
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)

        for keyword in keywords:
            try:
                resp = requests.get(
                    SEARCH_URL,
                    params={"q": keyword, "limit": 50, "sort": "latest"},
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.warning("Bluesky search failed for '%s': %s", keyword, e)
                continue

            for post in data.get("posts", []):
                record = post.get("record", {})
                created_at = record.get("createdAt", "")
                if not self.is_recent(created_at, hours_back):
                    continue

                author_obj = post.get("author", {})
                handle = author_obj.get("handle", "unknown")
                text = record.get("text", "")
                uri = post.get("uri", "")

                # Build a web URL from the AT URI
                # at://did:plc:xxx/app.bsky.feed.post/yyy -> https://bsky.app/profile/handle/post/yyy
                rkey = uri.split("/")[-1] if "/" in uri else ""
                web_url = f"https://bsky.app/profile/{handle}/post/{rkey}" if rkey else uri

                like_count = post.get("likeCount", 0)
                repost_count = post.get("repostCount", 0)
                reply_count = post.get("replyCount", 0)
                engagement = like_count + repost_count + reply_count

                results.append(self._make_result(
                    title=text[:120],
                    url=web_url,
                    author=handle,
                    timestamp=created_at,
                    engagement_score=engagement,
                    text=text,
                    extra={
                        "likes": like_count,
                        "reposts": repost_count,
                        "replies": reply_count,
                    },
                ))

        # Deduplicate by URL
        seen = set()
        deduped = []
        for r in results:
            if r["url"] not in seen:
                seen.add(r["url"])
                deduped.append(r)

        logger.info("Bluesky: found %d results for %d keywords", len(deduped), len(keywords))
        return deduped

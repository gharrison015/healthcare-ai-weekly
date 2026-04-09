"""X/Twitter monitor using twscrape (free, credential-based scraping).

Requires X_USERNAME and X_PASSWORD in the environment.
Gracefully skips if credentials are missing.
"""

import logging
import os
from datetime import datetime, timezone, timedelta

from bulletin.sources.base import BaseMonitor

logger = logging.getLogger(__name__)


class XScraper(BaseMonitor):
    source_platform = "x"

    def __init__(self):
        self.username = os.getenv("X_USERNAME", "")
        self.password = os.getenv("X_PASSWORD", "")
        self._pool = None

    def _has_credentials(self) -> bool:
        return bool(
            self.username
            and self.password
            and "PASTE" not in self.username
            and "PASTE" not in self.password
        )

    async def _get_pool(self):
        """Lazy-init the twscrape account pool."""
        if self._pool is not None:
            return self._pool

        try:
            from twscrape import AccountsPool, API
        except ImportError:
            logger.warning("twscrape not installed. Run: pip install twscrape")
            return None

        pool = AccountsPool()
        await pool.add_account(self.username, self.password, "", "")
        await pool.login_all()
        self._pool = API(pool)
        return self._pool

    def search(self, keywords: list[str], hours_back: int = 24) -> list[dict]:
        """Search X for recent tweets matching keywords.

        This uses twscrape which requires valid X credentials.
        Returns empty list if credentials are missing or twscrape is not installed.
        """
        if not self._has_credentials():
            logger.warning(
                "X scraper skipped: X_USERNAME/X_PASSWORD not configured. "
                "Set them in pipeline/.env to enable X monitoring."
            )
            return []

        try:
            import asyncio
            return asyncio.run(self._async_search(keywords, hours_back))
        except Exception as e:
            logger.warning("X scraper failed: %s", e)
            return []

    async def _async_search(self, keywords: list[str], hours_back: int = 24) -> list[dict]:
        api = await self._get_pool()
        if api is None:
            return []

        results = []
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)

        for keyword in keywords:
            try:
                async for tweet in api.search(keyword, limit=50):
                    created_at = tweet.date
                    if created_at and created_at < cutoff:
                        continue

                    ts = created_at.isoformat() if created_at else ""
                    engagement = (
                        (tweet.likeCount or 0)
                        + (tweet.retweetCount or 0)
                        + (tweet.quoteCount or 0)
                        + (tweet.replyCount or 0)
                    )

                    url = f"https://x.com/{tweet.user.username}/status/{tweet.id}"
                    results.append(self._make_result(
                        title=tweet.rawContent[:120] if tweet.rawContent else "",
                        url=url,
                        author=tweet.user.username if tweet.user else "unknown",
                        timestamp=ts,
                        engagement_score=engagement,
                        text=tweet.rawContent or "",
                        extra={
                            "likes": tweet.likeCount or 0,
                            "retweets": tweet.retweetCount or 0,
                            "quotes": tweet.quoteCount or 0,
                            "replies": tweet.replyCount or 0,
                            "impressions": tweet.viewCount or 0,
                        },
                    ))
            except Exception as e:
                logger.warning("X search failed for '%s': %s", keyword, e)

        # Deduplicate
        seen = set()
        deduped = []
        for r in results:
            if r["url"] not in seen:
                seen.add(r["url"])
                deduped.append(r)

        logger.info("X scraper: found %d results for %d keywords", len(deduped), len(keywords))
        return deduped

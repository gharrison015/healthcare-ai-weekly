"""Reddit monitor using the Reddit JSON API (no PRAW dependency needed).

Requires REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET for higher rate limits,
but falls back to unauthenticated JSON endpoints if missing.
"""

import logging
import os
from datetime import datetime, timezone, timedelta

import requests

from bulletin.sources.base import BaseMonitor

logger = logging.getLogger(__name__)

OAUTH_URL = "https://oauth.reddit.com"
PUBLIC_URL = "https://www.reddit.com"
TOKEN_URL = "https://www.reddit.com/api/v1/access_token"

DEFAULT_SUBREDDITS = ["MachineLearning", "healthcare", "artificial", "HealthIT"]


class RedditMonitor(BaseMonitor):
    source_platform = "reddit"

    def __init__(self):
        self.client_id = os.getenv("REDDIT_CLIENT_ID", "")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
        self._token = None
        self._session = requests.Session()
        self._session.headers["User-Agent"] = "HealthcareAIWeekly/1.0"

    def _has_credentials(self) -> bool:
        return bool(
            self.client_id
            and self.client_secret
            and "PASTE" not in self.client_id
            and "PASTE" not in self.client_secret
        )

    def _get_token(self) -> str | None:
        if self._token:
            return self._token
        if not self._has_credentials():
            return None
        try:
            resp = self._session.post(
                TOKEN_URL,
                auth=(self.client_id, self.client_secret),
                data={"grant_type": "client_credentials"},
                timeout=10,
            )
            resp.raise_for_status()
            self._token = resp.json().get("access_token")
            return self._token
        except Exception as e:
            logger.warning("Reddit OAuth failed: %s", e)
            return None

    def search(self, keywords: list[str], hours_back: int = 24,
               subreddits: list[str] | None = None) -> list[dict]:
        subs = subreddits or DEFAULT_SUBREDDITS
        results = []
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)

        token = self._get_token()

        for sub in subs:
            for keyword in keywords:
                try:
                    posts = self._search_subreddit(sub, keyword, token)
                except Exception as e:
                    logger.warning("Reddit search failed for r/%s '%s': %s", sub, keyword, e)
                    continue

                for post in posts:
                    created_utc = post.get("created_utc", 0)
                    created_at = datetime.fromtimestamp(created_utc, tz=timezone.utc)
                    if created_at < cutoff:
                        continue

                    title = post.get("title", "")
                    selftext = post.get("selftext", "") or ""
                    permalink = post.get("permalink", "")
                    url = f"https://www.reddit.com{permalink}" if permalink else ""
                    author = post.get("author", "unknown")
                    score = post.get("score", 0) or 0
                    num_comments = post.get("num_comments", 0) or 0

                    results.append(self._make_result(
                        title=title,
                        url=url,
                        author=f"u/{author}",
                        timestamp=created_at.isoformat(),
                        engagement_score=score + num_comments,
                        text=f"{title}\n\n{selftext[:1500]}".strip(),
                        extra={
                            "subreddit": post.get("subreddit", sub),
                            "score": score,
                            "num_comments": num_comments,
                            "external_url": post.get("url", ""),
                        },
                    ))

        # Deduplicate by URL
        seen = set()
        deduped = []
        for r in results:
            if r["url"] not in seen:
                seen.add(r["url"])
                deduped.append(r)

        logger.info("Reddit: found %d results for %d subreddits", len(deduped), len(subs))
        return deduped

    def _search_subreddit(self, subreddit: str, query: str, token: str | None) -> list[dict]:
        """Search a subreddit, using OAuth if available, otherwise public JSON."""
        if token:
            headers = {"Authorization": f"Bearer {token}"}
            url = f"{OAUTH_URL}/r/{subreddit}/search.json"
        else:
            headers = {}
            url = f"{PUBLIC_URL}/r/{subreddit}/search.json"

        resp = self._session.get(
            url,
            headers=headers,
            params={
                "q": query,
                "sort": "new",
                "t": "day",
                "limit": 25,
                "restrict_sr": "on",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        children = data.get("data", {}).get("children", [])
        return [child.get("data", {}) for child in children]

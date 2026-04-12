import feedparser
import json
import re
import uuid
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from time import mktime
from urllib.parse import quote

def resolve_google_news_url(url, timeout=3):
    """Resolve a Google News redirect URL to the actual article URL.

    Google News RSS feeds return redirect URLs (news.google.com/rss/articles/...)
    that need to be followed to get the real article URL.

    Returns the resolved URL, or the original URL if resolution fails.
    """
    if "news.google.com" not in url:
        return url
    try:
        response = requests.head(url, allow_redirects=True, timeout=timeout)
        resolved = response.url
        if "news.google.com" not in resolved:
            return resolved
        response = requests.get(url, allow_redirects=True, timeout=timeout, stream=True)
        resolved = response.url
        response.close()
        if "news.google.com" not in resolved:
            return resolved
        return url
    except Exception:
        return url


def build_google_news_url(query):
    encoded = quote(query)
    return f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"

def strip_html(text):
    return re.sub(r'<[^>]+>', '', text).strip()

def parse_feed_entry(entry, source, keywords, max_age_days=7):
    title = strip_html(entry.title) if hasattr(entry, "title") else ""
    raw_link = entry.link if hasattr(entry, "link") else ""
    link = resolve_google_news_url(raw_link)
    summary = strip_html(entry.get("summary", "")) if hasattr(entry, "get") else ""

    published_parsed = getattr(entry, "published_parsed", None)
    if published_parsed:
        published_dt = datetime.fromtimestamp(mktime(published_parsed))
        if datetime.now() - published_dt > timedelta(days=max_age_days):
            return None
        published_date = published_dt.strftime("%Y-%m-%d")
    else:
        published_date = datetime.now().strftime("%Y-%m-%d")

    text = f"{title} {summary}".lower()
    matched = [kw for kw in keywords if re.search(r'\b' + re.escape(kw.lower()) + r'\b', text)]
    if not matched:
        return None

    return {
        "id": str(uuid.uuid4()),
        "title": title,
        "source": source["name"],
        "source_tier": source["tier"],
        "url": link,
        "published_date": published_date,
        "summary": summary[:500],
        "category": source["category"],
        "keywords_matched": matched,
    }

def _fetch_feed(source, keywords, max_age_days):
    """Fetch and parse a single RSS feed. Thread-safe."""
    results = []
    try:
        feed = feedparser.parse(source["url"])
        for entry in feed.entries:
            article = parse_feed_entry(entry, source, keywords, max_age_days)
            if article:
                results.append(article)
    except Exception as e:
        print(f"Warning: Failed to parse {source['name']}: {e}")
    return results


def collect_rss(sources_path, max_age_days=7):
    with open(sources_path) as f:
        config = json.load(f)

    articles = []
    seen_urls = set()

    # Build the full list of feeds to fetch (RSS + Google News queries)
    feeds = list(config["feeds"])
    for query in config.get("google_news_queries", []):
        feeds.append({
            "name": "Google News",
            "tier": "catch_all",
            "category": "core",
            "url": build_google_news_url(query),
        })

    with ThreadPoolExecutor(max_workers=min(10, len(feeds))) as pool:
        futures = {
            pool.submit(_fetch_feed, source, config["keywords"], max_age_days): source
            for source in feeds
        }
        for future in as_completed(futures):
            for article in future.result():
                if article["url"] not in seen_urls:
                    seen_urls.add(article["url"])
                    articles.append(article)

    return articles

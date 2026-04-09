"""
Multi-source credibility checker with two-source verification.

Decision matrix:
  - 2+ platforms + 5+ authors + news coverage -> AUTO-PUBLISH
  - 2+ platforms + 3+ authors + no news yet  -> FLAG FOR REVIEW
  - 1 platform only                          -> SKIP
  - Single author across platforms            -> SKIP
"""

import json
import re
import feedparser
from urllib.parse import quote
from datetime import datetime, timezone


def load_config(config_path="bulletin/bulletin_config.json"):
    with open(config_path) as f:
        return json.load(f)


def search_google_news(query, max_results=10):
    """Search Google News RSS for articles matching a query."""
    encoded = quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"
    try:
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries[:max_results]:
            source = ""
            if hasattr(entry, "source") and hasattr(entry.source, "title"):
                source = entry.source.title
            articles.append({
                "title": entry.title if hasattr(entry, "title") else "",
                "link": entry.link if hasattr(entry, "link") else "",
                "source": source,
                "published": entry.get("published", ""),
            })
        return articles
    except Exception as e:
        print(f"Warning: Google News search failed for '{query}': {e}")
        return []


def classify_source(article):
    """Classify a news article source by credibility tier."""
    primary_domains = [
        "anthropic.com", "openai.com", "google.com", "microsoft.com",
        "epic.com", "fda.gov", "hhs.gov", "cms.gov", "nih.gov",
        "sec.gov", "whitehouse.gov",
    ]
    tier1_sources = [
        "reuters", "associated press", "ap news", "wall street journal", "wsj",
        "new york times", "nytimes", "washington post", "bloomberg",
        "stat news", "stat", "fierce healthcare", "fiercehealthcare",
        "modern healthcare", "health affairs", "nature", "nejm", "jama",
        "the lancet", "bmj", "science", "techcrunch", "the verge",
        "wired", "ars technica", "cnbc", "bbc",
    ]
    tier2_sources = [
        "becker", "healthcare it news", "healthcareitnews", "mobihealthnews",
        "health it analytics", "medcity news", "medscape", "endpoints news",
        "healthcare dive", "axios",
    ]

    link = article.get("link", "").lower()
    source = article.get("source", "").lower()
    title = article.get("title", "").lower()

    for domain in primary_domains:
        if domain in link:
            return "primary"
    for s in tier1_sources:
        if s in source or s in title:
            return "tier1"
    for s in tier2_sources:
        if s in source or s in title:
            return "tier2"
    return "unknown"


def check_credibility(topic, config_path="bulletin/bulletin_config.json"):
    """Run credibility checks on a multi-source topic spike.

    Implements the two-source verification decision matrix:
      - 2+ platforms + 5+ authors + news coverage -> AUTO-PUBLISH
      - 2+ platforms + 3+ authors + no news yet  -> FLAG FOR REVIEW
      - 1 platform only                          -> SKIP
      - Single author across platforms            -> SKIP

    Args:
        topic: dict from velocity_detector with topic_key, metrics,
               representative_items, is_big_ticket
        config_path: path to bulletin_config.json

    Returns a dict with decision, sources, reason, and diversity metrics.
    """
    config = load_config(config_path)
    verification = config.get("verification", {})
    min_platforms = verification.get("min_platforms", 2)
    min_authors = verification.get("min_unique_authors", 3)

    topic_key = topic.get("topic_key", "")
    metrics = topic.get("metrics", {})
    unique_platforms = metrics.get("unique_platforms", 0)
    unique_authors = metrics.get("unique_authors", 0)
    has_news_in_cluster = metrics.get("has_news_coverage", False)

    # --- Additional Google News search for external confirmation ---
    search_terms = [topic_key]
    rep_items = topic.get("representative_items", [])
    if rep_items:
        top_text = rep_items[0].get("text", "")
        clean_text = re.sub(r"https?://\S+", "", top_text)
        clean_text = re.sub(r"@\w+", "", clean_text).strip()
        if clean_text and len(clean_text) > 10:
            search_terms.append(clean_text[:80])

    all_articles = []
    for term in search_terms:
        articles = search_google_news(f"{term} healthcare AI")
        all_articles.extend(articles)

    # Deduplicate
    seen_links = set()
    unique_articles = []
    for article in all_articles:
        if article["link"] not in seen_links:
            seen_links.add(article["link"])
            article["tier"] = classify_source(article)
            unique_articles.append(article)

    primary_sources = [a for a in unique_articles if a["tier"] == "primary"]
    tier1_sources = [a for a in unique_articles if a["tier"] == "tier1"]
    tier2_sources = [a for a in unique_articles if a["tier"] == "tier2"]
    credible_count = len(primary_sources) + len(tier1_sources)

    # Best source for the bulletin
    best_source = None
    if primary_sources:
        best_source = primary_sources[0]
    elif tier1_sources:
        best_source = tier1_sources[0]
    elif tier2_sources:
        best_source = tier2_sources[0]

    # Combined news coverage check
    has_news = has_news_in_cluster or credible_count > 0 or len(tier2_sources) > 0

    # --- Decision matrix ---

    # SKIP: single platform
    if unique_platforms < min_platforms:
        decision = "skip"
        reason = (
            f"Single platform ({metrics.get('platforms', ['?'])}). "
            f"Two-source verification requires {min_platforms}+ platforms."
        )
    # SKIP: single author cross-posting
    elif unique_authors <= 1:
        decision = "skip"
        reason = "Single author cross-posting across platforms. Not independent verification."
    # AUTO-PUBLISH: 2+ platforms, 5+ authors, news coverage
    elif unique_platforms >= min_platforms and unique_authors >= 5 and has_news:
        decision = "auto_publish"
        reason = (
            f"{unique_platforms} platforms, {unique_authors} authors, "
            f"news coverage confirmed. Two-source verification passed."
        )
    # FLAG: 2+ platforms, 3+ authors, no news
    elif unique_platforms >= min_platforms and unique_authors >= min_authors:
        decision = "flag_for_review"
        reason = (
            f"{unique_platforms} platforms, {unique_authors} authors, "
            f"{'with' if has_news else 'without'} news coverage. Needs editorial review."
        )
    # Not enough signal
    else:
        decision = "queue_for_weekly"
        reason = (
            f"{unique_platforms} platforms, {unique_authors} authors. "
            f"Below bulletin threshold, queue for weekly issue."
        )

    result = {
        "decision": decision,
        "sources": unique_articles[:10],
        "primary_source": best_source,
        "credible_count": credible_count,
        "primary_count": len(primary_sources),
        "tier1_count": len(tier1_sources),
        "source_platforms": unique_platforms,
        "unique_authors": unique_authors,
        "has_primary_source": len(primary_sources) > 0,
        "news_coverage": has_news,
        "reason": reason,
    }

    print(f"Credibility Check [{topic_key}]: {decision} - {reason}")
    return result

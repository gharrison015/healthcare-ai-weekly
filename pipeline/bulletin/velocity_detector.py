"""
Multi-source velocity detector.

Clusters results from all monitors by topic (entity extraction),
then scores clusters by cross-platform velocity and source diversity.

TWO-SOURCE VERIFICATION: a cluster must have results from 2+ independent
sources (different platforms or different authors on the same platform)
to qualify as a velocity spike.
"""

import json
import os
import re
from collections import defaultdict
from datetime import datetime, timezone, timedelta


def load_config(config_path="bulletin/bulletin_config.json"):
    with open(config_path) as f:
        return json.load(f)


# ---------- Entity extraction ----------

KNOWN_ENTITIES = [
    "anthropic", "openai", "google", "microsoft", "epic", "oracle health",
    "cerner", "amazon", "apple", "nvidia", "meta", "deepmind",
    "fda", "cms", "hhs", "nih",
    "claude", "gpt", "gemini", "copilot", "medpalm",
    "ambience", "abridge", "nuance", "nabla", "hippocratic",
    "optum", "unitedhealth", "humana", "elevance", "cigna",
    "deloitte", "mckinsey", "accenture", "ey", "bcg", "chartis", "guidehouse",
]


def extract_entities(text):
    """Extract company/product names and key terms from text."""
    text_lower = text.lower()
    found = set()
    for entity in KNOWN_ENTITIES:
        if entity in text_lower:
            found.add(entity)
    # Extract hashtag topics
    hashtags = re.findall(r"#(\w+)", text)
    for ht in hashtags:
        found.add(ht.lower())
    return found


# ---------- Clustering ----------

def cluster_results(results):
    """Group results into topic clusters based on shared entities.

    Returns a dict mapping cluster_key -> list of result dicts.
    """
    result_entities = []
    for r in results:
        text = f"{r.get('title', '')} {r.get('text', '')}"
        entities = extract_entities(text)
        result_entities.append((r, entities))

    # Build entity -> result index
    entity_index = defaultdict(list)
    for i, (r, entities) in enumerate(result_entities):
        for entity in entities:
            entity_index[entity].append(i)

    assigned = set()
    clusters = {}

    sorted_entities = sorted(entity_index.items(), key=lambda x: len(x[1]), reverse=True)

    for entity, indices in sorted_entities:
        unassigned = [idx for idx in indices if idx not in assigned]
        if len(unassigned) < 2:
            continue
        cluster_key = entity
        cluster_items = []
        for idx in unassigned:
            assigned.add(idx)
            cluster_items.append(result_entities[idx][0])
        clusters[cluster_key] = cluster_items

    # Add unclustered items as singletons
    for i, (r, entities) in enumerate(result_entities):
        if i not in assigned:
            key = list(entities)[0] if entities else f"item_{i}"
            if key in clusters:
                clusters[key].append(r)
            else:
                clusters[key] = [r]

    return clusters


# ---------- Velocity computation ----------

def compute_velocity(cluster_items):
    """Compute engagement velocity and source diversity for a cluster.

    Returns a metrics dict including cross-platform counts.
    """
    now = datetime.now(timezone.utc)
    total_engagement = 0
    unique_authors = set()
    unique_platforms = set()
    earliest = now
    items_last_hour = []

    for item in cluster_items:
        total_engagement += item.get("engagement_score", 0)
        unique_authors.add(item.get("author", ""))
        unique_platforms.add(item.get("source_platform", ""))

        ts = item.get("timestamp", "")
        if ts:
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                dt = now
            if dt < earliest:
                earliest = dt
            if (now - dt).total_seconds() < 3600:
                items_last_hour.append(item)

    hours_elapsed = max((now - earliest).total_seconds() / 3600, 0.1)
    velocity = total_engagement / hours_elapsed

    last_hour_engagement = sum(i.get("engagement_score", 0) for i in items_last_hour)
    acceleration = last_hour_engagement / max(velocity, 1)

    # Check for news coverage in the cluster
    has_news = any(
        item.get("source_platform") in ("newsdata",)
        or item.get("is_news", False)
        for item in cluster_items
    )

    return {
        "total_engagement": total_engagement,
        "unique_authors": len(unique_authors),
        "unique_platforms": len(unique_platforms),
        "platforms": list(unique_platforms),
        "item_count": len(cluster_items),
        "hours_elapsed": round(hours_elapsed, 2),
        "velocity": round(velocity, 1),
        "velocity_last_hour": round(last_hour_engagement, 1),
        "acceleration": round(acceleration, 2),
        "is_accelerating": acceleration > 1.0,
        "has_news_coverage": has_news,
    }


# ---------- Dedup against published bulletins ----------

def get_published_slugs(bulletins_dir="data/bulletins"):
    """Load slugs/timestamps of previously published bulletins for dedup."""
    published = []
    if not os.path.exists(bulletins_dir):
        return published
    for filename in os.listdir(bulletins_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(bulletins_dir, filename)
            try:
                with open(filepath) as f:
                    bulletin = json.load(f)
                published.append({
                    "slug": bulletin.get("slug", ""),
                    "tags": bulletin.get("tags", []),
                    "timestamp": bulletin.get("timestamp", ""),
                    "headline": bulletin.get("headline", ""),
                })
            except (json.JSONDecodeError, IOError):
                continue
    return published


def is_duplicate(topic_key, published_bulletins, cooldown_hours=6):
    """Check if a topic was already covered within the cooldown window."""
    now = datetime.now(timezone.utc)
    for bulletin in published_bulletins:
        bulletin_tags = set(bulletin.get("tags", []))
        if topic_key in bulletin_tags or topic_key in bulletin.get("slug", ""):
            ts = bulletin.get("timestamp", "")
            if ts:
                try:
                    pub_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    if (now - pub_time).total_seconds() < cooldown_hours * 3600:
                        return True
                except ValueError:
                    pass
    return False


def bulletins_published_today(bulletins_dir="data/bulletins"):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    count = 0
    if not os.path.exists(bulletins_dir):
        return 0
    for filename in os.listdir(bulletins_dir):
        if filename.startswith(today) and filename.endswith(".json"):
            count += 1
    return count


# ---------- Big-ticket keyword check ----------

def has_big_ticket_keywords(cluster_items, big_ticket_keywords):
    """Check if any item in the cluster mentions big-ticket event keywords."""
    for item in cluster_items:
        text = f"{item.get('title', '')} {item.get('text', '')}".lower()
        for kw in big_ticket_keywords:
            if kw.lower() in text:
                return True
    return False


# ---------- Main entry point ----------

def detect_spikes(results, config_path="bulletin/bulletin_config.json",
                  bulletins_dir="data/bulletins"):
    """Run multi-source velocity detection on combined monitor results.

    Enforces TWO-SOURCE VERIFICATION: clusters must have 2+ unique platforms
    or 3+ unique authors to qualify.

    Returns a list of spike dicts sorted by velocity score.
    """
    config = load_config(config_path)
    verification = config.get("verification", {})
    limits = config.get("limits", {})

    min_platforms = verification.get("min_platforms", 2)
    min_authors = verification.get("min_unique_authors", 3)
    big_ticket_kws = verification.get("big_ticket_keywords", [])
    hours_back = verification.get("hours_back", 24)
    max_per_day = limits.get("max_bulletins_per_day", 3)
    cooldown = limits.get("cooldown_hours", 6)

    # Check daily limit
    today_count = bulletins_published_today(bulletins_dir)
    if today_count >= max_per_day:
        print(f"Velocity Detector: daily limit reached ({today_count}/{max_per_day})")
        return []

    # Cluster all results
    clusters = cluster_results(results)
    published = get_published_slugs(bulletins_dir)

    spikes = []
    remaining_slots = max_per_day - today_count

    for topic_key, cluster_items in clusters.items():
        # Skip duplicates
        if is_duplicate(topic_key, published, cooldown):
            continue

        metrics = compute_velocity(cluster_items)

        # TWO-SOURCE VERIFICATION
        # Must have 2+ platforms OR 3+ unique authors
        if metrics["unique_platforms"] < min_platforms and metrics["unique_authors"] < min_authors:
            continue

        # Single author cross-posting across platforms = SKIP
        if metrics["unique_authors"] <= 1:
            continue

        # Check for big-ticket relevance
        is_big_ticket = has_big_ticket_keywords(cluster_items, big_ticket_kws)

        # Compute composite velocity score
        velocity_score = min(100, int(
            (metrics["unique_platforms"] * 15)
            + (min(metrics["unique_authors"], 20) * 2)
            + (min(metrics["total_engagement"], 10000) / 100)
            + (20 if metrics["has_news_coverage"] else 0)
            + (15 if is_big_ticket else 0)
        ))

        # Sort items by engagement for representative selection
        sorted_items = sorted(
            cluster_items,
            key=lambda i: i.get("engagement_score", 0),
            reverse=True,
        )

        spikes.append({
            "topic_key": topic_key,
            "velocity_score": velocity_score,
            "metrics": metrics,
            "is_big_ticket": is_big_ticket,
            "representative_items": sorted_items[:5],
            "all_urls": [i["url"] for i in cluster_items if i.get("url")],
        })

    spikes.sort(key=lambda x: x["velocity_score"], reverse=True)
    spikes = spikes[:remaining_slots]

    print(f"Velocity Detector: {len(spikes)} topics exceeded thresholds from {len(clusters)} clusters")
    return spikes

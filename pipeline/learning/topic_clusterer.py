"""
Topic Clusterer -- Groups NotebookLM sources into learning topics.

Keyword-based scoring: for each source, score against each topic's keyword
list (count keyword matches in title + content). Assign source to the
highest-scoring topic. Then for each topic cluster, generate a 2-3 paragraph
summary by asking NotebookLM scoped to those source IDs.
"""

import json

from learning.content_extractor import ask_topic_summary


def score_source_for_topic(source, topic_keywords):
    """
    Score how well a source matches a topic based on keyword presence
    in the title and guide content.

    Returns a float score (0.0 to 1.0) representing the fraction of
    topic keywords found in the source text.
    """
    if not topic_keywords:
        return 0.0

    text_parts = []
    text_parts.append(source.get("title", "").lower())

    guide = source.get("guide")
    if guide:
        if isinstance(guide, dict):
            text_parts.append(str(guide.get("summary", "")).lower())
            keywords_list = guide.get("keywords", [])
            if isinstance(keywords_list, list):
                text_parts.extend([str(k).lower() for k in keywords_list])
            # Also check key_topics if present
            topics_list = guide.get("key_topics", [])
            if isinstance(topics_list, list):
                text_parts.extend([str(t).lower() for t in topics_list])
        elif isinstance(guide, str):
            text_parts.append(guide.lower())

    combined = " ".join(text_parts)

    matches = 0
    for kw in topic_keywords:
        if kw.lower() in combined:
            matches += 1

    return matches / len(topic_keywords)


def build_topic_config_dict(topics_list):
    """
    Convert the config topics array into a dict keyed by slug for clustering.

    Accepts either:
      - list of dicts with 'slug' key (config format)
      - dict keyed by slug (legacy/test format, returned as-is)
    """
    if isinstance(topics_list, dict):
        return topics_list

    config = {}
    for topic in topics_list:
        slug = topic["slug"]
        config[slug] = {
            "title": topic["title"],
            "description": topic["description"],
            "accent_color": topic.get("accent_color", "#059669"),
            "keywords": topic.get("keywords", []),
        }
    return config


def cluster_sources(sources, topic_config, threshold=0.15):
    """
    Assign each source to the best-matching topic cluster.

    Args:
        sources: list of extracted source dicts from content_extractor
        topic_config: either a list of topic dicts (from config) or a dict keyed by slug
        threshold: minimum score to include a source in a topic

    Returns:
        dict of topic_slug -> {
            slug, title, description, accent_color, keywords,
            sources: [list of source dicts],
            source_ids: [list of source IDs]
        }
    """
    topic_dict = build_topic_config_dict(topic_config)

    clusters = {}
    for slug, config in topic_dict.items():
        clusters[slug] = {
            "slug": slug,
            "title": config["title"],
            "description": config["description"],
            "accent_color": config.get("accent_color", "#059669"),
            "keywords": config.get("keywords", []),
            "sources": [],
            "source_ids": [],
        }

    # Score each source against each topic, assign to highest
    for source in sources:
        best_slug = None
        best_score = 0.0

        for slug, config in topic_dict.items():
            score = score_source_for_topic(source, config.get("keywords", []))
            if score > best_score:
                best_score = score
                best_slug = slug

        if best_slug and best_score >= threshold:
            clusters[best_slug]["sources"].append(source)
            clusters[best_slug]["source_ids"].append(source["source_id"])
        elif best_slug:
            # Low-confidence sources go into best match anyway
            clusters[best_slug]["sources"].append(source)
            clusters[best_slug]["source_ids"].append(source["source_id"])

    # Remove empty clusters
    clusters = {
        slug: cluster for slug, cluster in clusters.items()
        if cluster["sources"]
    }

    return clusters


def generate_topic_summaries(clusters, notebook_id):
    """
    For each cluster, ask NotebookLM to generate a 2-3 paragraph summary
    scoped to the cluster's sources:
        notebooklm ask "Summarize these sources for a non-technical business audience" -s [source_ids] --json
    """
    for slug, cluster in clusters.items():
        source_ids = cluster["source_ids"]
        if not source_ids:
            cluster["summary"] = cluster["description"]
            continue

        print(f"  Generating summary for '{cluster['title']}' ({len(source_ids)} sources)...")

        question = (
            "Summarize these sources for a non-technical business audience. "
            f"Focus on the key ideas about '{cluster['title']}'. "
            "Write 2-3 paragraphs. Be specific with facts, numbers, and examples. "
            "Do not use em dashes. Use plain, direct language."
        )

        summary = ask_topic_summary(question, source_ids, notebook_id)

        if summary:
            # Clean em dashes just in case
            summary = summary.replace("\u2014", " - ").replace("\u2013", " - ")
            cluster["summary"] = summary
        else:
            cluster["summary"] = cluster["description"]

    return clusters


def print_cluster_report(clusters):
    """Print a human-readable summary of the clustering results."""
    print(f"\nTopic Clustering Results")
    print(f"{'='*60}")
    for slug, cluster in clusters.items():
        source_count = len(cluster.get("sources", []))
        print(f"\n  {cluster['title']} [{slug}]")
        print(f"  Sources: {source_count}")
        for s in cluster.get("sources", []):
            print(f"    - {s.get('title', 'Unknown')[:55]}")
    print()

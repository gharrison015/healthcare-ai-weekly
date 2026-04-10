"""
Learning Pipeline -- Orchestrator for AI Learning content generation.

Runs: extract sources -> cluster into topics -> generate quizzes -> write output.

Usage:
    python -m learning.learning_pipeline
    python -m learning.learning_pipeline --config learning/learning_config.json
    python -m learning.learning_pipeline --skip-extract
    python -m learning.learning_pipeline --skip-quiz
    python -m learning.learning_pipeline --stage extract
    python -m learning.learning_pipeline --stage cluster
    python -m learning.learning_pipeline --stage quiz

Writes data/learn/[slug].json per topic + data/learn/manifest.json.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from learning.content_extractor import (
    set_notebook_context,
    extract_all_sources,
    load_cached_sources,
    save_sources_cache,
    SOURCES_CACHE_PATH,
)
from learning.topic_clusterer import (
    build_topic_config_dict,
    cluster_sources,
    generate_topic_summaries,
    print_cluster_report,
)
from learning.quiz_generator import generate_quiz_for_cluster


DEFAULT_CONFIG_PATH = "learning/learning_config.json"
DEFAULT_DATA_DIR = "data/learn"
DEFAULT_MANIFEST_PATH = "data/learn/manifest.json"


def load_config(config_path=None):
    """Load the learning pipeline configuration."""
    path = config_path or DEFAULT_CONFIG_PATH
    if not os.path.exists(path):
        print(f"Error: config file not found at {path}")
        sys.exit(1)

    with open(path) as f:
        return json.load(f)


def get_topic_config(config):
    """
    Extract topic configuration from the config dict.

    Supports both formats:
      - 'topics': list of dicts with 'slug' key (new format)
      - 'topic_clusters': dict keyed by slug (legacy format)
    """
    if "topics" in config:
        return config["topics"]
    if "topic_clusters" in config:
        return config["topic_clusters"]
    return []


def get_quiz_settings(config):
    """Extract quiz settings from config, supporting both key names."""
    return config.get("quiz", config.get("quiz_settings", {}))


def run_extract(config, skip_extract=False):
    """Stage 1: Extract content from NotebookLM sources."""
    print(f"\n{'='*60}")
    print("STAGE 1: EXTRACT SOURCES")
    print(f"{'='*60}")

    notebook_id = config["notebook_id"]

    if skip_extract:
        cached = load_cached_sources()
        if cached:
            print("Using cached source data...")
            print(f"  Loaded {len(cached)} cached sources")
            return cached
        print("  No cache found, extracting fresh...")

    set_notebook_context(notebook_id)
    sources = extract_all_sources(notebook_id, delay=2.0)
    save_sources_cache(sources)

    return sources


def run_cluster(config, sources):
    """Stage 2: Cluster sources into learning topics."""
    print(f"\n{'='*60}")
    print("STAGE 2: CLUSTER TOPICS")
    print(f"{'='*60}")

    topic_config = get_topic_config(config)
    clusters = cluster_sources(sources, topic_config)
    print_cluster_report(clusters)

    return clusters


def run_summaries(config, clusters):
    """Stage 3: Generate topic summaries via NotebookLM."""
    print(f"\n{'='*60}")
    print("STAGE 3: GENERATE SUMMARIES")
    print(f"{'='*60}")

    notebook_id = config["notebook_id"]
    clusters = generate_topic_summaries(clusters, notebook_id)

    return clusters


def run_quizzes(config, clusters, only_topic=None):
    """Stage 4: Generate quiz questions for each topic (or just one)."""
    print(f"\n{'='*60}")
    print("STAGE 4: GENERATE QUIZZES")
    print(f"{'='*60}")

    notebook_id = config["notebook_id"]
    quiz_settings = get_quiz_settings(config)

    for slug, cluster in clusters.items():
        if only_topic and slug != only_topic:
            print(f"  Skipping '{slug}' (only refreshing '{only_topic}')")
            continue
        quiz = generate_quiz_for_cluster(cluster, notebook_id, quiz_settings)
        cluster["quiz"] = quiz

    return clusters


def run_write_output(config, clusters, merge_with_existing=False):
    """Stage 5: Write topic JSON files and manifest.

    When merge_with_existing=True, keeps untouched topics from the prior manifest
    (used with --only-topic so one refresh doesn't wipe out the other topics).
    """
    print(f"\n{'='*60}")
    print("STAGE 5: WRITE OUTPUT")
    print(f"{'='*60}")

    data_dir = DEFAULT_DATA_DIR
    manifest_path = DEFAULT_MANIFEST_PATH

    # Allow config override
    output_config = config.get("output", {})
    if output_config.get("data_dir"):
        data_dir = output_config["data_dir"]
    if output_config.get("manifest_file"):
        manifest_path = output_config["manifest_file"]

    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(data_dir, exist_ok=True)

    manifest_topics = []

    # If merging, preload existing manifest topics for ones we're NOT refreshing
    existing_topics = {}
    if merge_with_existing and os.path.exists(manifest_path):
        try:
            with open(manifest_path) as f:
                old_manifest = json.load(f)
            for t in old_manifest.get("topics", []):
                existing_topics[t["slug"]] = t
        except Exception:
            pass

    refreshed_slugs = set(clusters.keys())

    # Keep existing topics that aren't being refreshed
    for slug, t in existing_topics.items():
        if slug not in refreshed_slugs:
            manifest_topics.append(t)

    # Write the refreshed topics
    for slug, cluster in clusters.items():
        topic_data = {
            "slug": slug,
            "title": cluster["title"],
            "description": cluster["description"],
            "accent_color": cluster.get("accent_color", "#059669"),
            "sources": cluster.get("source_ids", []),
            "source_count": len(cluster.get("sources", [])),
            "summary": cluster.get("summary", cluster["description"]),
            "quiz": cluster.get("quiz", {"title": f"Quick Check: {cluster['title']}", "questions": []}),
            "created_at": today,
            "updated_at": today,
        }

        output_path = os.path.join(data_dir, f"{slug}.json")
        with open(output_path, "w") as f:
            json.dump(topic_data, f, indent=2)
        print(f"  Wrote {output_path} ({len(topic_data['quiz'].get('questions', []))} questions)")

        manifest_topics.append({
            "slug": slug,
            "title": cluster["title"],
            "description": cluster["description"],
            "accent_color": cluster.get("accent_color", "#059669"),
            "source_count": len(cluster.get("sources", [])),
            "question_count": len(topic_data["quiz"].get("questions", [])),
        })

    manifest = {
        "generated_at": today,
        "topic_count": len(manifest_topics),
        "topics": manifest_topics,
    }

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"  Wrote manifest: {manifest_path}")

    return manifest


def main():
    parser = argparse.ArgumentParser(
        description="AI Learning Content + Quiz Generation Pipeline"
    )
    parser.add_argument(
        "--config", default=DEFAULT_CONFIG_PATH,
        help=f"Path to config file (default: {DEFAULT_CONFIG_PATH})"
    )
    parser.add_argument(
        "--skip-extract", action="store_true",
        help="Skip extraction, use cached source data"
    )
    parser.add_argument(
        "--skip-quiz", action="store_true",
        help="Skip quiz generation (useful for testing clustering)"
    )
    parser.add_argument(
        "--skip-summary", action="store_true",
        help="Skip summary generation (use topic descriptions instead)"
    )
    parser.add_argument(
        "--stage", choices=["extract", "cluster", "quiz", "all"],
        default="all",
        help="Run a specific stage or all stages"
    )
    parser.add_argument(
        "--only-topic",
        help="Only refresh the quiz for this topic slug (leaves other topics untouched)"
    )
    args = parser.parse_args()

    config = load_config(args.config)
    topic_config = get_topic_config(config)
    topic_count = len(topic_config) if isinstance(topic_config, list) else len(topic_config.keys())

    print("AI Learning Pipeline")
    print(f"Notebook: {config['notebook_id']}")
    print(f"Topics: {topic_count}")

    # Stage 1: Extract
    sources = run_extract(config, skip_extract=args.skip_extract)
    if args.stage == "extract":
        print(f"\nExtraction complete. {len(sources)} sources cached.")
        return

    # Stage 2: Cluster
    clusters = run_cluster(config, sources)
    if args.stage == "cluster":
        print("\nClustering complete.")
        return

    # Stage 3: Summaries
    if not args.skip_summary:
        clusters = run_summaries(config, clusters)

    # Stage 4: Quizzes
    if not args.skip_quiz and args.stage != "cluster":
        clusters = run_quizzes(config, clusters, only_topic=args.only_topic)

    # Stage 5: Write output (only write topics we actually refreshed)
    if args.only_topic:
        clusters = {k: v for k, v in clusters.items() if k == args.only_topic}
    manifest = run_write_output(config, clusters, merge_with_existing=bool(args.only_topic))

    print(f"\nDone. Generated {manifest['topic_count']} topics.")
    for t in manifest["topics"]:
        print(f"  {t['title']}: {t['question_count']} questions, {t['source_count']} sources")


if __name__ == "__main__":
    main()

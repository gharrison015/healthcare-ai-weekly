"""
Healthcare AI Weekly — Multi-Source Bulletin Pipeline Orchestrator

Runs the full bulletin detection and publishing pipeline:
  1. Multi-Source Monitor: poll Bluesky, HN, X, Newsdata, Reddit, Substack
  2. Velocity Detection: cluster by topic, enforce two-source verification
  3. Credibility Check: verify against credible news sources
  4. Bulletin Generator: Claude writes the take   (LOCAL/API-key mode only)
  5. Publish: save to data/bulletins/

Usage:
    python -m bulletin.bulletin_pipeline                 # Full run (local, needs API key)
    python -m bulletin.bulletin_pipeline --dry-run       # Test without publishing
    python -m bulletin.bulletin_pipeline --stage monitor # Run single stage
    python -m bulletin.bulletin_pipeline --cloud-mode    # Run 1-3, write candidates + heartbeat
                                                         #   (for remote trigger; agent writes bulletins)

CLOUD MODE:
  The --cloud-mode flag stops the pipeline after stage 3 (credibility check)
  and writes two files:
    - data/bulletins/_candidates.json  (verified topics ready for writing)
    - data/bulletins/_last_run.json    (heartbeat, ALWAYS written)
  The cloud agent then reads _candidates.json, writes bulletin bodies itself,
  and commits everything (including _last_run.json) back to the repo. This
  gives us a git-visible heartbeat for every run, even when zero bulletins
  are produced.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

from bulletin.sources import (
    BlueskyMonitor,
    HackerNewsMonitor,
    XScraper,
    NewsdataMonitor,
    RedditMonitor,
)
from bulletin.sources.substack_monitor import SubstackMonitor
from bulletin.velocity_detector import detect_spikes
from bulletin.credibility_checker import check_credibility
from bulletin.bulletin_generator import generate_bulletin, save_bulletin

logger = logging.getLogger(__name__)


def load_config(config_path="bulletin/bulletin_config.json"):
    with open(config_path) as f:
        return json.load(f)


def collect_all_sources(config_path="bulletin/bulletin_config.json"):
    """Run all enabled source monitors and return combined results."""
    config = load_config(config_path)
    sources_config = config.get("sources", {})
    verification = config.get("verification", {})
    hours_back = verification.get("hours_back", 24)

    all_results = []

    # Bluesky (free, no auth)
    if sources_config.get("bluesky", {}).get("enabled", True):
        keywords = sources_config["bluesky"].get("keywords", ["healthcare AI"])
        try:
            monitor = BlueskyMonitor()
            results = monitor.search(keywords, hours_back)
            print(f"  Bluesky: {len(results)} results")
            all_results.extend(results)
        except Exception as e:
            logger.warning("Bluesky monitor failed: %s", e)

    # Hacker News (free, no auth)
    if sources_config.get("hackernews", {}).get("enabled", True):
        keywords = sources_config["hackernews"].get("keywords", ["healthcare AI"])
        try:
            monitor = HackerNewsMonitor()
            results = monitor.search(keywords, hours_back)
            print(f"  Hacker News: {len(results)} results")
            all_results.extend(results)
        except Exception as e:
            logger.warning("HackerNews monitor failed: %s", e)

    # X/Twitter (needs credentials)
    if sources_config.get("x", {}).get("enabled", True):
        keywords = sources_config["x"].get("keywords", ["healthcare AI"])
        try:
            monitor = XScraper()
            results = monitor.search(keywords, hours_back)
            print(f"  X/Twitter: {len(results)} results")
            all_results.extend(results)
        except Exception as e:
            logger.warning("X scraper failed: %s", e)

    # Newsdata (needs API key)
    if sources_config.get("newsdata", {}).get("enabled", True):
        keywords = sources_config["newsdata"].get("keywords", ["healthcare AI"])
        try:
            monitor = NewsdataMonitor()
            results = monitor.search(keywords, hours_back)
            print(f"  Newsdata: {len(results)} results")
            all_results.extend(results)
        except Exception as e:
            logger.warning("Newsdata monitor failed: %s", e)

    # Reddit (works without auth, better with)
    if sources_config.get("reddit", {}).get("enabled", True):
        keywords = sources_config["reddit"].get("keywords", ["healthcare AI"])
        subreddits = sources_config["reddit"].get("subreddits")
        try:
            monitor = RedditMonitor()
            results = monitor.search(keywords, hours_back, subreddits)
            print(f"  Reddit: {len(results)} results")
            all_results.extend(results)
        except Exception as e:
            logger.warning("Reddit monitor failed: %s", e)

    # Substack RSS (free, no auth, no limits)
    if sources_config.get("substack", {}).get("enabled", True):
        keywords = sources_config.get("substack", {}).get("keywords", ["healthcare AI", "clinical AI", "medical AI"])
        try:
            monitor = SubstackMonitor()
            results = monitor.search(keywords, hours_back)
            print(f"  Substack: {len(results)} results")
            all_results.extend(results)
        except Exception as e:
            logger.warning("Substack monitor failed: %s", e)

    return all_results


def _write_heartbeat(bulletins_dir, source_counts, candidate_count, disposition, extra=None):
    """Write _last_run.json heartbeat file.

    Called at the end of every cloud-mode run, regardless of outcome, so that
    the cloud agent can commit it and we get a git-visible record of every
    trigger firing. This is what lets us answer "did the trigger run?" from
    `git log` without ever needing to open claude.ai.
    """
    os.makedirs(bulletins_dir, exist_ok=True)
    heartbeat = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source_counts": source_counts,
        "total_collected": sum(source_counts.values()),
        "candidate_count": candidate_count,
        "disposition": disposition,  # "no_results" | "no_spikes" | "no_credible" | "candidates_ready" | "error"
    }
    if extra:
        heartbeat.update(extra)
    path = os.path.join(bulletins_dir, "_last_run.json")
    with open(path, "w") as f:
        json.dump(heartbeat, f, indent=2)
    print(f"\n[heartbeat] Wrote {path}")
    return path


def _count_by_platform(results):
    counts = {}
    for r in results:
        p = r.get("source_platform", "unknown")
        counts[p] = counts.get(p, 0) + 1
    return counts


def run_cloud_mode(config_path="bulletin/bulletin_config.json",
                   bulletins_dir="data/bulletins"):
    """Run stages 1-3 and write _candidates.json + _last_run.json.

    This mode is designed for the remote cloud trigger which does NOT have
    an Anthropic API key (the agent IS Claude and will write bulletins
    itself). We run collection, velocity detection, and credibility checking
    using the proper Python modules, then hand off a clean list of verified
    candidates via JSON.

    Always writes a heartbeat file, even on zero-candidate runs.
    """
    print(f"\n{'='*60}")
    print(f"BULLETIN PIPELINE [CLOUD MODE] — "
          f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}")

    os.makedirs(bulletins_dir, exist_ok=True)
    candidates_path = os.path.join(bulletins_dir, "_candidates.json")

    # Stage 1: Multi-Source Monitor
    print(f"\n--- Stage 1: Multi-Source Monitor ---")
    try:
        all_results = collect_all_sources(config_path)
    except Exception as e:
        logger.exception("Collection failed")
        _write_heartbeat(bulletins_dir, {}, 0, "error", {"error": str(e)})
        # Wipe stale candidates so agent doesn't re-process old data
        with open(candidates_path, "w") as f:
            json.dump([], f)
        return []

    source_counts = _count_by_platform(all_results)

    if not all_results:
        print("No results from any source.")
        _write_heartbeat(bulletins_dir, source_counts, 0, "no_results")
        with open(candidates_path, "w") as f:
            json.dump([], f)
        return []

    print(f"\n  Total: {len(all_results)} results from all sources")

    # Stage 2: Velocity Detection
    print(f"\n--- Stage 2: Velocity Detection ---")
    spikes = detect_spikes(all_results, config_path, bulletins_dir)

    if not spikes:
        print("No velocity spikes detected (two-source verification).")
        _write_heartbeat(bulletins_dir, source_counts, 0, "no_spikes")
        with open(candidates_path, "w") as f:
            json.dump([], f)
        return []

    # Stage 3: Credibility Check
    print(f"\n--- Stage 3: Credibility Check ---")
    verified = []
    for spike in spikes:
        result = check_credibility(spike, config_path)
        spike["credibility"] = result
        if result["decision"] == "auto_publish":
            verified.append(spike)
        else:
            print(f"  skipped {spike.get('topic_key', '?')}: {result.get('reason', '')}")

    if not verified:
        print("No topics passed credibility check.")
        _write_heartbeat(bulletins_dir, source_counts, 0, "no_credible")
        with open(candidates_path, "w") as f:
            json.dump([], f)
        return []

    # Write candidates for the cloud agent to process
    with open(candidates_path, "w") as f:
        json.dump(verified, f, indent=2, default=str)

    _write_heartbeat(
        bulletins_dir,
        source_counts,
        len(verified),
        "candidates_ready",
        {"candidate_topics": [c.get("topic_key", "?") for c in verified]},
    )

    print(f"\n{'='*60}")
    print(f"CLOUD MODE COMPLETE — {len(verified)} candidate(s) ready for agent")
    print(f"Wrote: {candidates_path}")
    print(f"{'='*60}")
    return verified


def run_pipeline(dry_run=False, stage="all", config_path="bulletin/bulletin_config.json",
                 bulletins_dir="data/bulletins"):
    """Run the full multi-source bulletin pipeline or a specific stage.

    Args:
        dry_run: if True, skip publishing (save to stdout instead)
        stage: 'all', 'monitor', 'velocity', 'credibility', 'generate'
        config_path: path to bulletin_config.json
        bulletins_dir: directory for published bulletins

    Returns a list of published/generated bulletins.
    """
    print(f"\n{'='*60}")
    print(f"BULLETIN PIPELINE — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"{'='*60}")

    # Stage 1: Multi-Source Monitor
    print(f"\n--- Stage 1: Multi-Source Monitor ---")
    all_results = collect_all_sources(config_path)

    if not all_results:
        print("No results from any source. Pipeline complete.")
        return []

    print(f"\n  Total: {len(all_results)} results from all sources")

    if stage == "monitor":
        print(f"\nMonitor-only mode. Found {len(all_results)} results.")
        # Summary by platform
        platforms = {}
        for r in all_results:
            p = r.get("source_platform", "unknown")
            platforms[p] = platforms.get(p, 0) + 1
        for p, count in sorted(platforms.items()):
            print(f"  {p}: {count}")
        return all_results

    # Stage 2: Velocity Detection (with two-source verification)
    print(f"\n--- Stage 2: Velocity Detection ---")
    spikes = detect_spikes(all_results, config_path, bulletins_dir)

    if not spikes:
        print("No velocity spikes detected (two-source verification). Pipeline complete.")
        return []

    if stage == "velocity":
        print(f"\nVelocity-only mode. Found {len(spikes)} spikes.")
        print(json.dumps(spikes, indent=2, default=str))
        return spikes

    # Stage 3: Credibility Check
    print(f"\n--- Stage 3: Credibility Check ---")
    verified_topics = []
    flagged_topics = []
    skipped_topics = []

    for spike in spikes:
        result = check_credibility(spike, config_path)
        spike["credibility"] = result

        if result["decision"] == "auto_publish":
            verified_topics.append(spike)
        elif result["decision"] == "flag_for_review":
            flagged_topics.append(spike)
        else:
            skipped_topics.append(spike)

    if flagged_topics:
        print(f"\nFlagged for review ({len(flagged_topics)}):")
        for t in flagged_topics:
            print(f"  - {t['topic_key']}: {t['credibility']['reason']}")

    if skipped_topics:
        print(f"\nSkipped/queued ({len(skipped_topics)}):")
        for t in skipped_topics:
            print(f"  - {t['topic_key']}: {t['credibility']['reason']}")

    if not verified_topics:
        print("No topics passed credibility check for auto-publish.")
        return []

    if stage == "credibility":
        print(f"\nCredibility-only mode. {len(verified_topics)} verified.")
        return verified_topics

    # Stage 4: Bulletin Generator
    print(f"\n--- Stage 4: Bulletin Generator ---")
    bulletins = []

    for topic in verified_topics:
        try:
            bulletin = generate_bulletin(topic, topic["credibility"])
            bulletins.append(bulletin)
        except Exception as e:
            print(f"Failed to generate bulletin for {topic['topic_key']}: {e}")

    if not bulletins:
        print("No bulletins generated.")
        return []

    # Stage 5: Publish
    print(f"\n--- Stage 5: Publish ---")
    published = []

    for bulletin in bulletins:
        if dry_run:
            print(f"\n[DRY RUN] Would publish:")
            print(json.dumps(bulletin, indent=2))
            published.append(bulletin)
        else:
            filepath = save_bulletin(bulletin, bulletins_dir)
            bulletin["_filepath"] = filepath
            published.append(bulletin)

    print(f"\n{'='*60}")
    print(f"PIPELINE COMPLETE — {len(published)} bulletin(s) {'generated' if dry_run else 'published'}")
    print(f"{'='*60}")

    return published


def main():
    parser = argparse.ArgumentParser(
        description="Healthcare AI Weekly — Multi-Source Bulletin Pipeline"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run pipeline without publishing (output to stdout)",
    )
    parser.add_argument(
        "--stage",
        choices=["all", "monitor", "velocity", "credibility", "generate"],
        default="all",
        help="Run a specific stage or all stages",
    )
    parser.add_argument(
        "--cloud-mode",
        action="store_true",
        help=(
            "Run stages 1-3 and write _candidates.json + _last_run.json. "
            "Used by the remote cloud trigger (no API key; agent writes bulletins)."
        ),
    )
    parser.add_argument(
        "--config",
        default="bulletin/bulletin_config.json",
        help="Path to bulletin config JSON",
    )
    parser.add_argument(
        "--bulletins-dir",
        default="data/bulletins",
        help="Directory where candidates/heartbeat are written",
    )
    args = parser.parse_args()

    if args.cloud_mode:
        run_cloud_mode(
            config_path=args.config,
            bulletins_dir=args.bulletins_dir,
        )
    else:
        run_pipeline(
            dry_run=args.dry_run,
            stage=args.stage,
            config_path=args.config,
            bulletins_dir=args.bulletins_dir,
        )


if __name__ == "__main__":
    main()

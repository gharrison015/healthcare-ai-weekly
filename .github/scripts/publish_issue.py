#!/usr/bin/env python3
"""Publish a generated newsletter issue into content/ and update the manifest.

Usage: publish_issue.py YYYY-MM-DD

Expects the pipeline to have already produced:
  pipeline/data/curated/<date>.json
  pipeline/data/issues/<date>/index.html
  pipeline/data/issues/<date>/email.html

Writes:
  content/issues/<date>/data.json     (copy of curated JSON)
  content/issues/<date>/index.html    (copy of deep-dive HTML)
  content/manifests/issues.json       (prepends or updates the entry)
"""

import json
import re
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PIPELINE_DIR = REPO_ROOT / "pipeline"
CONTENT_DIR = REPO_ROOT / "content"

TRACKED_FIRMS = [
    "Guidehouse", "Deloitte", "McKinsey", "BCG", "Accenture", "Chartis",
    "Optum Advisory", "EY Parthenon", "EY", "Huron", "BRG", "Bain",
    "Oliver Wyman", "KPMG", "PwC",
]


def count_stories(sections: dict, key: str) -> int:
    return len(sections.get(key) or [])


def compute_week_range(date_str: str) -> str:
    end = datetime.strptime(date_str, "%Y-%m-%d")
    start = end - timedelta(days=7)
    return f"{start.strftime('%B %d')} - {end.strftime('%B %d, %Y')}"


def build_manifest_entry(date_str: str, curated: dict) -> dict:
    sections = curated.get("sections", {}) or {}
    # Handle legacy deal_flow -> ma_partnerships rename
    ma_key = "ma_partnerships" if "ma_partnerships" in sections else "deal_flow"
    return {
        "date": date_str,
        "week_range": curated.get("week_range") or compute_week_range(date_str),
        "editorial_summary": curated.get("editorial_summary", ""),
        "top_stories": count_stories(sections, "top_stories"),
        "vbc_watch": count_stories(sections, "vbc_watch"),
        "did_you_know": count_stories(sections, "did_you_know"),
        "ma_partnerships": count_stories(sections, ma_key),
        "consulting_intelligence": count_stories(sections, "consulting_intelligence"),
    }


def upsert_manifest(manifest_path: Path, entry: dict) -> None:
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
    else:
        manifest = []
    # Drop any existing entry for this date, then put the new one on top.
    filtered = [e for e in manifest if e.get("date") != entry["date"]]
    filtered.insert(0, entry)
    manifest_path.write_text(json.dumps(filtered, indent=2) + "\n")


def slugify(text: str, max_len: int = 80) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:max_len].rstrip("-")


def detect_firm(story: dict) -> str | None:
    """Find which tracked firm is the subject of this CI story."""
    haystack = " ".join([
        story.get("headline", ""),
        story.get("so_what", ""),
        story.get("consulting_signal", ""),
        (story.get("source_article") or {}).get("source", ""),
        (story.get("source_article") or {}).get("title", ""),
    ]).lower()
    for firm in TRACKED_FIRMS:
        if firm.lower() in haystack:
            return firm
    return None


def ci_entry_from_story(story: dict, firm: str, date_str: str) -> dict:
    source = story.get("source_article") or {}
    headline = story.get("headline", "")
    summary = story.get("email_summary") or story.get("so_what", "")
    relevance = "healthcare_direct" if "healthcare" in headline.lower() or "care" in headline.lower() else "healthcare_adjacent"
    slug = f"{slugify(firm)}-{slugify(headline)}"[:100].rstrip("-")
    return {
        "firm": firm,
        "headline": headline,
        "summary": summary,
        "so_what": story.get("so_what", ""),
        "relevance": relevance,
        "source_url": source.get("url", ""),
        "published_date": date_str,
        "original_title": source.get("title", ""),
        "slug": slug,
    }


def upsert_ci_manifest(manifest_path: Path, entries: list[dict]) -> None:
    """Prepend new CI entries to manifest.json, dropping any existing dupes by slug."""
    existing = []
    if manifest_path.exists():
        existing = json.loads(manifest_path.read_text())
    new_slugs = {e["slug"] for e in entries}
    kept = [e for e in existing if e.get("slug") not in new_slugs]
    manifest_entries = [
        {k: e[k] for k in ("slug", "headline", "firm", "relevance", "published_date")}
        for e in entries
    ]
    manifest_path.write_text(json.dumps(manifest_entries + kept, indent=2) + "\n")


def publish_consulting_intelligence(curated: dict, date_str: str) -> int:
    ci_stories = (curated.get("sections") or {}).get("consulting_intelligence") or []
    if not ci_stories:
        return 0

    ci_dir = CONTENT_DIR / "consulting-intelligence"
    ci_dir.mkdir(parents=True, exist_ok=True)

    written = []
    for story in ci_stories:
        firm = detect_firm(story)
        if not firm:
            print(f"  skip CI story (no tracked firm matched): {story.get('headline', '')[:60]}")
            continue
        entry = ci_entry_from_story(story, firm, date_str)
        entry_path = ci_dir / f"{entry['slug']}.json"
        if entry_path.exists():
            print(f"  skip CI entry (slug exists): {entry['slug']}")
            continue
        entry_path.write_text(json.dumps(entry, indent=2) + "\n")
        written.append(entry)
        print(f"  wrote CI entry: {entry['slug']}")

    if written:
        upsert_ci_manifest(ci_dir / "manifest.json", written)
    return len(written)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: publish_issue.py YYYY-MM-DD", file=sys.stderr)
        return 2
    date_str = sys.argv[1]

    curated_src = PIPELINE_DIR / "data" / "curated" / f"{date_str}.json"
    index_src = PIPELINE_DIR / "data" / "issues" / date_str / "index.html"

    if not curated_src.exists():
        print(f"error: {curated_src} not found (did the curator stage run?)", file=sys.stderr)
        return 1
    if not index_src.exists():
        print(f"error: {index_src} not found (did the generator stage run?)", file=sys.stderr)
        return 1

    dest_dir = CONTENT_DIR / "issues" / date_str
    dest_dir.mkdir(parents=True, exist_ok=True)

    curated = json.loads(curated_src.read_text())
    (dest_dir / "data.json").write_text(json.dumps(curated, indent=2) + "\n")
    shutil.copy2(index_src, dest_dir / "index.html")

    manifest_path = CONTENT_DIR / "manifests" / "issues.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    upsert_manifest(manifest_path, build_manifest_entry(date_str, curated))

    ci_count = publish_consulting_intelligence(curated, date_str)
    print(f"published {date_str} -> content/issues/{date_str}/ ({ci_count} CI entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

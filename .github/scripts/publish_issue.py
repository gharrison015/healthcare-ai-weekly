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
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PIPELINE_DIR = REPO_ROOT / "pipeline"
CONTENT_DIR = REPO_ROOT / "content"


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

    print(f"published {date_str} -> content/issues/{date_str}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())

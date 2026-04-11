"""Fuzzy-match deduplication for consulting intelligence entries.

Motivation: two different publishers covering the same announcement
get different URLs and different slugs, so a naive URL-based dedup
misses them. This module compares normalized headlines within a firm
and date window, and flags pairs above a similarity threshold as
duplicates.

Usage as a CLI:
    # Dry-run audit — reports duplicates but changes nothing
    python -m consulting_intelligence.dedup --check

    # Delete duplicates and update the manifest
    python -m consulting_intelligence.dedup --apply

    # Tune thresholds
    python -m consulting_intelligence.dedup --check --threshold 0.75 --window 21

Usage from Python (intended for future collectors):
    from consulting_intelligence import is_duplicate, load_entries

    existing = load_entries(content_dir)
    if is_duplicate(new_entry, existing):
        print("skipping duplicate")
    else:
        # write the new entry
        ...
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Iterable, List, Optional

DEFAULT_SIMILARITY_THRESHOLD = 0.80
DEFAULT_WINDOW_DAYS = 14

# Words that carry no disambiguating signal for consulting-intelligence
# headlines. Removed before comparison so that stopwords do not inflate
# similarity scores.
STOPWORDS = frozenset(
    """
    a an the and or of to for with in on at by from into new its their
    this that these those is are was were be been being as it's
    """.split()
)


@dataclass
class ConsultingEntry:
    slug: str
    firm: str
    headline: str
    published_date: str  # ISO YYYY-MM-DD
    source_url: str = ""
    path: str = ""
    raw: dict = field(default_factory=dict)


def _normalize(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace, drop stopwords."""
    if not text:
        return ""
    t = text.lower()
    t = re.sub(r"[^\w\s]", " ", t)
    tokens = [w for w in t.split() if w and w not in STOPWORDS]
    return " ".join(tokens)


def headline_similarity(a: str, b: str) -> float:
    """Return a 0.0-1.0 similarity score between two normalized headlines.

    Uses a blend of SequenceMatcher ratio and Jaccard over token sets, so
    both word-order similarity ("Bain expands Palantir partnership to
    accelerate AI") and token overlap ("Bain Palantir agentic") score
    high. Either signal alone is enough for obvious duplicates.
    """
    na = _normalize(a)
    nb = _normalize(b)
    if not na or not nb:
        return 0.0

    # Sequence similarity (accounts for word order)
    seq = SequenceMatcher(None, na, nb).ratio()

    # Jaccard over token sets (accounts for shared vocabulary)
    tokens_a = set(na.split())
    tokens_b = set(nb.split())
    if not tokens_a or not tokens_b:
        jaccard = 0.0
    else:
        jaccard = len(tokens_a & tokens_b) / len(tokens_a | tokens_b)

    # Max of the two — a strong signal on either axis is enough
    return max(seq, jaccard)


def _parse_date(s: str) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def _within_window(a: str, b: str, window_days: int) -> bool:
    da, db = _parse_date(a), _parse_date(b)
    if not da or not db:
        # If either date is missing/unparseable, don't use the date
        # constraint to gate dedup. Better safe than sorry.
        return True
    return abs((da - db).days) <= window_days


def is_duplicate(
    candidate: ConsultingEntry | dict,
    existing: Iterable[ConsultingEntry],
    *,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    window_days: int = DEFAULT_WINDOW_DAYS,
) -> Optional[ConsultingEntry]:
    """Return the first existing entry that duplicates the candidate.

    Returns None if no duplicate was found, otherwise the matching entry.
    A duplicate is defined as:
      - same firm (case-insensitive)
      - published within `window_days` of any existing entry
      - headline similarity >= `threshold`
    """
    if isinstance(candidate, dict):
        cand_firm = (candidate.get("firm") or "").strip()
        cand_headline = candidate.get("headline") or ""
        cand_date = candidate.get("published_date") or ""
    else:
        cand_firm = candidate.firm
        cand_headline = candidate.headline
        cand_date = candidate.published_date

    cand_firm_norm = cand_firm.lower().strip()

    for ex in existing:
        if ex.firm.lower().strip() != cand_firm_norm:
            continue
        if not _within_window(cand_date, ex.published_date, window_days):
            continue
        if headline_similarity(cand_headline, ex.headline) >= threshold:
            return ex
    return None


def load_entries(content_dir: str) -> List[ConsultingEntry]:
    """Load all *.json files in content_dir except manifest.json."""
    entries: List[ConsultingEntry] = []
    if not os.path.isdir(content_dir):
        return entries
    for fname in sorted(os.listdir(content_dir)):
        if not fname.endswith(".json") or fname == "manifest.json":
            continue
        path = os.path.join(content_dir, fname)
        try:
            with open(path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        entries.append(
            ConsultingEntry(
                slug=data.get("slug") or fname.replace(".json", ""),
                firm=data.get("firm") or "",
                headline=data.get("headline") or "",
                published_date=data.get("published_date") or "",
                source_url=data.get("source_url") or "",
                path=path,
                raw=data,
            )
        )
    return entries


def find_duplicates(
    entries: List[ConsultingEntry],
    *,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    window_days: int = DEFAULT_WINDOW_DAYS,
) -> List[tuple]:
    """Return a list of (keeper, duplicate, score) tuples.

    Sorts entries by published_date DESC and scans forward; the first
    occurrence is kept, subsequent near-matches are flagged as duplicates
    of it. "Keeper = newest" matches the convention used in the manual
    cleanups of Bain/Palantir and PwC/Leah.
    """
    # Most recent first so the keeper is the freshest
    sorted_entries = sorted(
        entries, key=lambda e: e.published_date, reverse=True
    )
    seen: List[ConsultingEntry] = []
    dupes: List[tuple] = []

    for e in sorted_entries:
        match = is_duplicate(
            e, seen, threshold=threshold, window_days=window_days
        )
        if match:
            score = headline_similarity(match.headline, e.headline)
            dupes.append((match, e, score))
        else:
            seen.append(e)
    return dupes


def _rewrite_manifest(content_dir: str, remaining: List[ConsultingEntry]) -> None:
    """Rewrite manifest.json, preserving the order of the existing manifest
    for entries that still exist. Entries that aren't referenced in the
    existing manifest get appended at the end sorted by date DESC.

    Order preservation matters so that a dedup run only changes what it
    needs to (the deleted entries), keeping git diffs minimal.
    """
    manifest_path = os.path.join(content_dir, "manifest.json")
    remaining_by_slug = {e.slug: e for e in remaining}

    original_order: List[str] = []
    if os.path.isfile(manifest_path):
        try:
            with open(manifest_path) as f:
                existing = json.load(f)
            original_order = [
                m.get("slug") for m in existing if isinstance(m, dict) and m.get("slug")
            ]
        except (json.JSONDecodeError, OSError):
            original_order = []

    ordered: List[ConsultingEntry] = []
    seen = set()
    for slug in original_order:
        entry = remaining_by_slug.get(slug)
        if entry and slug not in seen:
            ordered.append(entry)
            seen.add(slug)

    # Append any entries that weren't in the original manifest, newest first.
    leftovers = [e for e in remaining if e.slug not in seen]
    leftovers.sort(key=lambda e: e.published_date, reverse=True)
    ordered.extend(leftovers)

    manifest = [
        {
            "slug": e.slug,
            "headline": e.headline,
            "firm": e.firm,
            "relevance": e.raw.get("relevance") or "healthcare_adjacent",
            "published_date": e.published_date,
        }
        for e in ordered
    ]
    # Match existing manifest convention: no trailing newline, so a
    # dedup run on a clean directory produces zero diffs.
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fuzzy-match dedup for consulting intelligence entries."
    )
    parser.add_argument(
        "--content-dir",
        default="content/consulting-intelligence",
        help="Directory containing consulting intelligence JSON files "
        "(relative to the repo root)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report duplicates without changing anything (default)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Delete duplicate files and rewrite the manifest",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_SIMILARITY_THRESHOLD,
        help=f"Similarity threshold 0.0-1.0 "
        f"(default {DEFAULT_SIMILARITY_THRESHOLD})",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=DEFAULT_WINDOW_DAYS,
        help=f"Date window in days for considering two entries "
        f"(default {DEFAULT_WINDOW_DAYS})",
    )
    args = parser.parse_args()

    # Resolve content dir: relative paths are anchored at the repo root,
    # which is the parent of pipeline/. CWD may be pipeline/ or repo root.
    if os.path.isabs(args.content_dir):
        content_dir = args.content_dir
    else:
        cwd = os.getcwd()
        candidates = [
            os.path.join(cwd, args.content_dir),
            os.path.join(cwd, "..", args.content_dir),
        ]
        content_dir = next(
            (c for c in candidates if os.path.isdir(c)), candidates[0]
        )

    content_dir = os.path.normpath(content_dir)
    if not os.path.isdir(content_dir):
        print(f"[dedup] ERROR: content dir not found: {content_dir}")
        return 2

    entries = load_entries(content_dir)
    print(f"[dedup] Scanning {len(entries)} consulting entries in {content_dir}")
    print(
        f"[dedup] Threshold: {args.threshold} | Window: {args.window} days"
    )

    dupes = find_duplicates(
        entries, threshold=args.threshold, window_days=args.window
    )

    if not dupes:
        print("[dedup] No duplicates found. All clean.")
        return 0

    print(f"\n[dedup] Found {len(dupes)} duplicate(s):\n")
    for keeper, dupe, score in dupes:
        print(f"  Keep:   [{keeper.published_date}] {keeper.headline}")
        print(f"  Drop:   [{dupe.published_date}] {dupe.headline}")
        print(f"  Score:  {score:.2f}  (firm={keeper.firm})")
        print(f"  File:   {os.path.basename(dupe.path)}")
        print()

    if not args.apply:
        print("[dedup] Dry run (default). Pass --apply to delete files and rewrite manifest.")
        return 0

    # Apply: delete duplicate files, rewrite manifest with survivors
    dupe_paths = {d[1].path for d in dupes}
    for path in dupe_paths:
        try:
            os.remove(path)
            print(f"[dedup] Deleted {os.path.basename(path)}")
        except OSError as e:
            print(f"[dedup] Failed to delete {path}: {e}")

    survivors = [e for e in entries if e.path not in dupe_paths]
    _rewrite_manifest(content_dir, survivors)
    print(f"[dedup] Rewrote manifest.json with {len(survivors)} entries")
    print(f"[dedup] Removed {len(dupe_paths)} duplicate file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

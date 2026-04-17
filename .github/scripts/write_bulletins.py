#!/usr/bin/env python3
"""Turn velocity-detector candidates into published bulletins.

Reads `pipeline/data/bulletins/_candidates.json`, picks the top candidates
whose best URL is from a credible source (not pure Reddit/Twitter
speculation), calls Claude Haiku to write a 3-5 sentence bulletin body
with a healthcare angle, and writes:
  - content/bulletins/<slug>.json  (one per bulletin)
  - content/manifests/bulletins.json  (manifest refreshed; newest first)

Skips candidates whose slug already has a bulletin file (idempotent
across 4-hour cron runs).

Also archives bulletins older than 7 days into content/bulletins/archive/
so the public ticker stays fresh without a separate Sunday job.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PIPELINE_DIR = REPO_ROOT / "pipeline"
CONTENT_DIR = REPO_ROOT / "content"
BULLETINS_DIR = CONTENT_DIR / "bulletins"
ARCHIVE_DIR = BULLETINS_DIR / "archive"
MANIFEST_PATH = CONTENT_DIR / "manifests" / "bulletins.json"
CANDIDATES_PATH = PIPELINE_DIR / "data" / "bulletins" / "_candidates.json"

MAX_BULLETINS_PER_RUN = 2
ARCHIVE_AFTER_DAYS = 7

# URLs we will NOT lead a bulletin with — too speculative or low-signal.
LOW_SIGNAL_DOMAINS = (
    "reddit.com", "www.reddit.com", "old.reddit.com",
    "twitter.com", "x.com",
)


def slugify(text: str, max_len: int = 70) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:max_len].rstrip("-")


def pick_lead_url(candidate: dict) -> tuple[str, str, str] | None:
    """Return (url, source_name, title) for the best representative item.

    Prefers non-social-media URLs; if only social-media URLs exist, skip
    the candidate (the pipeline already auto_publish-flagged it, but
    writing a bulletin from a Reddit post alone is the wrong bar).
    """
    for item in candidate.get("representative_items", []):
        url = item.get("url") or ""
        external = item.get("external_url") or ""
        # Prefer external_url when present (often the real source)
        target = external if external and not any(d in external for d in LOW_SIGNAL_DOMAINS) else url
        if not target:
            continue
        if any(d in target for d in LOW_SIGNAL_DOMAINS):
            continue
        source = item.get("source_platform", "unknown")
        title = item.get("title", "")
        # Map source_platform to a readable source name
        if "anthropic.com" in target:
            source = "Anthropic"
        elif "openai.com" in target:
            source = "OpenAI"
        elif "cnbc.com" in target:
            source = "CNBC"
        elif "theverge.com" in target:
            source = "The Verge"
        elif "news.ycombinator.com" in target:
            source = "Hacker News"
        return target, source, title
    return None


def load_existing_slugs() -> set[str]:
    if not BULLETINS_DIR.exists():
        return set()
    return {
        p.stem for p in BULLETINS_DIR.glob("*.json")
        if not p.name.startswith("_")
    }


def load_existing_source_urls() -> set[str]:
    """Return the set of source URLs already represented in active bulletins."""
    urls: set[str] = set()
    if not BULLETINS_DIR.exists():
        return urls
    for p in BULLETINS_DIR.glob("*.json"):
        if p.name.startswith("_"):
            continue
        try:
            data = json.loads(p.read_text())
        except Exception:
            continue
        url = data.get("source_url")
        if url:
            urls.add(url)
    return urls


def archive_old_bulletins() -> int:
    """Move bulletins older than ARCHIVE_AFTER_DAYS into archive/. Returns count."""
    if not BULLETINS_DIR.exists():
        return 0
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    cutoff = datetime.now(timezone.utc) - timedelta(days=ARCHIVE_AFTER_DAYS)
    moved = 0
    for path in BULLETINS_DIR.glob("*.json"):
        if path.name.startswith("_"):
            continue
        try:
            data = json.loads(path.read_text())
        except Exception:
            continue
        ts = data.get("timestamp")
        if not ts:
            continue
        try:
            bulletin_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            continue
        if bulletin_time < cutoff:
            target = ARCHIVE_DIR / path.name
            path.rename(target)
            moved += 1
    return moved


def write_body_with_claude(candidate: dict, lead_url: str, lead_title: str) -> tuple[str, str]:
    """Call Claude Haiku to produce (headline, body) for the bulletin."""
    from anthropic import Anthropic

    client = Anthropic()
    metrics = candidate.get("metrics", {})
    context_lines = [
        f"Topic key: {candidate.get('topic_key')}",
        f"Velocity score: {candidate.get('velocity_score')}",
        f"Unique authors: {metrics.get('unique_authors')}",
        f"Platforms covering: {', '.join(metrics.get('platforms', []))}",
        f"Lead article title: {lead_title}",
        f"Lead article URL: {lead_url}",
        "",
        "Top representative items from the pipeline (already two-source verified):",
    ]
    for item in candidate.get("representative_items", [])[:5]:
        context_lines.append(f"  - [{item.get('source_platform')}] {item.get('title','')[:140]}")

    prompt = f"""You are the Healthcare AI Weekly bulletin writer. Your voice: direct, confident healthcare AI consultant. No em dashes ever. No marketing fluff.

Write ONE bulletin about the event below. Output must be a JSON object with two string fields: `headline` and `body`.

- headline: 8-14 words, hook style, present tense, no clickbait
- body: 3-5 sentences. Lead with what happened. Then why it matters specifically for healthcare AI (clinical workflows, EHR, value-based care, consulting implications, vendor landscape). Never fabricate facts not present in the context below. Do not repeat the headline.

CONTEXT:
{chr(10).join(context_lines)}

Respond with ONLY a JSON object, no other text."""

    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text.strip()
    # Strip code fences if the model added them
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
    parsed = json.loads(raw)
    return parsed["headline"].strip(), parsed["body"].strip()


def update_manifest(new_entries: list[dict]) -> None:
    """Rewrite manifest so the latest bulletins sit on top (newest first)."""
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = {"bulletins": []}
    if MANIFEST_PATH.exists():
        try:
            existing = json.loads(MANIFEST_PATH.read_text())
        except Exception:
            existing = {"bulletins": []}
    current = existing.get("bulletins", [])
    current_slugs = {e.get("slug") for e in current}
    merged = [e for e in new_entries if e["slug"] not in current_slugs] + current

    # Rebuild the manifest from active bulletin files only (drop archived)
    active_slugs = {p.stem for p in BULLETINS_DIR.glob("*.json") if not p.name.startswith("_")}
    merged = [e for e in merged if e.get("slug") in active_slugs]
    merged.sort(key=lambda e: e.get("timestamp", ""), reverse=True)

    MANIFEST_PATH.write_text(json.dumps({"bulletins": merged}, indent=2) + "\n")


def main() -> int:
    if not CANDIDATES_PATH.exists():
        print("no candidates file — pipeline didn't run or wrote nothing")
        return 0

    candidates = json.loads(CANDIDATES_PATH.read_text() or "[]")
    if not candidates:
        print("0 candidates from pipeline — nothing to write")
        archived = archive_old_bulletins()
        if archived:
            print(f"archived {archived} old bulletin(s)")
            update_manifest([])
        return 0

    BULLETINS_DIR.mkdir(parents=True, exist_ok=True)
    existing = load_existing_slugs()
    existing_urls = load_existing_source_urls()

    new_entries: list[dict] = []
    written = 0

    for candidate in candidates[:MAX_BULLETINS_PER_RUN + 3]:  # scan a few extras to find credible leads
        if written >= MAX_BULLETINS_PER_RUN:
            break
        lead = pick_lead_url(candidate)
        if not lead:
            print(f"skip {candidate.get('topic_key')} — no credible lead URL")
            continue
        lead_url, source_name, lead_title = lead
        if lead_url in existing_urls:
            print(f"skip {candidate.get('topic_key')} — source URL already bulletined")
            continue
        slug_seed = f"{candidate.get('topic_key','')}-{lead_title}"
        slug = slugify(slug_seed)
        if slug in existing:
            print(f"skip {slug} — bulletin file already exists")
            continue

        try:
            headline, body = write_body_with_claude(candidate, lead_url, lead_title)
        except Exception as e:
            print(f"skip {slug} — claude call failed: {e}")
            continue

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        metrics = candidate.get("metrics", {})
        bulletin = {
            "timestamp": timestamp,
            "slug": slug,
            "headline": headline,
            "body": body,
            "source_url": lead_url,
            "source_name": source_name,
            "velocity_score": candidate.get("velocity_score", 0),
            "verification": "confirmed",
            "verified_sources": metrics.get("platforms", []),
            "tags": [candidate.get("topic_key", "")],
        }
        (BULLETINS_DIR / f"{slug}.json").write_text(json.dumps(bulletin, indent=2) + "\n")
        print(f"wrote bulletin: {slug}")
        written += 1
        new_entries.append({
            "slug": slug,
            "headline": headline,
            "timestamp": timestamp,
            "source_name": source_name,
            "verification": "confirmed",
            "tags": bulletin["tags"],
        })

    archived = archive_old_bulletins()
    if archived:
        print(f"archived {archived} old bulletin(s)")

    if new_entries or archived:
        update_manifest(new_entries)

    print(f"done: {written} new bulletin(s), {archived} archived")
    return 0


if __name__ == "__main__":
    sys.exit(main())

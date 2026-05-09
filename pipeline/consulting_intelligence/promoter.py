"""Promote bulletins into consulting-intelligence stubs.

Motivation: the bulletin pipeline detects breaking AI/healthcare news every 4 hours,
but the consulting-intelligence corpus is only refreshed once a week by the curator.
A story like the Anthropic + Blackstone + Hellman & Friedman + Goldman Sachs JV gets
caught as a bulletin within hours, but does not reach consulting-intelligence until
the next Friday curation — and only if the curator's section rules permit.

This module bridges that gap. It scans existing bulletins, matches them against
consulting-intelligence triggers (tracked firms + competitive-entrant patterns), and
writes new consulting-intelligence stubs for unmatched ones. Existing entries are
left alone.

Triggers (from guardrails.json):
  Pattern (a) — tracked firm: McKinsey, Deloitte, BCG, Accenture, KPMG, EY, PwC,
                Bain, Guidehouse, Chartis, Huron, BRG, Oliver Wyman, Optum Advisory.
  Pattern (b) — competitive entrant: model lab (Anthropic, OpenAI, Google, etc.) OR
                PE / banking firm (Blackstone, KKR, Apollo, Hellman, Goldman, etc.)
                combined with a services signal (AI services firm, enterprise AI
                services, AI consulting, AI advisory, implementation arm, JV).

Usage as a CLI:
    # Dry-run: report what would be promoted
    python -m consulting_intelligence.promoter --check

    # Apply: write stubs and update manifest
    python -m consulting_intelligence.promoter --apply

Usage from Python:
    from consulting_intelligence.promoter import promote_bulletins
    promoted = promote_bulletins(bulletins_dir, consulting_dir, apply=True)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional

from consulting_intelligence.dedup import (
    ConsultingEntry,
    is_duplicate,
    load_entries,
)


TRACKED_FIRMS = [
    "McKinsey", "Deloitte", "BCG", "Boston Consulting Group", "Accenture",
    "KPMG", "EY", "Ernst & Young", "PwC", "PricewaterhouseCoopers",
    "Bain", "Guidehouse", "Chartis", "Huron",
    "BRG", "Berkeley Research Group", "Oliver Wyman",
    "Optum Advisory", "EY Parthenon",
]

MODEL_LABS = [
    "Anthropic", "OpenAI", "Google DeepMind", "DeepMind",
    "Mistral", "Cohere", "Meta", "Microsoft AI",
]

PE_AND_BANKING = [
    "Blackstone", "KKR", "Apollo", "Carlyle",
    "Hellman & Friedman", "Hellman", "Bain Capital", "TPG",
    "Goldman Sachs", "Morgan Stanley", "JPMorgan",
]

# Strong signals: a single match is enough when paired with a lab or PE firm.
# These phrases unambiguously indicate the consulting/services layer.
SERVICES_SIGNALS_STRONG = [
    "AI services firm", "enterprise AI services",
    "AI consulting firm", "AI consulting",
    "AI implementation", "AI advisory",
    "implementation arm", "services joint venture",
    "services firm", "advisory firm",
    "services JV", "consulting practice",
]

# Weak signals: noisier on their own (a JV could be anything), but in combination
# with a named model lab they are a reliable indicator that the lab is moving into
# the services layer. Required to combine with a lab/PE name to fire.
SERVICES_SIGNALS_WEAK = [
    "joint venture", "JV",
    "enterprise AI", "AI services",
    "regulated industries",
]

SERVICES_SIGNALS = SERVICES_SIGNALS_STRONG + SERVICES_SIGNALS_WEAK

HEALTHCARE_DIRECT_TERMS = [
    "healthcare", "health system", "hospital", "clinical",
    "patient", "physician", "nursing", "EHR", "Epic ",
    "payer", "provider", "Medicare", "Medicaid",
    "value-based care", "VBC", "prior authorization", "revenue cycle",
]


@dataclass
class PromotionSignal:
    firm: str
    trigger: str  # "tracked_firm" | "model_lab_services" | "pe_backed_services"
    matched_terms: List[str]


def _contains_any(text: str, terms: Iterable[str]) -> List[str]:
    """Return list of terms present in text (case-insensitive whole-word-ish)."""
    found = []
    lower = text.lower()
    for term in terms:
        # Use word-boundary match to avoid false positives ("ey" in "they")
        pattern = r"\b" + re.escape(term.lower()) + r"\b"
        if re.search(pattern, lower):
            found.append(term)
    return found


def detect_signal(headline: str, body: str) -> Optional[PromotionSignal]:
    """Inspect a bulletin's text and return a promotion signal if it qualifies."""
    text = f"{headline} {body}"

    # Pattern (a): direct mention of a tracked consulting firm
    tracked = _contains_any(text, TRACKED_FIRMS)
    if tracked:
        return PromotionSignal(
            firm=tracked[0],
            trigger="tracked_firm",
            matched_terms=tracked,
        )

    # Pattern (b): competitive entrant — needs both a vendor/sponsor signal
    # AND a services signal, otherwise too noisy
    services = _contains_any(text, SERVICES_SIGNALS)
    if not services:
        return None

    labs = _contains_any(text, MODEL_LABS)
    if labs:
        return PromotionSignal(
            firm=labs[0],
            trigger="model_lab_services",
            matched_terms=labs + services,
        )

    pe = _contains_any(text, PE_AND_BANKING)
    if pe:
        # For PE-backed, the headline AI lab is usually the keystone; if one
        # is mentioned, prefer it as the firm tag, otherwise tag as the lead PE
        return PromotionSignal(
            firm=pe[0],
            trigger="pe_backed_services",
            matched_terms=pe + services,
        )

    return None


def _classify_relevance(text: str) -> str:
    """healthcare_direct if explicit healthcare terms, otherwise healthcare_adjacent."""
    if _contains_any(text, HEALTHCARE_DIRECT_TERMS):
        return "healthcare_direct"
    return "healthcare_adjacent"


def _slugify(text: str, max_len: int = 80) -> str:
    s = text.lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s.strip())
    s = re.sub(r"-+", "-", s)
    return s[:max_len].rstrip("-")


def _build_so_what(body: str) -> str:
    """First 1-2 sentences of the bulletin body, truncated to a reasonable length."""
    if not body:
        return ""
    sents = re.split(r"(?<=[.!?])\s+", body.strip())
    so_what = " ".join(sents[:2])
    if len(so_what) > 480:
        so_what = so_what[:480].rsplit(" ", 1)[0] + "..."
    return so_what


def build_entry(bulletin: dict, signal: PromotionSignal) -> dict:
    """Convert a bulletin + signal into a consulting-intelligence entry."""
    headline = bulletin.get("headline", "").strip()
    body = bulletin.get("body", "").strip()
    source_url = bulletin.get("source_url", "")
    timestamp = bulletin.get("timestamp", "")
    published_date = timestamp[:10] if timestamp else datetime.utcnow().strftime("%Y-%m-%d")

    relevance = _classify_relevance(f"{headline} {body}")

    firm_slug = _slugify(signal.firm.split()[0])
    headline_slug = _slugify(headline)
    slug = f"{firm_slug}-{headline_slug}"[:120].rstrip("-")

    return {
        "firm": signal.firm,
        "headline": headline,
        "summary": body or headline,
        "so_what": _build_so_what(body),
        "relevance": relevance,
        "source_url": source_url,
        "published_date": published_date,
        "slug": slug,
        "auto_promoted": True,
        "promotion_trigger": signal.trigger,
        "promotion_matched_terms": signal.matched_terms,
    }


def _load_bulletins(bulletins_dir: str) -> List[dict]:
    if not os.path.isdir(bulletins_dir):
        return []
    out = []
    for fname in sorted(os.listdir(bulletins_dir)):
        if not fname.endswith(".json") or fname.startswith("_"):
            continue
        path = os.path.join(bulletins_dir, fname)
        try:
            with open(path) as f:
                data = json.load(f)
            data["_path"] = path
            out.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    return out


def _append_to_manifest(consulting_dir: str, new_entry: dict) -> None:
    """Insert the new entry at the position matching its published_date (DESC)."""
    manifest_path = os.path.join(consulting_dir, "manifest.json")
    manifest = []
    if os.path.isfile(manifest_path):
        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
        except (json.JSONDecodeError, OSError):
            manifest = []

    stub = {
        "slug": new_entry["slug"],
        "headline": new_entry["headline"],
        "firm": new_entry["firm"],
        "relevance": new_entry["relevance"],
        "published_date": new_entry["published_date"],
    }

    # Insert at correct date-DESC position
    inserted = False
    for i, m in enumerate(manifest):
        if (m.get("published_date") or "") < (new_entry["published_date"] or ""):
            manifest.insert(i, stub)
            inserted = True
            break
    if not inserted:
        manifest.append(stub)

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)


def promote_bulletins(
    bulletins_dir: str,
    consulting_dir: str,
    *,
    apply: bool = False,
    similarity_threshold: float = 0.80,
    window_days: int = 30,
) -> List[dict]:
    """Scan bulletins, return list of promotions. If apply=True, write them to disk."""
    bulletins = _load_bulletins(bulletins_dir)
    existing = load_entries(consulting_dir)
    existing_urls = {e.source_url for e in existing if e.source_url}
    # Also block re-promotion of bulletins whose URL is listed as an alias on
    # an existing entry (e.g. the canonical entry cites the press release; the
    # WSJ pre-announcement is aliased so it isn't double-promoted).
    for e in existing:
        for u in e.raw.get("aliased_urls", []) if e.raw else []:
            if u:
                existing_urls.add(u)

    promotions = []
    for bulletin in bulletins:
        headline = bulletin.get("headline", "")
        body = bulletin.get("body", "")
        if not headline:
            continue

        signal = detect_signal(headline, body)
        if not signal:
            continue

        # Skip if same source URL already in consulting-intel
        src = bulletin.get("source_url", "")
        if src and src in existing_urls:
            continue

        entry = build_entry(bulletin, signal)

        # Fuzzy dedup against existing entries within firm + window
        if is_duplicate(
            entry, existing,
            threshold=similarity_threshold,
            window_days=window_days,
        ):
            continue

        promotions.append(entry)

        if apply:
            out_path = os.path.join(consulting_dir, f"{entry['slug']}.json")
            # Avoid clobbering an existing file (slug collision)
            if os.path.exists(out_path):
                stem = entry["slug"]
                suffix = entry["published_date"].replace("-", "")
                out_path = os.path.join(consulting_dir, f"{stem}-{suffix}.json")
                entry["slug"] = f"{stem}-{suffix}"
            with open(out_path, "w") as f:
                json.dump(entry, f, indent=2)
            _append_to_manifest(consulting_dir, entry)
            # Track newly written entry so subsequent bulletins in this run see it
            existing.append(
                ConsultingEntry(
                    slug=entry["slug"],
                    firm=entry["firm"],
                    headline=entry["headline"],
                    published_date=entry["published_date"],
                    source_url=entry["source_url"],
                )
            )
            if entry["source_url"]:
                existing_urls.add(entry["source_url"])

    return promotions


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Promote bulletins into consulting-intelligence stubs."
    )
    parser.add_argument(
        "--bulletins-dir",
        default="content/bulletins",
        help="Bulletin JSON directory (default: content/bulletins)",
    )
    parser.add_argument(
        "--consulting-dir",
        default="content/consulting-intelligence",
        help="Consulting intelligence output directory (default: content/consulting-intelligence)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report promotions without writing files (default)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write stub files and update manifest",
    )
    args = parser.parse_args()

    # Resolve relative paths against repo root (parent of pipeline/)
    def _resolve(p):
        if os.path.isabs(p):
            return p
        cwd = os.getcwd()
        for cand in (os.path.join(cwd, p), os.path.join(cwd, "..", p)):
            cand = os.path.normpath(cand)
            if os.path.isdir(cand):
                return cand
        return os.path.normpath(os.path.join(cwd, p))

    bulletins_dir = _resolve(args.bulletins_dir)
    consulting_dir = _resolve(args.consulting_dir)

    print(f"[promoter] Bulletins:  {bulletins_dir}")
    print(f"[promoter] Consulting: {consulting_dir}")

    promotions = promote_bulletins(
        bulletins_dir, consulting_dir, apply=args.apply
    )

    if not promotions:
        print("[promoter] No promotion candidates found.")
        return 0

    print(f"\n[promoter] {'Promoted' if args.apply else 'Would promote'} {len(promotions)} bulletin(s):\n")
    for p in promotions:
        print(f"  [{p['promotion_trigger']}] {p['firm']} | {p['relevance']}")
        print(f"    {p['headline']}")
        print(f"    {p['source_url']}")
        print()

    if not args.apply:
        print("[promoter] Dry run. Pass --apply to write stubs and update manifest.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

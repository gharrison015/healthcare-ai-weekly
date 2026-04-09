"""
Content Extractor -- Pulls content from NotebookLM AI Learning notebook.

Uses the notebooklm CLI to:
  1. Set notebook context
  2. Run `notebooklm source list --json` to get all sources
  3. Run `notebooklm source guide [source_id]` for each source to get summaries

Caches results to data/learn/.sources_cache.json.
"""

import json
import os
import subprocess
import sys
import time

SOURCES_CACHE_PATH = os.path.join("data", "learn", ".sources_cache.json")


def run_notebooklm(args, timeout=120):
    """Run a notebooklm CLI command and return stdout, or None on failure."""
    cmd = ["notebooklm"] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            print(f"  Warning: notebooklm {' '.join(args[:3])} failed: {result.stderr.strip()}")
            return None
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print(f"  Warning: notebooklm {' '.join(args[:3])} timed out after {timeout}s")
        return None
    except FileNotFoundError:
        print("Error: notebooklm CLI not found. Install it first.")
        sys.exit(1)


def set_notebook_context(notebook_id):
    """Set the active notebook for subsequent CLI commands."""
    print(f"Setting notebook context: {notebook_id}")
    output = run_notebooklm(["use", notebook_id])
    if output is None:
        print("Failed to set notebook context")
        return False
    print(f"  Context set: {output}")
    return True


def list_sources(notebook_id):
    """List all sources in the notebook via `notebooklm source list --json`."""
    print("Listing sources...")
    output = run_notebooklm(["source", "list", "-n", notebook_id, "--json"])
    if output is None:
        return []

    try:
        sources = json.loads(output)
        if isinstance(sources, dict):
            sources = sources.get("sources", [])
        print(f"  Found {len(sources)} sources")
        return sources
    except json.JSONDecodeError:
        print("  Warning: could not parse source list JSON")
        return []


def get_source_guide(source_id, notebook_id):
    """
    Get the AI-generated source guide (structured summary) for a source
    via `notebooklm source guide [source_id]`.
    """
    output = run_notebooklm(
        ["source", "guide", source_id, "-n", notebook_id, "--json"],
        timeout=60,
    )
    if output is None:
        return None

    try:
        guide = json.loads(output)
        return guide
    except json.JSONDecodeError:
        # Sometimes the output is plain text, not JSON
        return {"summary": output, "keywords": []}


def extract_all_sources(notebook_id, delay=2.0):
    """
    Extract content from all sources in the notebook.

    Returns a list of dicts:
      - source_id: the source UUID
      - title: source title
      - type: source type (youtube, web, etc.)
      - guide: AI-generated summary and keywords
    """
    sources = list_sources(notebook_id)
    if not sources:
        print("No sources found. Check notebook ID and authentication.")
        return []

    results = []
    for i, source in enumerate(sources):
        source_id = source.get("id") or source.get("source_id", "")
        title = source.get("title", "Unknown")
        source_type = source.get("type", "unknown")

        print(f"  [{i+1}/{len(sources)}] Extracting: {title[:60]}...")

        guide = get_source_guide(source_id, notebook_id)

        results.append({
            "source_id": source_id,
            "title": title,
            "type": source_type,
            "guide": guide,
        })

        # Rate-limit to avoid hammering the API
        if i < len(sources) - 1:
            time.sleep(delay)

    print(f"Extracted {len(results)} source guides")
    return results


def load_cached_sources():
    """Load previously cached source data, or return None."""
    if os.path.exists(SOURCES_CACHE_PATH):
        with open(SOURCES_CACHE_PATH) as f:
            return json.load(f)
    return None


def save_sources_cache(sources):
    """Write extracted source data to the cache file."""
    os.makedirs(os.path.dirname(SOURCES_CACHE_PATH), exist_ok=True)
    with open(SOURCES_CACHE_PATH, "w") as f:
        json.dump(sources, f, indent=2)
    print(f"  Cached source data to {SOURCES_CACHE_PATH}")


def ask_topic_summary(question, source_ids, notebook_id):
    """
    Ask a question scoped to specific sources.
    Useful for generating a topic-level summary across multiple sources.
    """
    args = ["ask", question, "--notebook", notebook_id, "--json"]
    for sid in source_ids:
        args.extend(["-s", sid])

    output = run_notebooklm(args, timeout=90)
    if output is None:
        return ""

    try:
        data = json.loads(output)
        return data.get("answer", data.get("text", output))
    except json.JSONDecodeError:
        return output


if __name__ == "__main__":
    config_path = "learning/learning_config.json"
    with open(config_path) as f:
        config = json.load(f)

    notebook_id = config["notebook_id"]
    set_notebook_context(notebook_id)
    sources = extract_all_sources(notebook_id)
    save_sources_cache(sources)

    print(json.dumps(sources, indent=2))

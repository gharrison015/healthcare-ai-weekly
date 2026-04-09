import json
import os
import re
from collections import Counter

def extract_companies_from_curated(curated):
    companies = []
    for section_name in ["top_stories", "vbc_watch", "deal_flow"]:
        for story in curated.get("sections", {}).get(section_name, []):
            headline = story.get("headline", "")
            source_title = story.get("source_article", {}).get("title", "")
            companies.append(headline)
            companies.append(source_title)
    return companies

def extract_company_names(texts):
    words = []
    for text in texts:
        tokens = re.findall(r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b', text)
        words.extend(tokens)
    stop_words = {"The", "This", "That", "What", "When", "Where", "How", "Why",
                  "New", "First", "Just", "Health", "Healthcare", "Watch", "Act", "Now"}
    return [w for w in words if w not in stop_words and len(w) > 2]

def compute_delta(history, raw_articles):
    if not history:
        return {
            "weeks_analyzed": 0,
            "recurring_companies": [],
            "recurring_themes": [],
            "new_entrants": [],
            "dropped_threads": [],
        }

    all_company_mentions = Counter()
    recent_company_mentions = Counter()

    for curated in history:
        texts = extract_companies_from_curated(curated)
        names = extract_company_names(texts)
        for name in names:
            all_company_mentions[name] += 1

    if len(history) >= 2:
        for curated in history[-2:]:
            texts = extract_companies_from_curated(curated)
            names = extract_company_names(texts)
            for name in names:
                recent_company_mentions[name] += 1

    recurring = [
        {"name": name, "weeks_appeared": count}
        for name, count in all_company_mentions.items()
        if count >= 2
    ]
    recurring.sort(key=lambda x: x["weeks_appeared"], reverse=True)

    current_texts = [a.get("title", "") for a in raw_articles]
    current_names = set(extract_company_names(current_texts))
    historical_names = set(all_company_mentions.keys())
    new_entrants = list(current_names - historical_names)

    dropped = []
    if len(history) >= 3:
        old_names = set()
        for curated in history[:-2]:
            texts = extract_companies_from_curated(curated)
            old_names.update(extract_company_names(texts))
        recent_names = set()
        for curated in history[-2:]:
            texts = extract_companies_from_curated(curated)
            recent_names.update(extract_company_names(texts))
        for name in old_names - recent_names:
            if all_company_mentions[name] >= 2:
                dropped.append({
                    "story": name,
                    "last_seen": history[-3]["issue_date"] if len(history) >= 3 else "unknown",
                    "weeks_silent": 2,
                })

    return {
        "weeks_analyzed": len(history),
        "recurring_companies": recurring[:10],
        "recurring_themes": [],
        "new_entrants": new_entrants[:10],
        "dropped_threads": dropped[:5],
    }

def load_history(curated_dir):
    history = []
    if not os.path.exists(curated_dir):
        return history
    for filename in sorted(os.listdir(curated_dir)):
        if filename.endswith(".json") and not filename.endswith("-delta.json"):
            filepath = os.path.join(curated_dir, filename)
            with open(filepath) as f:
                history.append(json.load(f))
    return history

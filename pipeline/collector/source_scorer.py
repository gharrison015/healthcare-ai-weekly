import json
import os
from collections import Counter

SCORES_PATH = "data/source_scores.json"

def load_scores(path=SCORES_PATH):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

def save_scores(scores, path=SCORES_PATH):
    with open(path, "w") as f:
        json.dump(scores, f, indent=2)

def update_scores(scores, collected_articles, curated_source_names):
    collected_counts = Counter(a["source"] for a in collected_articles)
    curated_counts = Counter(curated_source_names)

    for source_name, count in collected_counts.items():
        if source_name not in scores:
            scores[source_name] = {
                "articles_collected": 0,
                "articles_curated": 0,
                "hit_rate": 0.0,
                "weeks_tracked": 0,
            }
        entry = scores[source_name]
        entry["articles_collected"] += count
        entry["articles_curated"] += curated_counts.get(source_name, 0)
        entry["weeks_tracked"] += 1
        if entry["articles_collected"] > 0:
            entry["hit_rate"] = round(entry["articles_curated"] / entry["articles_collected"], 3)

    return scores

def get_keyword_threshold(source_name, scores):
    entry = scores.get(source_name)
    if not entry or entry["weeks_tracked"] < 8:
        return 1
    if entry["hit_rate"] < 0.10:
        return 2
    return 1

def get_flagged_sources(scores, min_weeks=12, max_hit_rate=0.05):
    flagged = []
    for source, entry in scores.items():
        if entry["weeks_tracked"] >= min_weeks and entry["hit_rate"] < max_hit_rate:
            flagged.append({"source": source, "hit_rate": entry["hit_rate"], "weeks": entry["weeks_tracked"]})
    return flagged

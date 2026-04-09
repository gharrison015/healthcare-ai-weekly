from difflib import SequenceMatcher

TIER_PRIORITY = {"core": 0, "policy": 1, "funding": 2, "tech": 3, "general_ai": 4, "catch_all": 5}

def fuzzy_title_match(title_a, title_b, threshold=0.65):
    a = title_a.lower().strip()
    b = title_b.lower().strip()
    ratio = SequenceMatcher(None, a, b).ratio()
    return ratio >= threshold

def deduplicate_articles(articles):
    seen_urls = {}
    for article in articles:
        url = article["url"]
        if url in seen_urls:
            existing = seen_urls[url]
            if TIER_PRIORITY.get(article["source_tier"], 99) < TIER_PRIORITY.get(existing["source_tier"], 99):
                seen_urls[url] = article
        else:
            seen_urls[url] = article

    unique = list(seen_urls.values())

    to_remove = set()
    for i in range(len(unique)):
        if unique[i]["id"] in to_remove:
            continue
        for j in range(i + 1, len(unique)):
            if unique[j]["id"] in to_remove:
                continue
            if fuzzy_title_match(unique[i]["title"], unique[j]["title"]):
                tier_i = TIER_PRIORITY.get(unique[i]["source_tier"], 99)
                tier_j = TIER_PRIORITY.get(unique[j]["source_tier"], 99)
                loser = unique[j]["id"] if tier_i <= tier_j else unique[i]["id"]
                to_remove.add(loser)

    return [a for a in unique if a["id"] not in to_remove]

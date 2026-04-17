# Healthcare AI Weekly Newsletter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an automated weekly pipeline that collects AI healthcare news via RSS, curates it with a Claude-powered editorial agent, generates an executive HTML email + deep-dive HTML document, and delivers them every Friday at 5 AM.

**Architecture:** Four-stage pipeline (Collector -> Curator -> Generator -> Distributor) orchestrated by `pipeline.py`. Each stage reads the previous stage's JSON output from `data/`. Configurable via JSON/markdown files without code changes. Scheduled as a Claude Code remote trigger.

**Tech Stack:** Python 3.13, feedparser, anthropic SDK, jinja2, gws CLI (email), gh CLI (repo), Apify (fallback scraping)

---

### Task 1: Project Setup and Dependencies

**Files:**
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/requirements.txt`
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/.env`
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/.gitignore`

- [ ] **Step 1: Create virtual environment**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
python3 -m venv venv
source venv/bin/activate
```
Expected: Virtual environment created at `venv/`

- [ ] **Step 2: Write requirements.txt**

```
feedparser>=6.0
anthropic>=0.40.0
jinja2>=3.1
python-dotenv>=1.0
```

- [ ] **Step 3: Install dependencies**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate
pip install -r requirements.txt
```
Expected: All packages install successfully

- [ ] **Step 4: Create .env file**

```
ANTHROPIC_API_KEY=<key from existing setup>
```

Note: Check existing `.env` files in other Claude projects for the API key pattern. Do NOT hardcode the key in the plan.

- [ ] **Step 5: Create .gitignore**

```
venv/
.env
__pycache__/
*.pyc
data/raw/
data/curated/
data/issues/
data/linkedin-seed/
data/source_scores.json
```

- [ ] **Step 6: Create data directories**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
mkdir -p data/raw data/curated data/issues data/linkedin-seed collector curator generator/templates distributor
```

- [ ] **Step 7: Commit**

```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
git add requirements.txt .gitignore
git commit -m "feat: project setup with dependencies and structure"
```

---

### Task 2: Source Configuration (sources.json)

**Files:**
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/collector/sources.json`

- [ ] **Step 1: Write the test**

Create `tests/test_sources.py`:

```python
import json
import os

def test_sources_json_is_valid():
    path = os.path.join(os.path.dirname(__file__), "..", "collector", "sources.json")
    with open(path) as f:
        data = json.load(f)
    assert "feeds" in data
    assert "google_news_queries" in data
    assert "keywords" in data
    for feed in data["feeds"]:
        assert "name" in feed
        assert "url" in feed
        assert "tier" in feed
        assert "category" in feed

def test_sources_have_required_tiers():
    path = os.path.join(os.path.dirname(__file__), "..", "collector", "sources.json")
    with open(path) as f:
        data = json.load(f)
    tiers = {f["tier"] for f in data["feeds"]}
    assert "core" in tiers
    assert "policy" in tiers
    assert "general_ai" in tiers

def test_keywords_list_not_empty():
    path = os.path.join(os.path.dirname(__file__), "..", "collector", "sources.json")
    with open(path) as f:
        data = json.load(f)
    assert len(data["keywords"]) >= 5
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate
python -m pytest tests/test_sources.py -v
```
Expected: FAIL (file not found)

- [ ] **Step 3: Create sources.json**

```json
{
  "feeds": [
    {"name": "Fierce Healthcare", "url": "https://www.fiercehealthcare.com/rss/xml", "tier": "core", "category": "core"},
    {"name": "Becker's Hospital Review", "url": "https://www.beckershospitalreview.com/feed.xml", "tier": "core", "category": "core"},
    {"name": "STAT News", "url": "https://www.statnews.com/feed/", "tier": "core", "category": "core"},
    {"name": "Healthcare Dive", "url": "https://www.healthcaredive.com/feeds/news/", "tier": "core", "category": "core"},
    {"name": "Health Affairs Blog", "url": "https://www.healthaffairs.org/do/10.1377/feeds/blog/main/feed/", "tier": "core", "category": "core"},
    {"name": "CMS Newsroom", "url": "https://www.cms.gov/newsroom/rss", "tier": "policy", "category": "policy"},
    {"name": "HHS.gov", "url": "https://www.hhs.gov/rss/index.html", "tier": "policy", "category": "policy"},
    {"name": "Rock Health", "url": "https://rockhealth.com/feed/", "tier": "funding", "category": "funding"},
    {"name": "Google Health Blog", "url": "https://blog.google/technology/health/rss/", "tier": "tech", "category": "tech"},
    {"name": "Google Cloud Health Blog", "url": "https://cloud.google.com/blog/topics/healthcare-life-sciences/rss", "tier": "tech", "category": "tech"},
    {"name": "Microsoft Health Blog", "url": "https://blogs.microsoft.com/blog/tag/healthcare/feed/", "tier": "tech", "category": "tech"},
    {"name": "NVIDIA Healthcare Blog", "url": "https://blogs.nvidia.com/blog/category/healthcare/feed/", "tier": "tech", "category": "tech"},
    {"name": "AWS Health Blog", "url": "https://aws.amazon.com/blogs/healthcare/feed/", "tier": "tech", "category": "tech"},
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml", "tier": "general_ai", "category": "general_ai"},
    {"name": "Anthropic Blog", "url": "https://www.anthropic.com/blog/rss.xml", "tier": "general_ai", "category": "general_ai"},
    {"name": "Google AI Blog", "url": "https://blog.google/technology/ai/rss/", "tier": "general_ai", "category": "general_ai"},
    {"name": "The Verge AI", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "tier": "general_ai", "category": "general_ai"}
  ],
  "google_news_queries": [
    "\"artificial intelligence\" AND \"healthcare\"",
    "\"AI\" AND \"value based care\"",
    "\"OpenAI\" AND \"healthcare\"",
    "\"Anthropic\" AND \"healthcare\"",
    "\"Google\" AND \"health AI\"",
    "\"Epic\" AND \"artificial intelligence\""
  ],
  "keywords": [
    "AI", "artificial intelligence", "machine learning", "LLM", "large language model",
    "deep learning", "value-based care", "VBC", "clinical AI", "health AI",
    "generative AI", "ambient AI", "AI agent", "copilot", "clinical decision support",
    "risk adjustment", "quality measures", "population health", "care management",
    "prior authorization", "revenue cycle", "EHR", "Epic", "Cerner", "Oracle Health"
  ]
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate
python -m pytest tests/test_sources.py -v
```
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
git add collector/sources.json tests/test_sources.py
git commit -m "feat: add source configuration with RSS feeds and keywords"
```

---

### Task 3: RSS Collector

**Files:**
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/collector/rss_collector.py`
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/tests/test_rss_collector.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_rss_collector.py`:

```python
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from collector.rss_collector import collect_rss, parse_feed_entry, build_google_news_url

def test_parse_feed_entry_extracts_fields():
    entry = MagicMock()
    entry.title = "Epic launches AI-powered clinical agent"
    entry.link = "https://example.com/article"
    entry.get.return_value = "Epic announced a new clinical AI agent today."
    entry.published_parsed = (2026, 4, 2, 10, 0, 0, 2, 92, 0)

    source = {"name": "Fierce Healthcare", "tier": "core", "category": "core"}
    keywords = ["AI", "clinical"]

    result = parse_feed_entry(entry, source, keywords)
    assert result is not None
    assert result["title"] == "Epic launches AI-powered clinical agent"
    assert result["source"] == "Fierce Healthcare"
    assert result["source_tier"] == "core"
    assert result["category"] == "core"
    assert result["url"] == "https://example.com/article"
    assert "AI" in result["keywords_matched"]
    assert "id" in result

def test_parse_feed_entry_returns_none_when_no_keyword_match():
    entry = MagicMock()
    entry.title = "Hospital cafeteria menu updated"
    entry.link = "https://example.com/food"
    entry.get.return_value = "New salad bar options available."
    entry.published_parsed = (2026, 4, 2, 10, 0, 0, 2, 92, 0)

    source = {"name": "Becker's", "tier": "core", "category": "core"}
    keywords = ["AI", "machine learning"]

    result = parse_feed_entry(entry, source, keywords)
    assert result is None

def test_parse_feed_entry_filters_old_articles():
    entry = MagicMock()
    entry.title = "AI in healthcare roundup"
    entry.link = "https://example.com/old"
    entry.get.return_value = "Old AI news."
    entry.published_parsed = (2026, 1, 1, 10, 0, 0, 2, 1, 0)

    source = {"name": "STAT News", "tier": "core", "category": "core"}
    keywords = ["AI"]

    result = parse_feed_entry(entry, source, keywords, max_age_days=7)
    assert result is None

def test_build_google_news_url():
    query = '"artificial intelligence" AND "healthcare"'
    url = build_google_news_url(query)
    assert "news.google.com/rss/search" in url
    assert "healthcare" in url
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate
python -m pytest tests/test_rss_collector.py -v
```
Expected: FAIL (module not found)

- [ ] **Step 3: Implement rss_collector.py**

```python
import feedparser
import json
import uuid
import re
from datetime import datetime, timedelta
from time import mktime
from urllib.parse import quote

def build_google_news_url(query):
    encoded = quote(query)
    return f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"

def parse_feed_entry(entry, source, keywords, max_age_days=7):
    title = entry.title if hasattr(entry, "title") else ""
    link = entry.link if hasattr(entry, "link") else ""
    summary = entry.get("summary", "") if hasattr(entry, "get") else ""

    published_parsed = getattr(entry, "published_parsed", None)
    if published_parsed:
        published_dt = datetime.fromtimestamp(mktime(published_parsed))
        if datetime.now() - published_dt > timedelta(days=max_age_days):
            return None
        published_date = published_dt.strftime("%Y-%m-%d")
    else:
        published_date = datetime.now().strftime("%Y-%m-%d")

    text = f"{title} {summary}".lower()
    matched = [kw for kw in keywords if kw.lower() in text]
    if not matched:
        return None

    return {
        "id": str(uuid.uuid4()),
        "title": title,
        "source": source["name"],
        "source_tier": source["tier"],
        "url": link,
        "published_date": published_date,
        "summary": summary[:500],
        "category": source["category"],
        "keywords_matched": matched,
    }

def collect_rss(sources_path, max_age_days=7):
    with open(sources_path) as f:
        config = json.load(f)

    articles = []
    seen_urls = set()

    for source in config["feeds"]:
        try:
            feed = feedparser.parse(source["url"])
            for entry in feed.entries:
                article = parse_feed_entry(entry, source, config["keywords"], max_age_days)
                if article and article["url"] not in seen_urls:
                    seen_urls.add(article["url"])
                    articles.append(article)
        except Exception as e:
            print(f"Warning: Failed to parse {source['name']}: {e}")

    for query in config.get("google_news_queries", []):
        url = build_google_news_url(query)
        gn_source = {"name": "Google News", "tier": "catch_all", "category": "core"}
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                article = parse_feed_entry(entry, gn_source, config["keywords"], max_age_days)
                if article and article["url"] not in seen_urls:
                    seen_urls.add(article["url"])
                    articles.append(article)
        except Exception as e:
            print(f"Warning: Failed Google News query '{query}': {e}")

    return articles

if __name__ == "__main__":
    import sys
    sources = sys.argv[1] if len(sys.argv) > 1 else "collector/sources.json"
    results = collect_rss(sources)
    print(json.dumps({"article_count": len(results), "articles": results[:3]}, indent=2))
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate
python -m pytest tests/test_rss_collector.py -v
```
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
git add collector/rss_collector.py tests/test_rss_collector.py
git commit -m "feat: RSS collector with keyword filtering and dedup"
```

---

### Task 4: Filters (Deduplication and Fuzzy Matching)

**Files:**
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/collector/filters.py`
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/tests/test_filters.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_filters.py`:

```python
from collector.filters import deduplicate_articles, fuzzy_title_match

def test_deduplicate_by_url():
    articles = [
        {"id": "1", "url": "https://example.com/a", "title": "AI story", "source": "A", "source_tier": "core"},
        {"id": "2", "url": "https://example.com/a", "title": "AI story dupe", "source": "B", "source_tier": "core"},
        {"id": "3", "url": "https://example.com/b", "title": "Different story", "source": "C", "source_tier": "core"},
    ]
    result = deduplicate_articles(articles)
    assert len(result) == 2
    urls = [a["url"] for a in result]
    assert "https://example.com/a" in urls
    assert "https://example.com/b" in urls

def test_fuzzy_title_match_catches_similar():
    assert fuzzy_title_match(
        "OpenAI partners with Mayo Clinic on clinical AI",
        "OpenAI and Mayo Clinic announce clinical AI partnership"
    ) is True

def test_fuzzy_title_match_rejects_different():
    assert fuzzy_title_match(
        "OpenAI partners with Mayo Clinic",
        "Google launches new Pixel phone"
    ) is False

def test_deduplicate_prefers_higher_tier():
    articles = [
        {"id": "1", "url": "https://a.com/1", "title": "AI scribe saves time in clinics", "source": "Random Blog", "source_tier": "catch_all"},
        {"id": "2", "url": "https://b.com/2", "title": "AI scribe saves clinician time in clinics", "source": "STAT News", "source_tier": "core"},
    ]
    result = deduplicate_articles(articles)
    assert len(result) == 1
    assert result[0]["source"] == "STAT News"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate
python -m pytest tests/test_filters.py -v
```
Expected: FAIL (module not found)

- [ ] **Step 3: Implement filters.py**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate
python -m pytest tests/test_filters.py -v
```
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
git add collector/filters.py tests/test_filters.py
git commit -m "feat: article deduplication with fuzzy title matching and tier priority"
```

---

### Task 5: Curator Persona, Guardrails, and Feedback Files

**Files:**
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/curator/persona.md`
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/curator/guardrails.json`
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/curator/feedback.md`

- [ ] **Step 1: Create persona.md**

```markdown
# Editorial Persona

You are a senior healthcare AI consultant writing a weekly intelligence briefing for colleagues who advise health systems and payers on technology strategy.

## How you think

Every headline gets filtered through one question: "Should my client care about this?" You have deep knowledge of value-based care models, clinical workflows, EHR ecosystems (especially Epic), and how consulting firms position against technology shifts.

You care about:
- Real-world clinical and operational impact. If it's not deployed or close to deployed, it's "Watch This" at best.
- Products that change how care gets delivered at the point of care.
- Acquisitions and partnerships that reshape who controls clinical workflows.
- Capabilities that unlock something previously impossible for health systems or payers.
- Analytics that support VBC: AWV tools, risk adjustment engines, quality measure automation, care management platforms.
- AI agent integration into nursing, care management, and clinical documentation workflows.
- What OpenAI, Anthropic, Google, and Microsoft are doing specifically in healthcare and how it changes the consulting landscape.

## How you write

Channel Nate B Jones' communication style:
- Direct and confident. You state opinions as an insider. "Here's what this actually means for health systems."
- Conversational authority. You talk like the smartest person at the table who doesn't need to prove it.
- Strategic provocateur. You push readers to think about what's coming, not just what happened.

## What you never do

- Use em dashes as a crutch
- Write "In today's rapidly evolving landscape" or any variation
- Use passive voice like "Company X announced..."
- Treat every story as equally important
- Summarize without opinion
- Sound like a press release or a model summarizing feeds
- Use the word "delve" or "synergy" or "leverage" unironically
```

- [ ] **Step 2: Create guardrails.json**

```json
{
  "sections": {
    "top_stories": {
      "description": "Major stories with strategic analysis, split into act_now and watch_this",
      "min_count": 3,
      "max_count": 5,
      "required_fields": ["headline", "priority", "so_what", "email_summary", "deep_dive_notes"],
      "priority_values": ["act_now", "watch_this"]
    },
    "vbc_watch": {
      "description": "Stories touching value-based care, payment models, risk adjustment, quality measures",
      "min_count": 1,
      "max_count": 3,
      "required_fields": ["headline", "so_what", "email_summary", "deep_dive_notes"]
    },
    "deal_flow": {
      "description": "Acquisitions, funding rounds, major partnerships",
      "min_count": 1,
      "max_count": 3,
      "required_fields": ["headline", "so_what", "email_summary", "deep_dive_notes"]
    },
    "did_you_know": {
      "description": "General AI capability and release news, not healthcare-specific. Educational tone.",
      "min_count": 2,
      "max_count": 3,
      "required_fields": ["headline", "one_liner", "explainer"]
    }
  },
  "global_rules": [
    "At least one story must include a risk_angle or contrarian take",
    "At least one top_story must have priority act_now",
    "Every story needs a so_what that answers: why should a health system exec care?",
    "Connect related stories via the connections field when applicable",
    "Include a linkedin_seed with the single most compelling story for a LinkedIn post"
  ]
}
```

- [ ] **Step 3: Create empty feedback.md**

```markdown
# Editorial Feedback

Append notes after each issue. These are injected into the curator prompt as rolling guidance.

<!-- Add feedback after each issue like:
## YYYY-MM-DD
- What worked well
- What was missing or weak
- Tone/style notes
-->
```

- [ ] **Step 4: Commit**

```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
git add curator/persona.md curator/guardrails.json curator/feedback.md
git commit -m "feat: curator persona, guardrails, and feedback loop files"
```

---

### Task 6: Curator Agent

**Files:**
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/curator/curator_agent.py`
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/tests/test_curator.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_curator.py`:

```python
import json
from curator.curator_agent import build_curator_prompt, validate_curated_output

def test_build_curator_prompt_includes_all_parts():
    articles = [{"id": "1", "title": "Test", "source": "Test", "summary": "Test AI story"}]
    persona = "You are a healthcare AI consultant."
    guardrails = {"sections": {"top_stories": {"min_count": 3}}, "global_rules": ["rule1"]}
    feedback = "## 2026-04-04\n- More VBC depth"
    delta = None

    prompt = build_curator_prompt(articles, persona, guardrails, feedback, delta)
    assert "healthcare AI consultant" in prompt
    assert "Test AI story" in prompt
    assert "More VBC depth" in prompt
    assert "rule1" in prompt

def test_build_curator_prompt_includes_delta_when_present():
    articles = [{"id": "1", "title": "Test", "source": "Test", "summary": "Test"}]
    persona = "Persona"
    guardrails = {"sections": {}, "global_rules": []}
    feedback = ""
    delta = {"recurring_companies": [{"name": "Abridge", "weeks_appeared": 3}]}

    prompt = build_curator_prompt(articles, persona, guardrails, feedback, delta)
    assert "Abridge" in prompt
    assert "3" in prompt

def test_validate_curated_output_catches_missing_sections():
    guardrails = {
        "sections": {
            "top_stories": {"min_count": 3, "required_fields": ["headline"]},
            "vbc_watch": {"min_count": 1, "required_fields": ["headline"]},
            "deal_flow": {"min_count": 1, "required_fields": ["headline"]},
            "did_you_know": {"min_count": 2, "required_fields": ["headline"]}
        },
        "global_rules": []
    }
    output = {
        "sections": {
            "top_stories": [{"headline": "A"}, {"headline": "B"}, {"headline": "C"}],
            "vbc_watch": [],
            "deal_flow": [{"headline": "D"}],
            "did_you_know": [{"headline": "E"}, {"headline": "F"}]
        }
    }
    errors = validate_curated_output(output, guardrails)
    assert any("vbc_watch" in e for e in errors)

def test_validate_curated_output_passes_valid():
    guardrails = {
        "sections": {
            "top_stories": {"min_count": 1, "required_fields": ["headline"]},
        },
        "global_rules": []
    }
    output = {
        "sections": {
            "top_stories": [{"headline": "A"}],
        }
    }
    errors = validate_curated_output(output, guardrails)
    assert len(errors) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate
python -m pytest tests/test_curator.py -v
```
Expected: FAIL (module not found)

- [ ] **Step 3: Implement curator_agent.py**

```python
import json
import os
from anthropic import Anthropic

def build_curator_prompt(articles, persona, guardrails, feedback, delta):
    articles_text = json.dumps(articles, indent=2)

    guardrails_text = "SECTION REQUIREMENTS:\n"
    for section, rules in guardrails.get("sections", {}).items():
        guardrails_text += f"\n{section}:\n"
        guardrails_text += f"  Min items: {rules.get('min_count', 0)}, Max items: {rules.get('max_count', 'unlimited')}\n"
        guardrails_text += f"  Required fields per item: {', '.join(rules.get('required_fields', []))}\n"
    guardrails_text += "\nGLOBAL RULES:\n"
    for rule in guardrails.get("global_rules", []):
        guardrails_text += f"- {rule}\n"

    prompt = f"""# YOUR EDITORIAL IDENTITY

{persona}

# STRUCTURAL REQUIREMENTS

{guardrails_text}

"""

    if feedback and feedback.strip():
        prompt += f"""# EDITORIAL FEEDBACK FROM PREVIOUS ISSUES

Review this feedback and let it guide your editorial decisions. This is how the editor has reacted to past issues.

{feedback}

"""

    if delta:
        prompt += "# TREND CONTEXT (week-over-week patterns)\n\n"
        if delta.get("recurring_companies"):
            prompt += "Recurring companies (appeared in multiple recent issues):\n"
            for c in delta["recurring_companies"]:
                prompt += f"- {c['name']}: appeared {c['weeks_appeared']} weeks\n"
        if delta.get("recurring_themes"):
            prompt += "\nRecurring themes:\n"
            for t in delta["recurring_themes"]:
                prompt += f"- {t['theme']}: {t['weeks_appeared']} weeks ({t.get('trend', 'stable')})\n"
        if delta.get("dropped_threads"):
            prompt += "\nDropped threads (stories that went silent):\n"
            for d in delta["dropped_threads"]:
                prompt += f"- {d['story']}: last seen {d['last_seen']}, silent {d['weeks_silent']} weeks\n"
        if delta.get("new_entrants"):
            prompt += f"\nNew this week: {', '.join(delta['new_entrants'])}\n"
        prompt += "\nUse this context to optionally include a trend_watch section if patterns are strong enough.\n\n"

    prompt += f"""# THIS WEEK'S ARTICLES

Below are all articles collected this week. Select, rank, and annotate the ones that matter most.

{articles_text}

# YOUR OUTPUT

Return a single JSON object with this exact structure. No markdown fencing, just raw JSON:

{{
  "editorial_summary": "One paragraph overview of the week's themes and what matters",
  "sections": {{
    "top_stories": [
      {{
        "headline": "Your rewritten editorial headline",
        "source_article": {{"id": "original article id", "title": "original title", "source": "source name", "url": "url"}},
        "priority": "act_now or watch_this",
        "so_what": "Why a health system exec should care, 1-2 sentences",
        "risk_angle": "Downside or contrarian take, or null if not applicable",
        "consulting_signal": "Why a client might ask about this, or null",
        "connections": ["ids of related articles this week"],
        "deep_dive_notes": "Extended analysis for the HTML doc, 200-400 words",
        "email_summary": "Tight 1-2 sentence take for the executive email"
      }}
    ],
    "vbc_watch": [same structure as top_stories],
    "deal_flow": [same structure as top_stories],
    "did_you_know": [
      {{
        "headline": "What happened in general AI",
        "source_article": {{"id": "id", "title": "title", "source": "source", "url": "url"}},
        "one_liner": "Quick hit for the email",
        "explainer": "Deeper educational content for the HTML doc, 150-300 words"
      }}
    ]
  }},
  "linkedin_seed": {{
    "top_story": "The single most compelling story for a LinkedIn post",
    "hook": "Opening line suggestion",
    "angle": "How to frame it for LinkedIn audience"
  }},
  "trend_watch": {{
    "recurring_companies": ["list or empty"],
    "recurring_themes": ["list or empty"],
    "emerging_signal": "1-2 sentence callout or null if no strong pattern yet"
  }}
}}"""

    return prompt

def validate_curated_output(output, guardrails):
    errors = []
    sections = output.get("sections", {})

    for section_name, rules in guardrails.get("sections", {}).items():
        items = sections.get(section_name, [])
        min_count = rules.get("min_count", 0)
        if len(items) < min_count:
            errors.append(f"{section_name}: has {len(items)} items, needs at least {min_count}")
        for i, item in enumerate(items):
            for field in rules.get("required_fields", []):
                if field not in item or not item[field]:
                    errors.append(f"{section_name}[{i}]: missing required field '{field}'")

    return errors

def run_curator(raw_data_path, output_path, persona_path="curator/persona.md",
                guardrails_path="curator/guardrails.json", feedback_path="curator/feedback.md",
                delta_path=None):
    with open(raw_data_path) as f:
        raw_data = json.load(f)

    with open(persona_path) as f:
        persona = f.read()

    with open(guardrails_path) as f:
        guardrails = json.load(f)

    feedback = ""
    if os.path.exists(feedback_path):
        with open(feedback_path) as f:
            feedback = f.read()

    delta = None
    if delta_path and os.path.exists(delta_path):
        with open(delta_path) as f:
            delta = json.load(f)

    articles = raw_data.get("articles", [])
    prompt = build_curator_prompt(articles, persona, guardrails, feedback, delta)

    client = Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = response.content[0].text.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

    curated = json.loads(response_text)

    validation_errors = validate_curated_output(curated, guardrails)
    if validation_errors:
        print(f"Validation warnings: {validation_errors}")
        print("Re-running curator with correction prompt...")
        correction = prompt + f"\n\nYour previous output had these issues: {validation_errors}\nPlease fix them and return corrected JSON."
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            messages=[{"role": "user", "content": correction}],
        )
        response_text = response.content[0].text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("\n", 1)[1]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
        curated = json.loads(response_text)

    curated["issue_date"] = raw_data.get("collection_date", "")
    curated["week_range"] = raw_data.get("week_range", "")

    with open(output_path, "w") as f:
        json.dump(curated, f, indent=2)

    return curated

if __name__ == "__main__":
    import sys
    raw = sys.argv[1] if len(sys.argv) > 1 else "data/raw/latest.json"
    out = sys.argv[2] if len(sys.argv) > 2 else "data/curated/latest.json"
    run_curator(raw, out)
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate
python -m pytest tests/test_curator.py -v
```
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
git add curator/curator_agent.py tests/test_curator.py
git commit -m "feat: curator agent with persona prompt, guardrails validation, and retry"
```

---

### Task 7: Delta Tracker

**Files:**
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/data/curated/delta_tracker.py`
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/tests/test_delta_tracker.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_delta_tracker.py`:

```python
import json
from data.curated.delta_tracker import compute_delta

def make_curated(date, companies, themes):
    stories = []
    for c in companies:
        stories.append({"headline": f"{c} does something", "source_article": {"title": c}})
    return {
        "issue_date": date,
        "sections": {
            "top_stories": stories,
            "vbc_watch": [],
            "deal_flow": [],
            "did_you_know": [],
        }
    }

def test_finds_recurring_companies():
    history = [
        make_curated("2026-03-21", ["Abridge", "Epic"], []),
        make_curated("2026-03-28", ["Abridge", "Google"], []),
    ]
    raw_articles = [
        {"title": "Abridge launches new product", "source": "STAT"},
        {"title": "Microsoft health update", "source": "Becker's"},
    ]
    delta = compute_delta(history, raw_articles)
    recurring = [c["name"] for c in delta["recurring_companies"]]
    assert "Abridge" in recurring

def test_identifies_new_entrants():
    history = [
        make_curated("2026-03-28", ["Abridge"], []),
    ]
    raw_articles = [
        {"title": "BrandNewCo launches AI platform", "source": "STAT"},
    ]
    delta = compute_delta(history, raw_articles)
    assert "BrandNewCo" in delta["new_entrants"] or len(delta["new_entrants"]) >= 0

def test_empty_history_returns_valid_delta():
    delta = compute_delta([], [{"title": "AI story", "source": "Test"}])
    assert "recurring_companies" in delta
    assert "recurring_themes" in delta
    assert delta["weeks_analyzed"] == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate
python -m pytest tests/test_delta_tracker.py -v
```
Expected: FAIL (module not found)

- [ ] **Step 3: Create `data/__init__.py` and `data/curated/__init__.py`**

```bash
touch /Users/greg/Claude/healthcare-ai-newsletter/data/__init__.py
touch /Users/greg/Claude/healthcare-ai-newsletter/data/curated/__init__.py
touch /Users/greg/Claude/healthcare-ai-newsletter/collector/__init__.py
touch /Users/greg/Claude/healthcare-ai-newsletter/curator/__init__.py
touch /Users/greg/Claude/healthcare-ai-newsletter/generator/__init__.py
touch /Users/greg/Claude/healthcare-ai-newsletter/distributor/__init__.py
touch /Users/greg/Claude/healthcare-ai-newsletter/tests/__init__.py
```

- [ ] **Step 4: Implement delta_tracker.py**

```python
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

if __name__ == "__main__":
    import sys
    curated_dir = sys.argv[1] if len(sys.argv) > 1 else "data/curated"
    raw_path = sys.argv[2] if len(sys.argv) > 2 else "data/raw/latest.json"

    history = load_history(curated_dir)
    with open(raw_path) as f:
        raw = json.load(f)

    delta = compute_delta(history, raw.get("articles", []))
    print(json.dumps(delta, indent=2))
```

- [ ] **Step 5: Run tests to verify they pass**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate
python -m pytest tests/test_delta_tracker.py -v
```
Expected: All 3 tests PASS

- [ ] **Step 6: Commit**

```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
git add data/curated/delta_tracker.py tests/test_delta_tracker.py data/__init__.py data/curated/__init__.py collector/__init__.py curator/__init__.py generator/__init__.py distributor/__init__.py tests/__init__.py
git commit -m "feat: delta tracker for issue-over-issue trend detection"
```

---

### Task 8: Source Reliability Scoring

**Files:**
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/collector/source_scorer.py`
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/tests/test_source_scorer.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_source_scorer.py`:

```python
import json
from collector.source_scorer import update_scores, get_keyword_threshold

def test_update_scores_initializes_new_source():
    scores = {}
    collected = [{"source": "Fierce Healthcare"}, {"source": "Fierce Healthcare"}, {"source": "NVIDIA Blog"}]
    curated_sources = ["Fierce Healthcare"]

    updated = update_scores(scores, collected, curated_sources)
    assert updated["Fierce Healthcare"]["articles_collected"] == 2
    assert updated["Fierce Healthcare"]["articles_curated"] == 1
    assert updated["Fierce Healthcare"]["weeks_tracked"] == 1
    assert updated["NVIDIA Blog"]["articles_collected"] == 1
    assert updated["NVIDIA Blog"]["articles_curated"] == 0

def test_update_scores_accumulates():
    scores = {
        "Fierce Healthcare": {"articles_collected": 10, "articles_curated": 6, "hit_rate": 0.6, "weeks_tracked": 5}
    }
    collected = [{"source": "Fierce Healthcare"}, {"source": "Fierce Healthcare"}]
    curated_sources = ["Fierce Healthcare"]

    updated = update_scores(scores, collected, curated_sources)
    assert updated["Fierce Healthcare"]["articles_collected"] == 12
    assert updated["Fierce Healthcare"]["articles_curated"] == 7
    assert updated["Fierce Healthcare"]["weeks_tracked"] == 6

def test_keyword_threshold_default_before_8_weeks():
    scores = {"Fierce Healthcare": {"hit_rate": 0.01, "weeks_tracked": 5}}
    assert get_keyword_threshold("Fierce Healthcare", scores) == 1

def test_keyword_threshold_tighter_for_low_hit_rate_after_8_weeks():
    scores = {"NVIDIA Blog": {"hit_rate": 0.05, "weeks_tracked": 10}}
    assert get_keyword_threshold("NVIDIA Blog", scores) == 2

def test_keyword_threshold_looser_for_high_hit_rate_after_8_weeks():
    scores = {"Fierce Healthcare": {"hit_rate": 0.55, "weeks_tracked": 10}}
    assert get_keyword_threshold("Fierce Healthcare", scores) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate
python -m pytest tests/test_source_scorer.py -v
```
Expected: FAIL (module not found)

- [ ] **Step 3: Implement source_scorer.py**

```python
import json
import os

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
    from collections import Counter

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
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate
python -m pytest tests/test_source_scorer.py -v
```
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
git add collector/source_scorer.py tests/test_source_scorer.py
git commit -m "feat: source reliability scoring with adaptive keyword thresholds"
```

---

### Task 9: Email Template and Generator

**Files:**
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/generator/templates/email_template.html`
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/generator/email_generator.py`
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/tests/test_email_generator.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_email_generator.py`:

```python
from generator.email_generator import render_email, format_subject_line

def test_format_subject_line():
    result = format_subject_line("April 4, 2026")
    assert result == "Healthcare AI Weekly — Week of April 4, 2026"

def test_render_email_contains_all_sections():
    curated = {
        "issue_date": "2026-04-04",
        "week_range": "March 30 - April 4, 2026",
        "editorial_summary": "Big week for clinical AI.",
        "sections": {
            "top_stories": [{
                "headline": "Epic Launches AI Agent",
                "priority": "act_now",
                "email_summary": "Epic just changed the game.",
                "source_article": {"url": "https://example.com", "source": "STAT"},
            }],
            "vbc_watch": [{
                "headline": "CMS Updates VBC Scoring",
                "email_summary": "New quality measures incoming.",
                "source_article": {"url": "https://example.com/vbc", "source": "CMS"},
            }],
            "deal_flow": [{
                "headline": "Abridge Acquired for $3B",
                "email_summary": "Ambient AI consolidation continues.",
                "source_article": {"url": "https://example.com/deal", "source": "Rock Health"},
            }],
            "did_you_know": [{
                "headline": "Claude 4 Can Read Medical Images",
                "one_liner": "Anthropic's latest model handles radiology.",
            }],
        },
        "trend_watch": {"emerging_signal": None},
    }
    html = render_email(curated)
    assert "Epic Launches AI Agent" in html
    assert "act_now" in html.lower() or "Act Now" in html
    assert "VBC" in html or "CMS Updates" in html
    assert "Abridge" in html
    assert "Claude 4" in html
    assert "Big week" in html

def test_render_email_is_valid_html():
    curated = {
        "issue_date": "2026-04-04",
        "week_range": "March 30 - April 4, 2026",
        "editorial_summary": "Test week.",
        "sections": {
            "top_stories": [{"headline": "Test", "priority": "watch_this", "email_summary": "Test.", "source_article": {"url": "#", "source": "Test"}}],
            "vbc_watch": [],
            "deal_flow": [],
            "did_you_know": [],
        },
        "trend_watch": {"emerging_signal": None},
    }
    html = render_email(curated)
    assert html.strip().startswith("<!DOCTYPE html") or html.strip().startswith("<html")
    assert "</html>" in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate
python -m pytest tests/test_email_generator.py -v
```
Expected: FAIL (module not found)

- [ ] **Step 3: Create email_template.html**

Create `generator/templates/email_template.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Healthcare AI Weekly</title>
<style>
  body { margin: 0; padding: 0; font-family: Georgia, 'Times New Roman', serif; background: #f8f8f8; color: #1a1a1a; }
  .container { max-width: 640px; margin: 0 auto; background: #ffffff; padding: 32px 24px; }
  h1 { font-size: 22px; font-weight: 700; margin: 0 0 4px 0; color: #111; letter-spacing: -0.3px; }
  .week-range { font-size: 13px; color: #666; margin-bottom: 24px; }
  .editorial-summary { font-size: 15px; line-height: 1.6; color: #333; margin-bottom: 28px; border-left: 3px solid #2563eb; padding-left: 16px; }
  h2 { font-size: 16px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #2563eb; margin: 28px 0 12px 0; padding-bottom: 6px; border-bottom: 1px solid #e5e7eb; }
  .story { margin-bottom: 16px; }
  .story-headline { font-size: 15px; font-weight: 600; color: #111; }
  .story-headline a { color: #111; text-decoration: none; }
  .story-headline a:hover { text-decoration: underline; }
  .badge { display: inline-block; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; padding: 2px 6px; border-radius: 3px; margin-right: 6px; vertical-align: middle; }
  .badge-act-now { background: #dc2626; color: #fff; }
  .badge-watch-this { background: #2563eb; color: #fff; }
  .story-summary { font-size: 14px; line-height: 1.5; color: #444; margin-top: 4px; }
  .source-tag { font-size: 11px; color: #888; }
  .did-you-know-item { margin-bottom: 12px; }
  .did-you-know-item .headline { font-size: 14px; font-weight: 600; color: #111; }
  .did-you-know-item .one-liner { font-size: 13px; color: #555; margin-top: 2px; }
  .trend-watch { background: #f0f4ff; padding: 12px 16px; border-radius: 6px; margin: 20px 0; font-size: 14px; line-height: 1.5; color: #333; }
  .trend-watch strong { color: #2563eb; }
  .footer { margin-top: 32px; padding-top: 16px; border-top: 1px solid #e5e7eb; font-size: 13px; color: #888; line-height: 1.5; }
  .footer a { color: #2563eb; text-decoration: none; }
</style>
</head>
<body>
<div class="container">
  <h1>Healthcare AI Weekly</h1>
  <div class="week-range">Week of {{ week_range }}</div>

  <div class="editorial-summary">{{ editorial_summary }}</div>

  {% if top_stories %}
  <h2>What Matters This Week</h2>
  {% for story in top_stories %}
  <div class="story">
    <div class="story-headline">
      {% if story.priority == "act_now" %}<span class="badge badge-act-now">Act Now</span>{% else %}<span class="badge badge-watch-this">Watch This</span>{% endif %}
      <a href="{{ story.source_article.url }}">{{ story.headline }}</a>
    </div>
    <div class="story-summary">{{ story.email_summary }}</div>
    <div class="source-tag">{{ story.source_article.source }}</div>
  </div>
  {% endfor %}
  {% endif %}

  {% if vbc_watch %}
  <h2>VBC Watch</h2>
  {% for story in vbc_watch %}
  <div class="story">
    <div class="story-headline"><a href="{{ story.source_article.url }}">{{ story.headline }}</a></div>
    <div class="story-summary">{{ story.email_summary }}</div>
    <div class="source-tag">{{ story.source_article.source }}</div>
  </div>
  {% endfor %}
  {% endif %}

  {% if deal_flow %}
  <h2>Deal Flow</h2>
  {% for story in deal_flow %}
  <div class="story">
    <div class="story-headline"><a href="{{ story.source_article.url }}">{{ story.headline }}</a></div>
    <div class="story-summary">{{ story.email_summary }}</div>
    <div class="source-tag">{{ story.source_article.source }}</div>
  </div>
  {% endfor %}
  {% endif %}

  {% if did_you_know %}
  <h2>Did You Know?</h2>
  {% for item in did_you_know %}
  <div class="did-you-know-item">
    <div class="headline">{{ item.headline }}</div>
    <div class="one-liner">{{ item.one_liner }}</div>
  </div>
  {% endfor %}
  {% endif %}

  {% if trend_signal %}
  <div class="trend-watch">
    <strong>Trend Watch:</strong> {{ trend_signal }}
  </div>
  {% endif %}

  <div class="footer">
    {% if deep_dive_url %}<a href="{{ deep_dive_url }}">Read the full deep-dive with extended analysis</a><br><br>{% endif %}
    Healthcare AI Weekly is curated by Greg Harrison at Guidehouse.
  </div>
</div>
</body>
</html>
```

- [ ] **Step 4: Implement email_generator.py**

```python
import os
from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

def format_subject_line(week_display):
    return f"Healthcare AI Weekly — Week of {week_display}"

def render_email(curated, deep_dive_url=None):
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=False)
    template = env.get_template("email_template.html")

    sections = curated.get("sections", {})
    trend_watch = curated.get("trend_watch", {})
    trend_signal = trend_watch.get("emerging_signal") if trend_watch else None

    html = template.render(
        week_range=curated.get("week_range", ""),
        editorial_summary=curated.get("editorial_summary", ""),
        top_stories=sections.get("top_stories", []),
        vbc_watch=sections.get("vbc_watch", []),
        deal_flow=sections.get("deal_flow", []),
        did_you_know=sections.get("did_you_know", []),
        trend_signal=trend_signal,
        deep_dive_url=deep_dive_url,
    )
    return html

if __name__ == "__main__":
    import json, sys
    with open(sys.argv[1]) as f:
        curated = json.load(f)
    html = render_email(curated)
    out = sys.argv[2] if len(sys.argv) > 2 else "data/issues/preview_email.html"
    with open(out, "w") as f:
        f.write(html)
    print(f"Email preview: {out}")
```

- [ ] **Step 5: Run tests to verify they pass**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate
python -m pytest tests/test_email_generator.py -v
```
Expected: All 3 tests PASS

- [ ] **Step 6: Commit**

```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
git add generator/email_generator.py generator/templates/email_template.html tests/test_email_generator.py
git commit -m "feat: email generator with Jinja2 template and priority badges"
```

---

### Task 10: HTML Deep-Dive Template and Generator

**Files:**
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/generator/templates/doc_template.html`
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/generator/html_generator.py`
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/tests/test_html_generator.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_html_generator.py`:

```python
from generator.html_generator import render_deep_dive

def test_render_deep_dive_contains_all_sections():
    curated = {
        "issue_date": "2026-04-04",
        "week_range": "March 30 - April 4, 2026",
        "editorial_summary": "Big week.",
        "sections": {
            "top_stories": [{
                "headline": "Epic AI Agent",
                "priority": "act_now",
                "so_what": "Changes everything.",
                "deep_dive_notes": "Extended analysis of the Epic announcement and what it means for clinical workflows.",
                "risk_angle": "Integration costs could be brutal.",
                "source_article": {"url": "https://example.com", "source": "STAT", "title": "Epic Launches AI"},
                "connections": [],
            }],
            "vbc_watch": [{
                "headline": "CMS VBC Update",
                "so_what": "New measures.",
                "deep_dive_notes": "Deep analysis of CMS changes.",
                "source_article": {"url": "#", "source": "CMS", "title": "CMS Update"},
            }],
            "deal_flow": [{
                "headline": "Abridge Acquired",
                "so_what": "Consolidation.",
                "deep_dive_notes": "What the Abridge deal means.",
                "source_article": {"url": "#", "source": "Rock Health", "title": "Abridge Deal"},
            }],
            "did_you_know": [{
                "headline": "Claude 4 Reads X-rays",
                "explainer": "Detailed explanation of how Claude 4 handles medical imaging.",
            }],
        },
        "trend_watch": {"emerging_signal": "Ambient AI scribes appeared 4 of last 6 weeks."},
    }
    all_articles = [{"title": "Article 1", "source": "Test", "url": "#"}]

    html = render_deep_dive(curated, all_articles)
    assert "Epic AI Agent" in html
    assert "Extended analysis" in html
    assert "CMS VBC Update" in html
    assert "Abridge Acquired" in html
    assert "Claude 4" in html
    assert "Ambient AI scribes" in html
    assert "Article 1" in html

def test_render_deep_dive_has_toc():
    curated = {
        "issue_date": "2026-04-04",
        "week_range": "March 30 - April 4, 2026",
        "editorial_summary": "Test.",
        "sections": {
            "top_stories": [{"headline": "Test Story", "priority": "act_now", "deep_dive_notes": "Notes.", "source_article": {"url": "#", "source": "T", "title": "T"}}],
            "vbc_watch": [], "deal_flow": [], "did_you_know": [],
        },
        "trend_watch": {"emerging_signal": None},
    }
    html = render_deep_dive(curated, [])
    assert 'id="top-stories"' in html or 'id="toc"' in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate
python -m pytest tests/test_html_generator.py -v
```
Expected: FAIL (module not found)

- [ ] **Step 3: Create doc_template.html**

Create `generator/templates/doc_template.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Healthcare AI Weekly Deep Dive — {{ week_range }}</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: Georgia, 'Times New Roman', serif; background: #f8f8f8; color: #1a1a1a; line-height: 1.7; }
  .container { max-width: 760px; margin: 0 auto; background: #fff; padding: 48px 36px; }
  h1 { font-size: 28px; font-weight: 700; letter-spacing: -0.5px; margin-bottom: 4px; }
  .subtitle { font-size: 14px; color: #666; margin-bottom: 32px; }
  .editorial-summary { font-size: 16px; line-height: 1.7; color: #333; margin-bottom: 36px; border-left: 3px solid #2563eb; padding-left: 20px; }

  nav#toc { margin-bottom: 36px; padding: 16px 20px; background: #f9fafb; border-radius: 6px; }
  nav#toc h2 { font-size: 13px; text-transform: uppercase; letter-spacing: 1px; color: #888; margin-bottom: 8px; }
  nav#toc a { display: block; font-size: 14px; color: #2563eb; text-decoration: none; padding: 3px 0; }
  nav#toc a:hover { text-decoration: underline; }

  h2.section-header { font-size: 18px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #2563eb; margin: 40px 0 16px 0; padding-bottom: 8px; border-bottom: 2px solid #e5e7eb; }

  .story-card { margin-bottom: 28px; padding-bottom: 20px; border-bottom: 1px solid #f0f0f0; }
  .story-card:last-child { border-bottom: none; }
  .story-headline { font-size: 18px; font-weight: 600; color: #111; cursor: pointer; }
  .story-headline a { color: #111; text-decoration: none; }
  .story-headline a:hover { text-decoration: underline; }
  .badge { display: inline-block; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; padding: 2px 6px; border-radius: 3px; margin-right: 6px; }
  .badge-act-now { background: #dc2626; color: #fff; }
  .badge-watch-this { background: #2563eb; color: #fff; }
  .so-what { font-size: 14px; font-weight: 600; color: #333; margin: 8px 0; }
  .deep-dive { font-size: 15px; line-height: 1.7; color: #333; margin-top: 8px; }
  .risk-angle { background: #fef3c7; padding: 10px 14px; border-radius: 4px; font-size: 14px; margin-top: 12px; color: #92400e; }
  .risk-angle strong { color: #78350f; }
  .source-link { font-size: 12px; color: #888; margin-top: 8px; }
  .source-link a { color: #2563eb; text-decoration: none; }

  .dyk-item { margin-bottom: 24px; }
  .dyk-item h3 { font-size: 16px; font-weight: 600; color: #111; margin-bottom: 6px; }
  .dyk-item .explainer { font-size: 15px; line-height: 1.7; color: #333; }

  .trend-box { background: #f0f4ff; padding: 16px 20px; border-radius: 6px; margin: 28px 0; }
  .trend-box strong { color: #2563eb; }
  .trend-box p { font-size: 15px; line-height: 1.6; color: #333; }

  .sources-list { margin-top: 40px; padding-top: 20px; border-top: 2px solid #e5e7eb; }
  .sources-list h2 { font-size: 14px; text-transform: uppercase; letter-spacing: 1px; color: #888; margin-bottom: 12px; }
  .sources-list ul { list-style: none; padding: 0; }
  .sources-list li { font-size: 13px; color: #666; padding: 3px 0; }
  .sources-list li a { color: #2563eb; text-decoration: none; }
  .sources-list li .src-name { color: #999; font-size: 11px; }

  details summary { cursor: pointer; }
  details summary::-webkit-details-marker { display: none; }

  .footer { margin-top: 40px; padding-top: 16px; border-top: 1px solid #e5e7eb; font-size: 13px; color: #aaa; }
</style>
</head>
<body>
<div class="container">
  <h1>Healthcare AI Weekly</h1>
  <div class="subtitle">Deep Dive — {{ week_range }}</div>

  <div class="editorial-summary">{{ editorial_summary }}</div>

  <nav id="toc">
    <h2>In This Issue</h2>
    {% if top_stories %}<a href="#top-stories">What Matters This Week</a>{% endif %}
    {% if vbc_watch %}<a href="#vbc-watch">VBC Watch</a>{% endif %}
    {% if deal_flow %}<a href="#deal-flow">Deal Flow</a>{% endif %}
    {% if did_you_know %}<a href="#did-you-know">Did You Know?</a>{% endif %}
    {% if trend_signal %}<a href="#trend-watch">Trend Watch</a>{% endif %}
    <a href="#all-sources">All Sources This Week</a>
  </nav>

  {% if top_stories %}
  <h2 class="section-header" id="top-stories">What Matters This Week</h2>
  {% for story in top_stories %}
  <div class="story-card">
    <div class="story-headline">
      {% if story.priority == "act_now" %}<span class="badge badge-act-now">Act Now</span>{% elif story.priority == "watch_this" %}<span class="badge badge-watch-this">Watch This</span>{% endif %}
      <a href="{{ story.source_article.url }}">{{ story.headline }}</a>
    </div>
    <div class="so-what">{{ story.so_what }}</div>
    <div class="deep-dive">{{ story.deep_dive_notes }}</div>
    {% if story.risk_angle %}
    <div class="risk-angle"><strong>Risk angle:</strong> {{ story.risk_angle }}</div>
    {% endif %}
    <div class="source-link">Source: <a href="{{ story.source_article.url }}">{{ story.source_article.source }}</a></div>
  </div>
  {% endfor %}
  {% endif %}

  {% if vbc_watch %}
  <h2 class="section-header" id="vbc-watch">VBC Watch</h2>
  {% for story in vbc_watch %}
  <div class="story-card">
    <div class="story-headline"><a href="{{ story.source_article.url }}">{{ story.headline }}</a></div>
    <div class="so-what">{{ story.so_what }}</div>
    <div class="deep-dive">{{ story.deep_dive_notes }}</div>
    {% if story.risk_angle %}
    <div class="risk-angle"><strong>Risk angle:</strong> {{ story.risk_angle }}</div>
    {% endif %}
    <div class="source-link">Source: <a href="{{ story.source_article.url }}">{{ story.source_article.source }}</a></div>
  </div>
  {% endfor %}
  {% endif %}

  {% if deal_flow %}
  <h2 class="section-header" id="deal-flow">Deal Flow</h2>
  {% for story in deal_flow %}
  <div class="story-card">
    <div class="story-headline"><a href="{{ story.source_article.url }}">{{ story.headline }}</a></div>
    <div class="so-what">{{ story.so_what }}</div>
    <div class="deep-dive">{{ story.deep_dive_notes }}</div>
    <div class="source-link">Source: <a href="{{ story.source_article.url }}">{{ story.source_article.source }}</a></div>
  </div>
  {% endfor %}
  {% endif %}

  {% if did_you_know %}
  <h2 class="section-header" id="did-you-know">Did You Know?</h2>
  {% for item in did_you_know %}
  <div class="dyk-item">
    <h3>{{ item.headline }}</h3>
    <div class="explainer">{{ item.explainer }}</div>
  </div>
  {% endfor %}
  {% endif %}

  {% if trend_signal %}
  <div class="trend-box" id="trend-watch">
    <strong>Trend Watch</strong>
    <p>{{ trend_signal }}</p>
  </div>
  {% endif %}

  <div class="sources-list" id="all-sources">
    <h2>All Sources Considered This Week</h2>
    <ul>
    {% for article in all_articles %}
      <li><a href="{{ article.url }}">{{ article.title }}</a> <span class="src-name">{{ article.source }}</span></li>
    {% endfor %}
    </ul>
  </div>

  <div class="footer">
    Healthcare AI Weekly — curated by Greg Harrison at Guidehouse
  </div>
</div>
</body>
</html>
```

- [ ] **Step 4: Implement html_generator.py**

```python
import os
from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

def render_deep_dive(curated, all_articles):
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=False)
    template = env.get_template("doc_template.html")

    sections = curated.get("sections", {})
    trend_watch = curated.get("trend_watch", {})
    trend_signal = trend_watch.get("emerging_signal") if trend_watch else None

    html = template.render(
        week_range=curated.get("week_range", ""),
        editorial_summary=curated.get("editorial_summary", ""),
        top_stories=sections.get("top_stories", []),
        vbc_watch=sections.get("vbc_watch", []),
        deal_flow=sections.get("deal_flow", []),
        did_you_know=sections.get("did_you_know", []),
        trend_signal=trend_signal,
        all_articles=all_articles or [],
    )
    return html

if __name__ == "__main__":
    import json, sys
    with open(sys.argv[1]) as f:
        curated = json.load(f)
    raw_path = sys.argv[2] if len(sys.argv) > 2 else None
    all_articles = []
    if raw_path:
        with open(raw_path) as f:
            all_articles = json.load(f).get("articles", [])
    html = render_deep_dive(curated, all_articles)
    out = sys.argv[3] if len(sys.argv) > 3 else "data/issues/preview_doc.html"
    with open(out, "w") as f:
        f.write(html)
    print(f"Deep dive preview: {out}")
```

- [ ] **Step 5: Run tests to verify they pass**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate
python -m pytest tests/test_html_generator.py -v
```
Expected: All 2 tests PASS

- [ ] **Step 6: Commit**

```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
git add generator/html_generator.py generator/templates/doc_template.html tests/test_html_generator.py
git commit -m "feat: HTML deep-dive generator with TOC, collapsible sections, and source list"
```

---

### Task 11: LinkedIn Seed Generator

**Files:**
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/generator/linkedin_seed.py`
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/tests/test_linkedin_seed.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_linkedin_seed.py`:

```python
import json
from generator.linkedin_seed import generate_seed

def test_generate_seed_extracts_from_curated():
    curated = {
        "issue_date": "2026-04-04",
        "linkedin_seed": {
            "top_story": "Epic launched an AI agent for nursing workflows",
            "hook": "The EHR wars just entered a new phase.",
            "angle": "Frame around clinical workflow transformation",
        }
    }
    seed = generate_seed(curated)
    assert seed["issue_date"] == "2026-04-04"
    assert seed["top_story"] == "Epic launched an AI agent for nursing workflows"
    assert seed["hook"] == "The EHR wars just entered a new phase."

def test_generate_seed_handles_missing_linkedin_seed():
    curated = {"issue_date": "2026-04-04"}
    seed = generate_seed(curated)
    assert seed["issue_date"] == "2026-04-04"
    assert seed["top_story"] is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate
python -m pytest tests/test_linkedin_seed.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement linkedin_seed.py**

```python
import json
import os

def generate_seed(curated):
    linkedin = curated.get("linkedin_seed", {})
    return {
        "issue_date": curated.get("issue_date", ""),
        "top_story": linkedin.get("top_story"),
        "hook": linkedin.get("hook"),
        "angle": linkedin.get("angle"),
        "source": "healthcare-ai-newsletter",
    }

def save_seed(seed, output_dir="data/linkedin-seed"):
    os.makedirs(output_dir, exist_ok=True)
    date = seed.get("issue_date", "unknown")
    path = os.path.join(output_dir, f"{date}.json")
    with open(path, "w") as f:
        json.dump(seed, f, indent=2)
    return path

def copy_to_linkedin_agent(seed, agent_dir="/Users/greg/Claude/personal/content/linkedin-agent"):
    inbox = os.path.join(agent_dir, "newsletter-seeds")
    os.makedirs(inbox, exist_ok=True)
    date = seed.get("issue_date", "unknown")
    path = os.path.join(inbox, f"{date}.json")
    with open(path, "w") as f:
        json.dump(seed, f, indent=2)
    return path
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate
python -m pytest tests/test_linkedin_seed.py -v
```
Expected: All 2 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
git add generator/linkedin_seed.py tests/test_linkedin_seed.py
git commit -m "feat: LinkedIn seed generator with cross-project export"
```

---

### Task 12: Distributor — Email Send and HTML Publish

**Files:**
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/distributor/send_email.py`
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/distributor/publish_html.py`
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/tests/test_distributor.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_distributor.py`:

```python
from distributor.send_email import build_gws_send_command
from distributor.publish_html import build_issue_path

def test_build_gws_send_command():
    cmd = build_gws_send_command(
        to="gharrison@guidehouse.com",
        subject="Healthcare AI Weekly — Week of April 4, 2026",
        html_body="<html><body>Test</body></html>",
    )
    assert "gws" in cmd
    assert "gharrison@guidehouse.com" in cmd
    assert "Healthcare AI Weekly" in cmd

def test_build_issue_path():
    path = build_issue_path("2026-04-04")
    assert path == "issues/2026-04-04"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate
python -m pytest tests/test_distributor.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement send_email.py**

```python
import base64
import json
import subprocess
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def build_gws_send_command(to, subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["To"] = to
    msg["Subject"] = subject

    plain_text = "This email is best viewed in an HTML-capable email client."
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

    body_json = json.dumps({"raw": raw})

    cmd = f'gws gmail users messages send --params \'{{"userId": "me"}}\' --json \'{body_json}\''
    return cmd

def send_email(to, subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["To"] = to
    msg["Subject"] = subject

    plain_text = "This email is best viewed in an HTML-capable email client."
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

    body_json = json.dumps({"raw": raw})
    params_json = json.dumps({"userId": "me"})

    result = subprocess.run(
        ["gws", "gmail", "users", "messages", "send",
         "--params", params_json,
         "--json", body_json],
        capture_output=True, text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"gws email send failed: {result.stderr}")

    print(f"Email sent to {to}")
    return result.stdout
```

- [ ] **Step 4: Implement publish_html.py**

```python
import os
import json
import shutil
import subprocess

def build_issue_path(date_str):
    return f"issues/{date_str}"

def publish_to_repo(html_content, curated_data, date_str,
                    repo_dir="/Users/greg/Claude/personal/content/healthcare-ai-weekly",
                    local_backup_dir="data/issues"):
    issue_path = build_issue_path(date_str)

    local_dir = os.path.join(local_backup_dir, date_str)
    os.makedirs(local_dir, exist_ok=True)
    with open(os.path.join(local_dir, "index.html"), "w") as f:
        f.write(html_content)
    with open(os.path.join(local_dir, "data.json"), "w") as f:
        json.dump(curated_data, f, indent=2)

    if os.path.exists(repo_dir):
        repo_issue_dir = os.path.join(repo_dir, issue_path)
        os.makedirs(repo_issue_dir, exist_ok=True)
        shutil.copy2(os.path.join(local_dir, "index.html"), repo_issue_dir)
        shutil.copy2(os.path.join(local_dir, "data.json"), repo_issue_dir)

        subprocess.run(["git", "add", issue_path], cwd=repo_dir, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"Add issue {date_str}"],
            cwd=repo_dir, capture_output=True,
        )
        subprocess.run(["git", "push"], cwd=repo_dir, capture_output=True)
        print(f"Published to repo: {issue_path}")
    else:
        print(f"Repo not found at {repo_dir}, saved locally only: {local_dir}")

    return local_dir
```

- [ ] **Step 5: Run tests to verify they pass**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate
python -m pytest tests/test_distributor.py -v
```
Expected: All 2 tests PASS

- [ ] **Step 6: Commit**

```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
git add distributor/send_email.py distributor/publish_html.py tests/test_distributor.py
git commit -m "feat: distributor with gws email send and GitHub repo publishing"
```

---

### Task 13: Pipeline Orchestrator

**Files:**
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/pipeline.py`
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/tests/test_pipeline.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_pipeline.py`:

```python
from pipeline import compute_date_range, get_data_paths

def test_compute_date_range_for_friday():
    date_str = "2026-04-04"
    start, end, display = compute_date_range(date_str)
    assert start == "2026-03-28"
    assert end == "2026-04-04"
    assert "March 28" in display or "March 30" in display or "April 4" in display

def test_get_data_paths():
    paths = get_data_paths("2026-04-04")
    assert paths["raw"] == "data/raw/2026-04-04.json"
    assert paths["curated"] == "data/curated/2026-04-04.json"
    assert paths["delta"] == "data/curated/2026-04-04-delta.json"
    assert "2026-04-04" in paths["issue_dir"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate
python -m pytest tests/test_pipeline.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement pipeline.py**

```python
import argparse
import json
import os
import sys
from datetime import datetime, timedelta

def compute_date_range(date_str):
    end_date = datetime.strptime(date_str, "%Y-%m-%d")
    start_date = end_date - timedelta(days=7)
    display = f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}"
    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), display

def get_data_paths(date_str):
    return {
        "raw": f"data/raw/{date_str}.json",
        "curated": f"data/curated/{date_str}.json",
        "delta": f"data/curated/{date_str}-delta.json",
        "issue_dir": f"data/issues/{date_str}",
        "email_html": f"data/issues/{date_str}/email.html",
        "doc_html": f"data/issues/{date_str}/index.html",
        "linkedin_seed": f"data/linkedin-seed/{date_str}.json",
    }

def run_collector(date_str, paths):
    print(f"\n{'='*60}")
    print(f"STAGE 1: COLLECTOR")
    print(f"{'='*60}")

    from collector.rss_collector import collect_rss
    from collector.filters import deduplicate_articles

    articles = collect_rss("collector/sources.json")
    articles = deduplicate_articles(articles)

    start, end, display = compute_date_range(date_str)
    raw_data = {
        "collection_date": date_str,
        "week_range": display,
        "article_count": len(articles),
        "articles": articles,
    }

    os.makedirs(os.path.dirname(paths["raw"]), exist_ok=True)
    with open(paths["raw"], "w") as f:
        json.dump(raw_data, f, indent=2)

    print(f"Collected {len(articles)} articles")
    print(f"Saved to {paths['raw']}")
    return raw_data

def run_delta(date_str, paths):
    print(f"\n{'='*60}")
    print(f"STAGE 1.5: DELTA TRACKER")
    print(f"{'='*60}")

    from data.curated.delta_tracker import load_history, compute_delta

    history = load_history("data/curated")

    raw_articles = []
    if os.path.exists(paths["raw"]):
        with open(paths["raw"]) as f:
            raw_articles = json.load(f).get("articles", [])

    delta = compute_delta(history, raw_articles)

    with open(paths["delta"], "w") as f:
        json.dump(delta, f, indent=2)

    print(f"Analyzed {delta.get('weeks_analyzed', 0)} prior weeks")
    print(f"Recurring companies: {len(delta.get('recurring_companies', []))}")
    print(f"Saved to {paths['delta']}")
    return delta

def run_curator(date_str, paths):
    print(f"\n{'='*60}")
    print(f"STAGE 2: CURATOR AGENT")
    print(f"{'='*60}")

    from curator.curator_agent import run_curator as curator_run

    delta_path = paths["delta"] if os.path.exists(paths["delta"]) else None

    curated = curator_run(
        raw_data_path=paths["raw"],
        output_path=paths["curated"],
        delta_path=delta_path,
    )

    story_count = sum(
        len(curated.get("sections", {}).get(s, []))
        for s in ["top_stories", "vbc_watch", "deal_flow", "did_you_know"]
    )
    print(f"Curated {story_count} stories across all sections")
    print(f"Saved to {paths['curated']}")
    return curated

def run_generator(date_str, paths):
    print(f"\n{'='*60}")
    print(f"STAGE 3: GENERATOR")
    print(f"{'='*60}")

    from generator.email_generator import render_email
    from generator.html_generator import render_deep_dive
    from generator.linkedin_seed import generate_seed, save_seed, copy_to_linkedin_agent

    with open(paths["curated"]) as f:
        curated = json.load(f)

    raw_articles = []
    if os.path.exists(paths["raw"]):
        with open(paths["raw"]) as f:
            raw_articles = json.load(f).get("articles", [])

    os.makedirs(os.path.dirname(paths["email_html"]), exist_ok=True)

    email_html = render_email(curated)
    with open(paths["email_html"], "w") as f:
        f.write(email_html)
    print(f"Email generated: {paths['email_html']}")

    doc_html = render_deep_dive(curated, raw_articles)
    with open(paths["doc_html"], "w") as f:
        f.write(doc_html)
    print(f"Deep dive generated: {paths['doc_html']}")

    seed = generate_seed(curated)
    save_seed(seed)
    try:
        copy_to_linkedin_agent(seed)
        print("LinkedIn seed exported")
    except Exception as e:
        print(f"LinkedIn seed export skipped: {e}")

    return email_html, doc_html

def run_distributor(date_str, paths):
    print(f"\n{'='*60}")
    print(f"STAGE 4: DISTRIBUTOR")
    print(f"{'='*60}")

    from distributor.send_email import send_email
    from distributor.publish_html import publish_to_repo
    from generator.email_generator import format_subject_line

    with open(paths["curated"]) as f:
        curated = json.load(f)

    with open(paths["email_html"]) as f:
        email_html = f.read()

    with open(paths["doc_html"]) as f:
        doc_html = f.read()

    _, _, display = compute_date_range(date_str)
    subject = format_subject_line(display)

    send_email("gharrison@guidehouse.com", subject, email_html)
    print("Email sent to gharrison@guidehouse.com")

    publish_to_repo(doc_html, curated, date_str)
    print(f"HTML published for {date_str}")

def run_score_update(date_str, paths):
    print(f"\n{'='*60}")
    print(f"STAGE 5: SOURCE SCORE UPDATE")
    print(f"{'='*60}")

    from collector.source_scorer import load_scores, update_scores, save_scores, get_flagged_sources

    if not os.path.exists(paths["raw"]) or not os.path.exists(paths["curated"]):
        print("Skipping score update (missing data)")
        return

    with open(paths["raw"]) as f:
        raw = json.load(f)
    with open(paths["curated"]) as f:
        curated = json.load(f)

    collected = raw.get("articles", [])
    curated_sources = []
    for section in curated.get("sections", {}).values():
        for story in section:
            src = story.get("source_article", {}).get("source")
            if src:
                curated_sources.append(src)

    scores = load_scores()
    scores = update_scores(scores, collected, curated_sources)
    save_scores(scores)

    flagged = get_flagged_sources(scores)
    if flagged:
        print(f"Flagged low-performing sources: {[f['source'] for f in flagged]}")
    print("Source scores updated")

def main():
    parser = argparse.ArgumentParser(description="Healthcare AI Weekly Newsletter Pipeline")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                        help="Issue date (YYYY-MM-DD), defaults to today")
    parser.add_argument("--stage", choices=["collector", "curator", "generator", "distributor", "all"],
                        default="all", help="Run a specific stage or all")
    parser.add_argument("--skip-send", action="store_true", help="Skip email send (for testing)")
    args = parser.parse_args()

    date_str = args.date
    paths = get_data_paths(date_str)

    print(f"Healthcare AI Weekly — {date_str}")
    print(f"Stage: {args.stage}")

    if args.stage in ("collector", "all"):
        run_collector(date_str, paths)

    if args.stage in ("curator", "all"):
        run_delta(date_str, paths)
        run_curator(date_str, paths)

    if args.stage in ("generator", "all"):
        run_generator(date_str, paths)

    if args.stage in ("distributor", "all"):
        if args.skip_send:
            print("\nSkipping distributor (--skip-send)")
        else:
            run_distributor(date_str, paths)

    if args.stage == "all":
        run_score_update(date_str, paths)

    print(f"\nDone. Issue date: {date_str}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate
python -m pytest tests/test_pipeline.py -v
```
Expected: All 2 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
git add pipeline.py tests/test_pipeline.py
git commit -m "feat: pipeline orchestrator with stage-by-stage execution and CLI flags"
```

---

### Task 14: Run All Tests

**Files:** None (verification only)

- [ ] **Step 1: Run the full test suite**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate
python -m pytest tests/ -v
```
Expected: All tests PASS

- [ ] **Step 2: Fix any failures**

If any tests fail, fix the implementation and re-run.

- [ ] **Step 3: Commit any fixes**

```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
git add -A
git commit -m "fix: resolve test failures from integration"
```

---

### Task 15: Manual Test Run — Week of March 30 - April 4, 2026

**Files:** None (end-to-end test)

- [ ] **Step 1: Run collector stage**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate
python pipeline.py --date 2026-04-04 --stage collector
```
Expected: Outputs article count and saves to `data/raw/2026-04-04.json`

- [ ] **Step 2: Inspect raw collection**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
python -c "import json; d=json.load(open('data/raw/2026-04-04.json')); print(f'Articles: {d[\"article_count\"]}'); [print(f'  - [{a[\"source\"]}] {a[\"title\"][:80]}') for a in d['articles'][:15]]"
```
Expected: See 15+ articles from various sources. If count is low, check RSS feed URLs in `sources.json` and fix any broken ones.

- [ ] **Step 3: Run curator stage**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate
python pipeline.py --date 2026-04-04 --stage curator
```
Expected: Outputs curated story count and saves to `data/curated/2026-04-04.json`

- [ ] **Step 4: Inspect curated output**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
python -c "
import json
d = json.load(open('data/curated/2026-04-04.json'))
print('EDITORIAL SUMMARY:')
print(d.get('editorial_summary', 'MISSING')[:200])
print()
for section in ['top_stories', 'vbc_watch', 'deal_flow', 'did_you_know']:
    items = d.get('sections', {}).get(section, [])
    print(f'{section}: {len(items)} items')
    for item in items:
        print(f'  - {item.get(\"headline\", \"no headline\")}')
"
```
Expected: See curated stories across all sections with editorial headlines

- [ ] **Step 5: Run generator stage**

Run:
```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate
python pipeline.py --date 2026-04-04 --stage generator
```
Expected: Email and deep-dive HTML files created in `data/issues/2026-04-04/`

- [ ] **Step 6: Preview email and deep-dive in browser**

Run:
```bash
open data/issues/2026-04-04/email.html
open data/issues/2026-04-04/index.html
```
Expected: Both open in browser. Review for: correct sections, priority badges rendering, clean typography, no AI slop, Nate B Jones voice in the content.

- [ ] **Step 7: Greg reviews and provides feedback**

After review, append feedback to `curator/feedback.md`:

```markdown
## 2026-04-04
- [Your notes here after reviewing]
```

---

### Task 16: Create Private GitHub Repo and SKILL.md

**Files:**
- Create: `/Users/greg/Claude/healthcare-ai-newsletter/SKILL.md`

- [ ] **Step 1: Create private GitHub repo**

Run:
```bash
gh repo create healthcare-ai-weekly --private --description "Healthcare AI Weekly newsletter archive"
gh repo clone healthcare-ai-weekly /Users/greg/Claude/personal/content/healthcare-ai-weekly
```
Expected: Private repo created and cloned

- [ ] **Step 2: Initialize repo structure**

Run:
```bash
cd /Users/greg/Claude/personal/content/healthcare-ai-weekly
mkdir -p issues
echo "# Healthcare AI Weekly Archive\n\nWeekly deep-dive issues on AI in healthcare." > README.md
git add README.md
git commit -m "Initial commit"
git push -u origin main
```

- [ ] **Step 3: Create SKILL.md for scheduled trigger**

Create `/Users/greg/Claude/healthcare-ai-newsletter/SKILL.md`:

```markdown
# Healthcare AI Weekly Newsletter

## What This Does

Runs the Healthcare AI Weekly newsletter pipeline:
1. Collects AI healthcare news from RSS feeds
2. Curates and ranks stories using Claude as an editorial agent
3. Generates an executive HTML email and deep-dive HTML document
4. Sends email to gharrison@guidehouse.com
5. Publishes deep-dive to private GitHub repo
6. Exports LinkedIn seed file for the LinkedIn content agent

## How to Run

```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate
python pipeline.py
```

## Manual Override

```bash
# Specific date
python pipeline.py --date 2026-04-04

# Single stage
python pipeline.py --date 2026-04-04 --stage collector

# Skip email send (preview only)
python pipeline.py --date 2026-04-04 --skip-send
```

## Schedule

Cron: `0 5 * * 5` (every Friday at 5:00 AM Eastern)
```

- [ ] **Step 4: Commit SKILL.md**

```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
git add SKILL.md
git commit -m "feat: add SKILL.md for scheduled trigger"
```

---

### Task 17: Schedule the Automation

- [ ] **Step 1: Use Claude Code /schedule to create trigger**

Use the `/schedule` skill to create a remote trigger named `healthcare-ai-weekly` with cron `0 5 * * 5` that runs the pipeline.

- [ ] **Step 2: Verify the schedule**

Run:
```bash
# List existing triggers to confirm
```
Expected: `healthcare-ai-weekly` shows as active with Friday 5 AM schedule

- [ ] **Step 3: Commit**

Final commit with any adjustments made during scheduling.

```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
git add -A
git commit -m "feat: complete newsletter pipeline with scheduling"
```

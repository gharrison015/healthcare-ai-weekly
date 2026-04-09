import json
import os
import re
from datetime import datetime, timezone
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()


def load_persona(persona_path="curator/persona.md"):
    """Load the editorial persona for voice consistency."""
    with open(persona_path) as f:
        return f.read()


def slugify(text):
    """Convert a headline to a URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:60].strip("-")


def strip_formatting(text):
    """Remove all em dashes, markdown bold, and citation brackets. Clean output only."""
    import re
    text = text.replace("\u2014", ",")
    text = text.replace("\u2013", ",")
    text = text.replace(" -- ", ", ")
    text = text.replace("--", ",")
    text = text.replace("**", "")
    text = re.sub(r'\s*\[\d+(?:\s*,\s*\d+)*\]', '', text)
    text = re.sub(r'  +', ' ', text)
    return text.strip()


def generate_bulletin(topic, credibility_result, persona_path="curator/persona.md"):
    """Use Claude to write a bulletin take for a verified topic.

    Args:
        topic: dict from velocity_detector with topic_key, metrics, representative_tweets
        credibility_result: dict from credibility_checker with decision, sources, primary_source

    Returns a bulletin dict ready for saving.
    """
    persona = load_persona(persona_path)

    # Build context from tweets and sources
    rep_tweets = topic.get("representative_tweets", [])
    tweet_context = "\n".join(
        f"- @{t['author_username']}: {t['text'][:280]}"
        for t in rep_tweets[:5]
    )

    source = credibility_result.get("primary_source", {})
    source_url = source.get("link", "") if source else ""
    source_name = source.get("source", "") if source else ""
    source_title = source.get("title", "") if source else ""

    news_sources = credibility_result.get("sources", [])
    news_context = "\n".join(
        f"- [{a.get('source', 'unknown')}] {a.get('title', '')}"
        for a in news_sources[:5]
    )

    metrics = topic.get("metrics", {})

    prompt = f"""# YOUR EDITORIAL IDENTITY

{persona}

# TASK: WRITE A BREAKING BULLETIN

You are writing a short, punchy breaking news bulletin for the Healthcare AI Weekly audience.
This is the signal layer: fast, authoritative, opinionated.

# TOPIC

Key entity: {topic.get('topic_key', 'unknown')}
Velocity score: {topic.get('velocity_score', 0)}
Total impressions: {metrics.get('total_impressions', 0):,}
Unique accounts discussing: {metrics.get('unique_authors', 0)}
Hours since first post: {metrics.get('hours_elapsed', 0)}

# WHAT PEOPLE ARE SAYING ON X

{tweet_context}

# NEWS COVERAGE

{news_context}

Primary source: {source_title}
Source URL: {source_url}

# INSTRUCTIONS

Write a bulletin with:
1. A headline: short, punchy, max 8-10 words. The hook.
2. A body: 3-5 sentences. Lead with what happened, then why it matters for health systems and the consulting landscape. Same Nate B Jones voice.
3. Tags: 2-4 lowercase tags for topic tracking.

CRITICAL RULES:
- Do NOT use em dashes. Not the character \u2014, not --, not \u2013. Use periods, commas, or colons instead.
- Do NOT use passive voice like "It was announced that..."
- Do NOT sound like a press release.
- Be direct, confident, opinionated.
- If the impact is unclear, say so honestly.

Return ONLY a JSON object (no markdown fencing) with this exact structure:
{{
  "headline": "Short Punchy Headline Here",
  "body": "3-5 sentence take...",
  "tags": ["tag1", "tag2"]
}}"""

    client = Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = response.content[0].text.strip()

    # Strip markdown fencing if present
    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

    generated = json.loads(response_text)

    # Strip em dashes from all generated content
    headline = strip_formatting(generated.get("headline", ""))
    body = strip_formatting(generated.get("body", ""))
    tags = generated.get("tags", [])

    now = datetime.now(timezone.utc)
    slug = slugify(headline)

    bulletin = {
        "timestamp": now.isoformat(),
        "slug": slug,
        "headline": headline,
        "body": body,
        "source_url": source_url,
        "source_name": source_name or source_title,
        "velocity_score": topic.get("velocity_score", 0),
        "verification": credibility_result.get("decision", "unknown"),
        "tags": tags,
        "metrics": {
            "total_impressions": metrics.get("total_impressions", 0),
            "unique_authors": metrics.get("unique_authors", 0),
            "velocity": metrics.get("velocity", 0),
        },
    }

    print(f"Bulletin Generator: '{headline}' ({len(body)} chars)")
    return bulletin


def save_bulletin(bulletin, bulletins_dir="data/bulletins"):
    """Save a bulletin JSON to the data directory.

    Returns the file path of the saved bulletin.
    """
    os.makedirs(bulletins_dir, exist_ok=True)

    now = datetime.now(timezone.utc)
    slug = bulletin.get("slug", "unknown")
    filename = f"{now.strftime('%Y-%m-%d-%H')}-{slug}.json"
    filepath = os.path.join(bulletins_dir, filename)

    with open(filepath, "w") as f:
        json.dump(bulletin, f, indent=2)

    print(f"Bulletin saved: {filepath}")
    return filepath

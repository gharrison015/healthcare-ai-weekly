import json
import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

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

CRITICAL: Do not use em dashes (the -- or \u2014 character) anywhere in your output. Not in headlines, not in summaries, not in the editorial summary, not anywhere. Use periods, commas, colons, or semicolons instead.

Return a single JSON object with this exact structure. No markdown fencing, just raw JSON:

{{
  "editorial_summary": "One paragraph overview of the week's themes and what matters",
  "sections": {{
    "top_stories": [
      {{
        "headline": "Short punchy headline, max 8-10 words. The hook, not a summary.",
        "source_article": {{"id": "original article id", "title": "original title", "source": "source name", "url": "url"}},
        "priority": "act_now or watch_this",
        "so_what": "Why a health system exec should care, 1-2 sentences",
        "risk_angle": "Downside or contrarian take, or null if not applicable",
        "consulting_signal": "Why a client might ask about this, or null",
        "connections": ["ids of related articles this week"],
        "deep_dive_notes": "Extended analysis for the HTML doc, 200-400 words",
        "email_summary": "Give the reader everything they need to know in 2-3 sentences. Include key numbers, names, and data points. The headline hooks, this delivers the substance. Be concise but complete."
      }}
    ],
    "vbc_watch": [same structure as top_stories],
    "ma_partnerships": [same structure as top_stories],
    "consulting_intelligence": [same structure as top_stories, 1-3 items about consulting firm moves],
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
        max_tokens=16000,
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
            max_tokens=16000,
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

    # Strip em dashes from all string values
    def strip_em_dashes(obj):
        if isinstance(obj, str):
            return obj.replace("\u2014", ",").replace("\u2013", ",").replace(" -- ", ", ").replace("--", ",")
        elif isinstance(obj, dict):
            return {k: strip_em_dashes(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [strip_em_dashes(item) for item in obj]
        return obj

    curated = strip_em_dashes(curated)

    with open(output_path, "w") as f:
        json.dump(curated, f, indent=2)

    return curated

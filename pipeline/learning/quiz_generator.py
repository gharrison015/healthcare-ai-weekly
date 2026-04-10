"""
Quiz Generator -- Creates trivia-style quiz questions from NotebookLM content.

Primary: `notebooklm generate quiz -s [source_ids] --json` then
         `notebooklm download quiz --format json`. Parse and normalize.
Fallback: Anthropic SDK to generate questions from extracted content.

Quiz output format:
{
  "id": "topic-slug-q1",
  "question": "...",
  "options": ["A", "B", "C", "D"],
  "correct": 2,
  "explanation": "..."
}

All em dashes are stripped. Validated: 4 options, correct index in range,
no empty fields.
"""

import json
import os
import re
import subprocess
import tempfile
import time

from learning.content_extractor import run_notebooklm


def strip_em_dashes(text):
    """Replace em dashes and en dashes with ' - '."""
    if not text:
        return text
    return text.replace("\u2014", " - ").replace("\u2013", " - ")


def validate_question(q):
    """
    Validate a single normalized question dict.
    Returns True if valid, False otherwise.
    """
    if not q.get("id"):
        return False
    if not q.get("question"):
        return False
    options = q.get("options", [])
    if not isinstance(options, list) or len(options) != 4:
        return False
    if any(not opt for opt in options):
        return False
    correct = q.get("correct")
    if not isinstance(correct, int) or correct < 0 or correct >= len(options):
        return False
    if not q.get("explanation"):
        return False
    return True


def generate_quiz_via_notebooklm(source_ids, notebook_id, difficulty="medium", quantity="more"):
    """
    Use notebooklm CLI to generate a quiz scoped to specific sources.

    Runs: notebooklm generate quiz -s [source_ids] --json
    Returns the raw quiz data from NotebookLM, or None on failure.
    """
    args = [
        "generate", "quiz",
        "Focus on surprising facts and practical takeaways. "
        "Make questions feel like fun trivia, not an exam.",
        "-n", notebook_id,
        "--difficulty", difficulty,
        "--quantity", quantity,
        "--wait",
        "--json",
    ]
    for sid in source_ids:
        args.extend(["-s", sid])

    print(f"    Generating quiz via NotebookLM ({len(source_ids)} sources)...")
    output = run_notebooklm(args, timeout=180)
    if output is None:
        return None

    try:
        result = json.loads(output)
        return result
    except json.JSONDecodeError:
        return None


def download_quiz_json(notebook_id, artifact_id=None):
    """
    Download the most recent quiz as JSON.

    Runs: notebooklm download quiz --format json
    """
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tmp:
        tmp_path = tmp.name

    args = ["download", "quiz", tmp_path, "-n", notebook_id, "--format", "json"]
    if artifact_id:
        args.extend(["-a", artifact_id])

    output = run_notebooklm(args, timeout=60)
    if output is None:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        return None

    try:
        with open(tmp_path) as f:
            quiz_data = json.load(f)
        return quiz_data
    except (json.JSONDecodeError, FileNotFoundError):
        return None
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def normalize_quiz_questions(raw_quiz, topic_slug, max_questions=10):
    """
    Normalize quiz data from NotebookLM (or Anthropic) into our standard format.

    Handles multiple input structures:
      - list of question dicts
      - dict with 'questions' key
      - dict with nested 'quiz' -> 'questions'
      - dict with 'items' key

    Returns a list of validated, em-dash-free question dicts.
    """
    questions = []

    # Find the questions list in various possible structures
    raw_questions = []
    if isinstance(raw_quiz, list):
        raw_questions = raw_quiz
    elif isinstance(raw_quiz, dict):
        raw_questions = (
            raw_quiz.get("questions", [])
            or raw_quiz.get("quiz", {}).get("questions", [])
            or raw_quiz.get("items", [])
        )

    for i, rq in enumerate(raw_questions[:max_questions]):
        question_text = rq.get("question", rq.get("text", rq.get("prompt", "")))
        if not question_text:
            continue

        # Extract options (handle string list, dict list, or keyed variants)
        options = rq.get("options", rq.get("choices", rq.get("answers", [])))
        if isinstance(options, list) and len(options) >= 2:
            clean_options = []
            for opt in options:
                if isinstance(opt, str):
                    clean_options.append(opt)
                elif isinstance(opt, dict):
                    clean_options.append(opt.get("text", opt.get("label", str(opt))))
                else:
                    clean_options.append(str(opt))
            options = clean_options[:4]
        else:
            continue  # Skip questions without proper options

        # Require exactly 4 options
        if len(options) != 4:
            continue

        # Find correct answer index
        correct = rq.get("correct", rq.get("correct_index", rq.get("answer", 0)))
        if isinstance(correct, str):
            # Match correct answer text to an option
            correct_lower = correct.lower().strip()
            found = False
            for idx, opt in enumerate(options):
                if opt.lower().strip() == correct_lower or correct_lower in opt.lower():
                    correct = idx
                    found = True
                    break
            if not found:
                correct = 0

        # Clamp correct index to valid range
        if not isinstance(correct, int):
            try:
                correct = int(correct)
            except (ValueError, TypeError):
                correct = 0
        correct = max(0, min(correct, len(options) - 1))

        # Explanation
        explanation = rq.get("explanation", rq.get("rationale", rq.get("why", "")))

        # Strip em dashes from all text fields
        question_text = strip_em_dashes(question_text)
        explanation = strip_em_dashes(explanation)
        options = [strip_em_dashes(o) for o in options]

        questions.append({
            "id": f"{topic_slug}-q{i+1}",
            "question": question_text,
            "options": options,
            "correct": correct,
            "explanation": explanation,
        })

    return questions


QUESTION_HISTORY_PATH = "data/learn/question-history.json"


def load_question_history():
    """Load the question history file. Returns dict keyed by topic slug."""
    if not os.path.exists(QUESTION_HISTORY_PATH):
        return {}
    try:
        with open(QUESTION_HISTORY_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def save_question_history(history):
    """Save question history to disk."""
    os.makedirs(os.path.dirname(QUESTION_HISTORY_PATH), exist_ok=True)
    with open(QUESTION_HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=2)


def append_to_history(slug, new_questions, history=None):
    """Append new question texts to the history file for a given topic."""
    if history is None:
        history = load_question_history()
    if slug not in history:
        history[slug] = []
    for q in new_questions:
        text = q.get("question", "").strip()
        if text and text not in history[slug]:
            history[slug].append(text)
    save_question_history(history)
    return history


def generate_quiz_via_anthropic(cluster, max_questions=10, level=None):
    """
    Fallback: use the Anthropic SDK to generate quiz questions from
    extracted source content. Reads question history to avoid repeats.
    """
    try:
        from anthropic import Anthropic
    except ImportError:
        print("    Anthropic SDK not available for fallback quiz generation")
        return []

    client = Anthropic()

    # Build context from source guides
    context_parts = []
    for source in cluster.get("sources", []):
        title = source.get("title", "Unknown")
        guide = source.get("guide", {})
        summary = ""
        if isinstance(guide, dict):
            summary = guide.get("summary", "")
        elif isinstance(guide, str):
            summary = guide
        context_parts.append(f"Source: {title}\n{summary}")

    context = "\n\n---\n\n".join(context_parts)
    topic_title = cluster.get("title", "AI")
    slug = cluster.get("slug", "topic")

    # Load history of previously-asked questions for this topic
    history = load_question_history()
    prior_questions = history.get(slug, [])
    history_block = ""
    if prior_questions:
        # Include up to the last 100 previously-asked questions to stay within context
        recent = prior_questions[-100:]
        history_block = "\n\nPREVIOUSLY ASKED QUESTIONS (DO NOT REPEAT OR REPHRASE THESE):\n" + "\n".join(
            f"- {q}" for q in recent
        )

    level_hint = ""
    if level == 100:
        level_hint = "\n- Target difficulty: FUNDAMENTALS (100-level). Accessible to someone new to AI. Focus on core concepts, basic vocabulary, surprising facts."
    elif level == 200:
        level_hint = "\n- Target difficulty: APPLIED (200-level). For professionals using AI at work. Focus on practical applications, trade-offs, real examples."
    elif level == 300:
        level_hint = "\n- Target difficulty: STRATEGIC (300-level). For executives making AI decisions. Focus on business implications, ROI, risk management, market dynamics."

    prompt = f"""Generate {max_questions} trivia-style multiple choice questions about "{topic_title}" based on the content below.

RULES:
- Each question should have exactly 4 options
- Questions should feel like fun "did you know?" trivia, not exam questions
- Base questions on specific facts, numbers, or examples from the sources
- Include a brief explanation for each correct answer
- Do NOT use em dashes anywhere
- Use plain, direct language appropriate for business professionals
- Every question must be NEW. Do not repeat, rephrase, or substantially overlap with previously asked questions.{level_hint}

CONTENT:
{context}{history_block}

Return ONLY a JSON array (no markdown fencing) where each element has:
- "question": the question text
- "options": array of 4 option strings
- "correct": zero-based index of the correct option
- "explanation": why that answer is correct (1-2 sentences)
"""

    print(f"    Generating quiz via Anthropic for '{topic_title}'...")
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        # Strip markdown fencing if present
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

        raw = json.loads(text)
        return normalize_quiz_questions(raw, slug, max_questions)
    except Exception as e:
        print(f"    Anthropic fallback failed: {e}")
        return []


def get_level_for_slug(slug):
    """Mirror the frontend getTopicLevel() logic so prompts can target difficulty."""
    if "101" in slug or "fundamentals" in slug:
        return 100
    if "strategy" in slug or "leaders" in slug:
        return 300
    return 200


def generate_quiz_for_cluster(cluster, notebook_id, quiz_settings):
    """
    Generate quiz questions for a topic cluster.
    Tries NotebookLM first, falls back to Anthropic SDK.
    Tracks question history to avoid repeats across runs.
    """
    slug = cluster["slug"]
    source_ids = cluster.get("source_ids", [])
    max_q = quiz_settings.get("questions_per_topic", 10)
    difficulty = quiz_settings.get("difficulty", "medium")
    quantity = quiz_settings.get("quantity", "more")
    level = get_level_for_slug(slug)

    questions = []

    # Primary: NotebookLM generate quiz
    if source_ids:
        result = generate_quiz_via_notebooklm(
            source_ids, notebook_id, difficulty, quantity
        )
        if result:
            artifact_id = None
            if isinstance(result, dict):
                artifact_id = result.get("artifact_id", result.get("id"))

            time.sleep(3)  # Let the artifact finalize
            downloaded = download_quiz_json(notebook_id, artifact_id)
            if downloaded:
                questions = normalize_quiz_questions(downloaded, slug, max_q)

    # Fallback: Anthropic SDK (uses history + level targeting)
    if not questions:
        print(f"    NotebookLM quiz unavailable for '{slug}', using Anthropic fallback (level {level})...")
        questions = generate_quiz_via_anthropic(cluster, max_q, level=level)

    # Validate all questions
    questions = [q for q in questions if validate_question(q)]

    # Deduplicate against history and append new ones
    history = load_question_history()
    prior = set(q.strip() for q in history.get(slug, []))
    fresh_questions = [q for q in questions if q.get("question", "").strip() not in prior]

    if len(fresh_questions) < len(questions):
        print(f"    Filtered {len(questions) - len(fresh_questions)} duplicate questions from history")

    if fresh_questions:
        append_to_history(slug, fresh_questions, history)
        print(f"    Generated {len(fresh_questions)} new questions for '{slug}' (level {level})")
    else:
        print(f"    Warning: no fresh questions generated for '{slug}'")

    return {
        "title": f"Quick Check: {cluster['title']}",
        "questions": fresh_questions,
        "level": level,
    }

"""Tests for quiz_generator.py -- format validation, em dash stripping, option normalization, correct index validation."""

from learning.quiz_generator import normalize_quiz_questions, validate_question, strip_em_dashes


# --- strip_em_dashes tests ---

def test_strip_em_dashes_em():
    """Em dash (U+2014) should be replaced."""
    assert "\u2014" not in strip_em_dashes("Hello \u2014 world")
    assert strip_em_dashes("Hello \u2014 world") == "Hello  -  world"


def test_strip_em_dashes_en():
    """En dash (U+2013) should be replaced."""
    assert "\u2013" not in strip_em_dashes("Hello \u2013 world")


def test_strip_em_dashes_none():
    """None input should return None."""
    assert strip_em_dashes(None) is None


def test_strip_em_dashes_empty():
    """Empty string should return empty string."""
    assert strip_em_dashes("") == ""


# --- validate_question tests ---

def test_validate_question_valid():
    """A properly formed question should pass validation."""
    q = {
        "id": "test-q1",
        "question": "What is AI?",
        "options": ["A", "B", "C", "D"],
        "correct": 1,
        "explanation": "B is correct.",
    }
    assert validate_question(q) is True


def test_validate_question_missing_id():
    q = {"question": "Q?", "options": ["A", "B", "C", "D"], "correct": 0, "explanation": "A."}
    assert validate_question(q) is False


def test_validate_question_wrong_option_count():
    q = {"id": "q1", "question": "Q?", "options": ["A", "B", "C"], "correct": 0, "explanation": "A."}
    assert validate_question(q) is False


def test_validate_question_correct_out_of_range():
    q = {"id": "q1", "question": "Q?", "options": ["A", "B", "C", "D"], "correct": 5, "explanation": "A."}
    assert validate_question(q) is False


def test_validate_question_negative_correct():
    q = {"id": "q1", "question": "Q?", "options": ["A", "B", "C", "D"], "correct": -1, "explanation": "A."}
    assert validate_question(q) is False


def test_validate_question_empty_option():
    q = {"id": "q1", "question": "Q?", "options": ["A", "", "C", "D"], "correct": 0, "explanation": "A."}
    assert validate_question(q) is False


def test_validate_question_missing_explanation():
    q = {"id": "q1", "question": "Q?", "options": ["A", "B", "C", "D"], "correct": 0, "explanation": ""}
    assert validate_question(q) is False


# --- normalize_quiz_questions tests ---

def test_normalize_basic_questions():
    """Standard format should normalize cleanly."""
    raw = [
        {
            "question": "What percentage of enterprises will use AI agents by 2028?",
            "options": ["25%", "50%", "75%", "90%"],
            "correct": 2,
            "explanation": "Gartner projects 75% of enterprises will deploy AI agents by 2028.",
        },
        {
            "question": "Which company released the first AI agent framework?",
            "options": ["Google", "OpenAI", "LangChain", "Anthropic"],
            "correct": 2,
            "explanation": "LangChain was among the first widely adopted agent frameworks.",
        },
    ]
    questions = normalize_quiz_questions(raw, "test-topic")
    assert len(questions) == 2
    assert questions[0]["id"] == "test-topic-q1"
    assert questions[1]["id"] == "test-topic-q2"


def test_normalize_question_format():
    """Each normalized question should have all required fields with correct types."""
    raw = [
        {
            "question": "Test question?",
            "options": ["A", "B", "C", "D"],
            "correct": 1,
            "explanation": "B is correct.",
        },
    ]
    questions = normalize_quiz_questions(raw, "fmt-test")
    q = questions[0]

    assert isinstance(q["id"], str)
    assert isinstance(q["question"], str)
    assert isinstance(q["options"], list)
    assert isinstance(q["correct"], int)
    assert isinstance(q["explanation"], str)
    assert len(q["options"]) == 4
    assert 0 <= q["correct"] < len(q["options"])


def test_normalize_dict_wrapper():
    """Handle quiz wrapped in a dict with 'questions' key."""
    raw = {
        "questions": [
            {"question": "Q1?", "options": ["A", "B", "C", "D"], "correct": 0, "explanation": "A is correct."},
        ],
    }
    questions = normalize_quiz_questions(raw, "dict-test")
    assert len(questions) == 1
    assert questions[0]["question"] == "Q1?"


def test_normalize_nested_quiz_wrapper():
    """Handle quiz nested under quiz -> questions."""
    raw = {
        "quiz": {
            "questions": [
                {"question": "Nested?", "options": ["A", "B", "C", "D"], "correct": 3, "explanation": "D."},
            ],
        },
    }
    questions = normalize_quiz_questions(raw, "nested-test")
    assert len(questions) == 1
    assert questions[0]["correct"] == 3


def test_normalize_correct_as_text():
    """Handle correct answer specified as text instead of index."""
    raw = [
        {
            "question": "Capital of France?",
            "options": ["London", "Berlin", "Paris", "Rome"],
            "correct": "Paris",
            "explanation": "Paris is the capital of France.",
        },
    ]
    questions = normalize_quiz_questions(raw, "text-correct")
    assert len(questions) == 1
    assert questions[0]["correct"] == 2  # index of "Paris"


def test_normalize_strips_em_dashes():
    """Em dashes should be replaced in all text fields."""
    raw = [
        {
            "question": "What is AI \u2014 and why does it matter?",
            "options": ["Option A", "B \u2014 the best", "C \u2013 okay", "D"],
            "correct": 1,
            "explanation": "B is correct \u2014 obviously.",
        },
    ]
    questions = normalize_quiz_questions(raw, "dash-test")
    q = questions[0]
    assert "\u2014" not in q["question"]
    assert "\u2013" not in q["question"]
    assert "\u2014" not in q["explanation"]
    for opt in q["options"]:
        assert "\u2014" not in opt
        assert "\u2013" not in opt


def test_normalize_max_questions():
    """Should respect the max_questions limit."""
    raw = [
        {"question": f"Q{i}?", "options": ["A", "B", "C", "D"], "correct": 0, "explanation": "A."}
        for i in range(20)
    ]
    questions = normalize_quiz_questions(raw, "limit-test", max_questions=5)
    assert len(questions) == 5


def test_normalize_skips_incomplete():
    """Questions without proper options should be skipped."""
    raw = [
        {"question": "Good?", "options": ["A", "B", "C", "D"], "correct": 0, "explanation": "A."},
        {"question": "Bad?", "options": [], "correct": 0, "explanation": "none."},
        {"question": "No opts?", "correct": 0, "explanation": "none."},
        {"question": "One opt?", "options": ["A"], "correct": 0, "explanation": "A."},
    ]
    questions = normalize_quiz_questions(raw, "skip-test")
    assert len(questions) == 1
    assert questions[0]["question"] == "Good?"


def test_normalize_dict_options():
    """Handle options as dicts with text/label keys."""
    raw = [
        {
            "question": "Test?",
            "options": [
                {"text": "Alpha", "label": "A"},
                {"text": "Beta", "label": "B"},
                {"text": "Gamma", "label": "C"},
                {"text": "Delta", "label": "D"},
            ],
            "correct": 1,
            "explanation": "Beta.",
        },
    ]
    questions = normalize_quiz_questions(raw, "dict-opts")
    assert questions[0]["options"] == ["Alpha", "Beta", "Gamma", "Delta"]


def test_normalize_clamps_correct_index():
    """Correct index out of range should be clamped to valid range."""
    raw = [
        {"question": "Q?", "options": ["A", "B", "C", "D"], "correct": 99, "explanation": "Last."},
    ]
    questions = normalize_quiz_questions(raw, "clamp-test")
    assert questions[0]["correct"] == 3  # clamped to max valid index


def test_normalize_items_key():
    """Handle quiz data with 'items' key instead of 'questions'."""
    raw = {
        "items": [
            {"question": "Item Q?", "options": ["A", "B", "C", "D"], "correct": 0, "explanation": "A."},
        ],
    }
    questions = normalize_quiz_questions(raw, "items-test")
    assert len(questions) == 1
    assert questions[0]["question"] == "Item Q?"

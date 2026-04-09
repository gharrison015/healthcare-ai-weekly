"""Tests for learning_pipeline.py -- config loading, output schema validation, manifest generation."""

import json
import os
import tempfile

from learning.learning_pipeline import (
    load_config,
    get_topic_config,
    get_quiz_settings,
    run_cluster,
    run_write_output,
)


MOCK_CONFIG = {
    "notebook_id": "test-notebook-id",
    "topics": [
        {
            "slug": "ai-agents-101",
            "title": "AI Agents: What You Need to Know",
            "description": "Agents and agentic workflows",
            "accent_color": "#059669",
            "keywords": ["agent", "agentic", "autonomous"],
        },
        {
            "slug": "ai-safety-governance",
            "title": "AI Safety and Governance",
            "description": "Guardrails and risks",
            "accent_color": "#dc2626",
            "keywords": ["safety", "risk", "guardrail"],
        },
    ],
    "quiz": {
        "questions_per_topic": 10,
        "difficulty": "medium",
        "style": "trivia",
    },
}

MOCK_CONFIG_LEGACY = {
    "notebook_id": "test-notebook-id",
    "topic_clusters": {
        "ai-agents-101": {
            "title": "AI Agents: What You Need to Know",
            "description": "Agents and agentic workflows",
            "accent_color": "#059669",
            "keywords": ["agent", "agentic", "autonomous"],
        },
    },
    "quiz_settings": {
        "questions_per_topic": 5,
        "difficulty": "easy",
    },
}

MOCK_SOURCES = [
    {
        "source_id": "src-001",
        "title": "AI Agents Deep Dive",
        "type": "youtube",
        "guide": {
            "summary": "Comprehensive look at autonomous agent systems and agentic workflows.",
            "keywords": ["agent", "agentic", "autonomous"],
        },
    },
    {
        "source_id": "src-002",
        "title": "AI Safety Risks in 2026",
        "type": "youtube",
        "guide": {
            "summary": "Analysis of AI safety concerns including guardrails and risk mitigation.",
            "keywords": ["safety", "risk", "guardrail"],
        },
    },
]


def test_load_config():
    """Config loading should parse all expected fields."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(MOCK_CONFIG, f)
        tmp_path = f.name

    try:
        config = load_config(tmp_path)
        assert config["notebook_id"] == "test-notebook-id"
        assert len(config["topics"]) == 2
        assert config["quiz"]["difficulty"] == "medium"
    finally:
        os.unlink(tmp_path)


def test_get_topic_config_new_format():
    """get_topic_config should return topics list from new format."""
    topics = get_topic_config(MOCK_CONFIG)
    assert isinstance(topics, list)
    assert len(topics) == 2
    assert topics[0]["slug"] == "ai-agents-101"


def test_get_topic_config_legacy_format():
    """get_topic_config should return topic_clusters dict from legacy format."""
    topics = get_topic_config(MOCK_CONFIG_LEGACY)
    assert isinstance(topics, dict)
    assert "ai-agents-101" in topics


def test_get_quiz_settings_new_format():
    """get_quiz_settings should return 'quiz' key from new format."""
    settings = get_quiz_settings(MOCK_CONFIG)
    assert settings["questions_per_topic"] == 10
    assert settings["difficulty"] == "medium"


def test_get_quiz_settings_legacy_format():
    """get_quiz_settings should fall back to 'quiz_settings' key."""
    settings = get_quiz_settings(MOCK_CONFIG_LEGACY)
    assert settings["questions_per_topic"] == 5
    assert settings["difficulty"] == "easy"


def test_run_cluster_with_mock_sources():
    """Clustering stage should assign sources to correct topics."""
    clusters = run_cluster(MOCK_CONFIG, MOCK_SOURCES)

    assert "ai-agents-101" in clusters
    assert "ai-safety-governance" in clusters

    agent_ids = clusters["ai-agents-101"]["source_ids"]
    assert "src-001" in agent_ids

    safety_ids = clusters["ai-safety-governance"]["source_ids"]
    assert "src-002" in safety_ids


def test_run_write_output_creates_files():
    """Output stage should create topic JSON files and manifest."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = dict(MOCK_CONFIG)
        config["output"] = {
            "data_dir": tmpdir,
            "manifest_file": os.path.join(tmpdir, "manifest.json"),
        }

        clusters = {
            "ai-agents-101": {
                "slug": "ai-agents-101",
                "title": "AI Agents: What You Need to Know",
                "description": "Agents and agentic workflows",
                "accent_color": "#059669",
                "sources": [MOCK_SOURCES[0]],
                "source_ids": ["src-001"],
                "summary": "A summary about AI agents.",
                "quiz": {
                    "title": "Quick Check: AI Agents",
                    "questions": [
                        {
                            "id": "ai-agents-101-q1",
                            "question": "What is an AI agent?",
                            "options": ["A bot", "An autonomous system", "A chatbot", "A script"],
                            "correct": 1,
                            "explanation": "AI agents are autonomous systems that can use tools.",
                        },
                    ],
                },
            },
        }

        manifest = run_write_output(config, clusters)

        # Check topic file
        topic_path = os.path.join(tmpdir, "ai-agents-101.json")
        assert os.path.exists(topic_path)
        with open(topic_path) as f:
            topic_data = json.load(f)
        assert topic_data["slug"] == "ai-agents-101"
        assert topic_data["title"] == "AI Agents: What You Need to Know"
        assert len(topic_data["quiz"]["questions"]) == 1
        assert topic_data["sources"] == ["src-001"]

        # Check manifest
        manifest_path = os.path.join(tmpdir, "manifest.json")
        assert os.path.exists(manifest_path)
        with open(manifest_path) as f:
            manifest_data = json.load(f)
        assert manifest_data["topic_count"] == 1
        assert manifest_data["topics"][0]["slug"] == "ai-agents-101"
        assert manifest_data["topics"][0]["question_count"] == 1


def test_output_json_schema():
    """Verify the output JSON matches the expected schema from the design spec."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = dict(MOCK_CONFIG)
        config["output"] = {
            "data_dir": tmpdir,
            "manifest_file": os.path.join(tmpdir, "manifest.json"),
        }

        clusters = {
            "test-topic": {
                "slug": "test-topic",
                "title": "Test Topic",
                "description": "Test description",
                "accent_color": "#059669",
                "sources": [MOCK_SOURCES[0]],
                "source_ids": ["src-001"],
                "summary": "A test summary.",
                "quiz": {
                    "title": "Quick Check: Test",
                    "questions": [
                        {
                            "id": "test-topic-q1",
                            "question": "Test?",
                            "options": ["A", "B", "C", "D"],
                            "correct": 0,
                            "explanation": "A.",
                        },
                    ],
                },
            },
        }

        run_write_output(config, clusters)

        topic_path = os.path.join(tmpdir, "test-topic.json")
        with open(topic_path) as f:
            data = json.load(f)

        # Verify all required top-level fields from spec
        required_fields = ["slug", "title", "description", "accent_color",
                           "sources", "summary", "quiz", "created_at", "updated_at"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Verify quiz structure
        assert "title" in data["quiz"]
        assert "questions" in data["quiz"]
        assert isinstance(data["quiz"]["questions"], list)

        # Verify question structure
        q = data["quiz"]["questions"][0]
        q_fields = ["id", "question", "options", "correct", "explanation"]
        for field in q_fields:
            assert field in q, f"Missing question field: {field}"
        assert isinstance(q["options"], list)
        assert isinstance(q["correct"], int)


def test_manifest_schema():
    """Manifest should have generated_at, topic_count, and topics array."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = dict(MOCK_CONFIG)
        config["output"] = {
            "data_dir": tmpdir,
            "manifest_file": os.path.join(tmpdir, "manifest.json"),
        }

        clusters = {
            "t1": {
                "slug": "t1",
                "title": "Topic 1",
                "description": "Desc 1",
                "accent_color": "#059669",
                "sources": [MOCK_SOURCES[0]],
                "source_ids": ["src-001"],
                "summary": "Summary 1.",
                "quiz": {"title": "Quick Check: T1", "questions": []},
            },
            "t2": {
                "slug": "t2",
                "title": "Topic 2",
                "description": "Desc 2",
                "accent_color": "#dc2626",
                "sources": [MOCK_SOURCES[1]],
                "source_ids": ["src-002"],
                "summary": "Summary 2.",
                "quiz": {"title": "Quick Check: T2", "questions": []},
            },
        }

        manifest = run_write_output(config, clusters)

        assert "generated_at" in manifest
        assert manifest["topic_count"] == 2
        assert len(manifest["topics"]) == 2

        # Each manifest topic entry should have these fields
        for t in manifest["topics"]:
            assert "slug" in t
            assert "title" in t
            assert "description" in t
            assert "accent_color" in t
            assert "source_count" in t
            assert "question_count" in t

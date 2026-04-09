"""Tests for topic_clusterer.py -- keyword scoring, source assignment, edge cases."""

from learning.topic_clusterer import (
    score_source_for_topic,
    cluster_sources,
    build_topic_config_dict,
)


MOCK_SOURCES = [
    {
        "source_id": "src-001",
        "title": "How AI Agents Are Changing Sales",
        "type": "youtube",
        "guide": {
            "summary": "Explores agentic workflows and autonomous AI systems in enterprise sales pipelines.",
            "keywords": ["agent", "agentic", "autonomous", "workflow", "sales"],
        },
    },
    {
        "source_id": "src-002",
        "title": "AI Safety: The Risks We Need to Talk About",
        "type": "youtube",
        "guide": {
            "summary": "Deep dive into AI safety risks including alignment, blackmail scenarios, and guardrails.",
            "keywords": ["safety", "risk", "alignment", "guardrail", "regulation"],
        },
    },
    {
        "source_id": "src-003",
        "title": "ChatGPT for Healthcare: Clinical Applications",
        "type": "web",
        "guide": {
            "summary": "Overview of clinical AI applications including diagnostic support and patient triage.",
            "keywords": ["healthcare", "clinical", "diagnostic", "patient", "ChatGPT"],
        },
    },
    {
        "source_id": "src-004",
        "title": "AI in Your Daily Work: Productivity Tips",
        "type": "youtube",
        "guide": {
            "summary": "Practical guide to using AI tools for workplace productivity and skill development.",
            "keywords": ["productivity", "workplace", "skill", "career", "tools"],
        },
    },
    {
        "source_id": "src-005",
        "title": "Should Your Company Build or Buy AI?",
        "type": "youtube",
        "guide": {
            "summary": "Strategic analysis for leaders evaluating AI vendor solutions vs custom builds.",
            "keywords": ["strategy", "leader", "vendor", "build", "buy", "ROI"],
        },
    },
    {
        "source_id": "src-006",
        "title": "Multi-Agent Systems Explained",
        "type": "youtube",
        "guide": {
            "summary": "How multi-agent architectures enable complex autonomous task completion.",
            "keywords": ["agent", "multi-agent", "autonomous", "tool use"],
        },
    },
]

# Dict-keyed format (legacy/test)
TOPIC_CONFIG_DICT = {
    "ai-agents-101": {
        "title": "AI Agents: What You Need to Know",
        "description": "Agents and agentic workflows",
        "accent_color": "#059669",
        "keywords": ["agent", "agentic", "autonomous", "workflow", "tool use", "multi-agent"],
    },
    "ai-safety-governance": {
        "title": "AI Safety and Governance",
        "description": "Guardrails and risks",
        "accent_color": "#dc2626",
        "keywords": ["safety", "risk", "governance", "guardrail", "alignment", "blackmail", "regulation"],
    },
    "ai-in-the-workplace": {
        "title": "AI in the Workplace",
        "description": "Productivity and hiring",
        "accent_color": "#7c3aed",
        "keywords": ["productivity", "workplace", "hiring", "job", "skill", "career", "obsolescence"],
    },
    "healthcare-ai": {
        "title": "AI in Healthcare",
        "description": "Clinical applications",
        "accent_color": "#0284c7",
        "keywords": ["healthcare", "clinical", "diagnostic", "patient", "medical", "health system", "EHR"],
    },
    "ai-strategy-for-leaders": {
        "title": "AI Strategy for Leaders",
        "description": "Build vs buy decisions",
        "accent_color": "#d97706",
        "keywords": ["strategy", "leader", "executive", "vendor", "build", "buy", "ROI", "adoption"],
    },
}

# Array format (new config style)
TOPIC_CONFIG_LIST = [
    {"slug": "ai-agents-101", "title": "AI Agents: What You Need to Know", "description": "Agents and agentic workflows", "accent_color": "#059669", "keywords": ["agent", "agentic", "autonomous", "workflow", "tool use", "multi-agent"]},
    {"slug": "ai-safety-governance", "title": "AI Safety and Governance", "description": "Guardrails and risks", "accent_color": "#dc2626", "keywords": ["safety", "risk", "governance", "guardrail", "alignment", "blackmail", "regulation"]},
    {"slug": "healthcare-ai", "title": "AI in Healthcare", "description": "Clinical applications", "accent_color": "#0284c7", "keywords": ["healthcare", "clinical", "diagnostic", "patient", "medical", "health system", "EHR"]},
]


# --- Scoring tests ---

def test_score_source_for_topic_high_match():
    """Source about agents should score high for agents topic."""
    source = MOCK_SOURCES[0]
    keywords = TOPIC_CONFIG_DICT["ai-agents-101"]["keywords"]
    score = score_source_for_topic(source, keywords)
    assert score >= 0.3, f"Expected high score for agents source, got {score}"


def test_score_source_for_topic_low_match():
    """Source about safety should score low for agents topic."""
    source = MOCK_SOURCES[1]
    keywords = TOPIC_CONFIG_DICT["ai-agents-101"]["keywords"]
    score = score_source_for_topic(source, keywords)
    assert score < 0.2, f"Expected low score for safety source vs agents, got {score}"


def test_score_source_empty_keywords():
    """Empty keywords list should return 0."""
    score = score_source_for_topic(MOCK_SOURCES[0], [])
    assert score == 0.0


def test_score_source_string_guide():
    """Should handle guide as a plain string (not dict)."""
    source = {
        "source_id": "src-x",
        "title": "Test",
        "guide": "This covers agent workflows and autonomous systems.",
    }
    score = score_source_for_topic(source, ["agent", "autonomous", "workflow"])
    assert score > 0.5


def test_score_source_no_guide():
    """Source with no guide should still score based on title."""
    source = {
        "source_id": "src-y",
        "title": "AI agent workflows for enterprise",
        "guide": None,
    }
    score = score_source_for_topic(source, ["agent", "workflow"])
    assert score > 0.0


def test_score_source_key_topics_field():
    """Should also check the key_topics field in guide."""
    source = {
        "source_id": "src-z",
        "title": "Test",
        "guide": {
            "summary": "Generic overview.",
            "keywords": [],
            "key_topics": ["autonomous agents", "multi-agent systems"],
        },
    }
    score = score_source_for_topic(source, ["agent", "multi-agent", "autonomous"])
    assert score > 0.3


# --- Clustering tests ---

def test_cluster_sources_assigns_correctly():
    """Each mock source should land in the expected cluster."""
    clusters = cluster_sources(MOCK_SOURCES, TOPIC_CONFIG_DICT)

    agent_ids = clusters["ai-agents-101"]["source_ids"]
    assert "src-001" in agent_ids
    assert "src-006" in agent_ids

    safety_ids = clusters["ai-safety-governance"]["source_ids"]
    assert "src-002" in safety_ids

    health_ids = clusters["healthcare-ai"]["source_ids"]
    assert "src-003" in health_ids


def test_cluster_sources_no_empty_clusters():
    """Clearly-matched topics should appear as clusters."""
    clusters = cluster_sources(MOCK_SOURCES, TOPIC_CONFIG_DICT)
    assert "ai-agents-101" in clusters
    assert "ai-safety-governance" in clusters
    assert "healthcare-ai" in clusters


def test_cluster_sources_preserves_metadata():
    """Cluster output should carry through title, description, accent_color."""
    clusters = cluster_sources(MOCK_SOURCES, TOPIC_CONFIG_DICT)
    for slug, cluster in clusters.items():
        assert "title" in cluster
        assert "description" in cluster
        assert "accent_color" in cluster
        assert "source_ids" in cluster
        assert "sources" in cluster
        assert cluster["slug"] == slug


def test_cluster_every_source_assigned():
    """Every source should end up in some cluster (no sources dropped)."""
    clusters = cluster_sources(MOCK_SOURCES, TOPIC_CONFIG_DICT)
    all_assigned = set()
    for cluster in clusters.values():
        all_assigned.update(cluster["source_ids"])
    all_source_ids = {s["source_id"] for s in MOCK_SOURCES}
    assert all_source_ids == all_assigned, f"Unassigned: {all_source_ids - all_assigned}"


def test_cluster_with_list_config():
    """Clustering should work with the new array-based topic config format."""
    clusters = cluster_sources(MOCK_SOURCES, TOPIC_CONFIG_LIST)
    assert "ai-agents-101" in clusters
    assert "healthcare-ai" in clusters


# --- build_topic_config_dict tests ---

def test_build_topic_config_dict_from_list():
    """Should convert list format to dict keyed by slug."""
    result = build_topic_config_dict(TOPIC_CONFIG_LIST)
    assert isinstance(result, dict)
    assert "ai-agents-101" in result
    assert "healthcare-ai" in result
    assert result["ai-agents-101"]["title"] == "AI Agents: What You Need to Know"


def test_build_topic_config_dict_from_dict():
    """Should pass through dict format unchanged."""
    result = build_topic_config_dict(TOPIC_CONFIG_DICT)
    assert result is TOPIC_CONFIG_DICT

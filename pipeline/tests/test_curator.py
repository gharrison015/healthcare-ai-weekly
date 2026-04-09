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

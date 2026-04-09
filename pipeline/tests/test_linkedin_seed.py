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

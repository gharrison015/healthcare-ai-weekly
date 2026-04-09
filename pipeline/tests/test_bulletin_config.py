import json
import os


def _load_config():
    config_path = os.path.join(os.path.dirname(__file__), "..", "bulletin", "bulletin_config.json")
    with open(config_path) as f:
        return json.load(f)


def test_config_loads():
    config = _load_config()
    assert isinstance(config, dict)


def test_config_has_sources_section():
    config = _load_config()
    assert "sources" in config
    assert isinstance(config["sources"], dict)


def test_config_has_all_source_types():
    config = _load_config()
    sources = config["sources"]
    assert "x" in sources
    assert "bluesky" in sources
    assert "reddit" in sources
    assert "hackernews" in sources
    assert "newsdata" in sources


def test_config_x_has_accounts():
    config = _load_config()
    x = config["sources"]["x"]
    assert "accounts" in x
    assert len(x["accounts"]) > 0
    assert "EricTopol" in x["accounts"]
    assert "AnthropicAI" in x["accounts"]


def test_config_x_has_keywords():
    config = _load_config()
    x = config["sources"]["x"]
    assert "keywords" in x
    assert "healthcare AI" in x["keywords"]


def test_config_x_has_hashtags():
    config = _load_config()
    x = config["sources"]["x"]
    assert "hashtags" in x
    assert "healthcareAI" in x["hashtags"]


def test_config_bluesky_has_keywords():
    config = _load_config()
    assert "keywords" in config["sources"]["bluesky"]


def test_config_reddit_has_subreddits():
    config = _load_config()
    reddit = config["sources"]["reddit"]
    assert "subreddits" in reddit
    assert "MachineLearning" in reddit["subreddits"]
    assert "HealthIT" in reddit["subreddits"]


def test_config_has_verification_section():
    config = _load_config()
    assert "verification" in config
    v = config["verification"]
    assert isinstance(v, dict)


def test_config_verification_values():
    config = _load_config()
    v = config["verification"]
    assert v["min_independent_sources"] == 2
    assert v["min_unique_authors"] == 3
    assert v["min_platforms"] == 2
    assert v["hours_back"] == 24


def test_config_has_big_ticket_keywords():
    config = _load_config()
    kws = config["verification"]["big_ticket_keywords"]
    assert isinstance(kws, list)
    assert "FDA" in kws
    assert "acquisition" in kws
    assert "breach" in kws


def test_config_has_limits():
    config = _load_config()
    assert "limits" in config
    limits = config["limits"]
    assert limits["max_bulletins_per_day"] == 3
    assert limits["cooldown_hours"] == 6


def test_config_all_sources_have_enabled_flag():
    config = _load_config()
    for name, source in config["sources"].items():
        assert "enabled" in source, f"Source '{name}' missing 'enabled' flag"


def test_config_accounts_no_at_signs():
    """Account names should be bare usernames, no @ prefix."""
    config = _load_config()
    for account in config["sources"]["x"]["accounts"]:
        assert not account.startswith("@"), f"Account '{account}' should not start with @"


def test_config_valid_json_roundtrip():
    """Config should survive JSON serialization roundtrip."""
    config = _load_config()
    roundtripped = json.loads(json.dumps(config))
    assert roundtripped == config

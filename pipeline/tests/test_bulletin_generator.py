import json
import os
import tempfile

from bulletin.bulletin_generator import slugify, strip_em_dashes, save_bulletin


def test_slugify_basic():
    assert slugify("Claude Mythos Is Finding Real Vulnerabilities") == "claude-mythos-is-finding-real-vulnerabilities"


def test_slugify_special_chars():
    assert slugify("FDA's AI Clearance: A Big Deal!") == "fdas-ai-clearance-a-big-deal"


def test_slugify_truncates():
    long_headline = "A" * 100
    slug = slugify(long_headline)
    assert len(slug) <= 60


def test_slugify_strips_trailing_hyphens():
    slug = slugify("test - ")
    assert not slug.endswith("-")


def test_slugify_collapses_hyphens():
    slug = slugify("hello   world   test")
    assert "--" not in slug


def test_slugify_lowercase():
    slug = slugify("ALL CAPS HEADLINE")
    assert slug == slug.lower()


def test_strip_em_dashes_unicode():
    assert "\u2014" not in strip_em_dashes("hello \u2014 world")
    assert "\u2013" not in strip_em_dashes("hello \u2013 world")


def test_strip_em_dashes_ascii():
    result = strip_em_dashes("hello -- world")
    assert " -- " not in result


def test_strip_em_dashes_preserves_clean():
    clean = "This is clean text, no dashes here."
    assert strip_em_dashes(clean) == clean


def test_strip_em_dashes_replaces_with_comma():
    result = strip_em_dashes("first \u2014 second")
    assert "," in result


def test_strip_em_dashes_multiple():
    result = strip_em_dashes("a \u2014 b \u2013 c -- d")
    assert "\u2014" not in result
    assert "\u2013" not in result
    assert "--" not in result


def test_save_bulletin_creates_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        bulletin = {
            "timestamp": "2026-04-08T14:00:00+00:00",
            "slug": "test-bulletin",
            "headline": "Test Bulletin Headline",
            "body": "This is the body of the test bulletin.",
            "source_url": "https://example.com",
            "source_name": "Example",
            "velocity_score": 75,
            "verification": "auto_publish",
            "tags": ["test"],
        }
        filepath = save_bulletin(bulletin, tmpdir)
        assert os.path.exists(filepath)
        assert filepath.endswith(".json")

        with open(filepath) as f:
            saved = json.load(f)
        assert saved["headline"] == "Test Bulletin Headline"
        assert saved["slug"] == "test-bulletin"


def test_save_bulletin_creates_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        nested = os.path.join(tmpdir, "nested", "dir")
        bulletin = {"slug": "test", "headline": "Test", "body": "Body", "tags": []}
        filepath = save_bulletin(bulletin, nested)
        assert os.path.exists(filepath)


def test_save_bulletin_filename_format():
    with tempfile.TemporaryDirectory() as tmpdir:
        bulletin = {"slug": "my-test-slug", "headline": "Test", "body": "Body", "tags": []}
        filepath = save_bulletin(bulletin, tmpdir)
        filename = os.path.basename(filepath)
        assert "my-test-slug" in filename
        assert filename.endswith(".json")


def test_bulletin_json_structure():
    """Verify the expected JSON structure of a bulletin."""
    bulletin = {
        "timestamp": "2026-04-08T14:00:00+00:00",
        "slug": "claude-mythos-security",
        "headline": "Claude Mythos Is Finding Real Security Vulnerabilities",
        "body": "Three sentences here. They are punchy. They matter.",
        "source_url": "https://anthropic.com/blog/mythos",
        "source_name": "Anthropic Blog",
        "velocity_score": 87,
        "verification": "confirmed",
        "tags": ["anthropic", "security", "model-release"],
    }

    required_keys = [
        "timestamp", "slug", "headline", "body",
        "source_url", "source_name", "velocity_score",
        "verification", "tags",
    ]
    for key in required_keys:
        assert key in bulletin, f"Missing required key: {key}"

    assert isinstance(bulletin["tags"], list)
    assert isinstance(bulletin["velocity_score"], int)
    assert len(bulletin["body"]) > 0
    assert len(bulletin["headline"]) > 0

    # No em dashes allowed
    assert "\u2014" not in bulletin["body"]
    assert "\u2014" not in bulletin["headline"]
    assert "--" not in bulletin["body"]


def test_bulletin_tags_are_lowercase():
    """Tags should be lowercase for consistent topic tracking."""
    tags = ["anthropic", "security", "model-release"]
    for tag in tags:
        assert tag == tag.lower()

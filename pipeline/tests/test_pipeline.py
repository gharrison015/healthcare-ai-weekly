from pipeline import compute_date_range, get_data_paths

def test_compute_date_range_for_friday():
    date_str = "2026-04-04"
    start, end, display = compute_date_range(date_str)
    assert start == "2026-03-28"
    assert end == "2026-04-04"
    assert "March 28" in display or "March 30" in display or "April 4" in display

def test_get_data_paths():
    paths = get_data_paths("2026-04-04")
    assert paths["raw"] == "data/raw/2026-04-04.json"
    assert paths["curated"] == "data/curated/2026-04-04.json"
    assert paths["delta"] == "data/curated/2026-04-04-delta.json"
    assert "2026-04-04" in paths["issue_dir"]

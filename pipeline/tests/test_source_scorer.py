from collector.source_scorer import update_scores, get_keyword_threshold

def test_update_scores_initializes_new_source():
    scores = {}
    collected = [{"source": "Fierce Healthcare"}, {"source": "Fierce Healthcare"}, {"source": "NVIDIA Blog"}]
    curated_sources = ["Fierce Healthcare"]

    updated = update_scores(scores, collected, curated_sources)
    assert updated["Fierce Healthcare"]["articles_collected"] == 2
    assert updated["Fierce Healthcare"]["articles_curated"] == 1
    assert updated["Fierce Healthcare"]["weeks_tracked"] == 1
    assert updated["NVIDIA Blog"]["articles_collected"] == 1
    assert updated["NVIDIA Blog"]["articles_curated"] == 0

def test_update_scores_accumulates():
    scores = {
        "Fierce Healthcare": {"articles_collected": 10, "articles_curated": 6, "hit_rate": 0.6, "weeks_tracked": 5}
    }
    collected = [{"source": "Fierce Healthcare"}, {"source": "Fierce Healthcare"}]
    curated_sources = ["Fierce Healthcare"]

    updated = update_scores(scores, collected, curated_sources)
    assert updated["Fierce Healthcare"]["articles_collected"] == 12
    assert updated["Fierce Healthcare"]["articles_curated"] == 7
    assert updated["Fierce Healthcare"]["weeks_tracked"] == 6

def test_keyword_threshold_default_before_8_weeks():
    scores = {"Fierce Healthcare": {"hit_rate": 0.01, "weeks_tracked": 5}}
    assert get_keyword_threshold("Fierce Healthcare", scores) == 1

def test_keyword_threshold_tighter_for_low_hit_rate_after_8_weeks():
    scores = {"NVIDIA Blog": {"hit_rate": 0.05, "weeks_tracked": 10}}
    assert get_keyword_threshold("NVIDIA Blog", scores) == 2

def test_keyword_threshold_looser_for_high_hit_rate_after_8_weeks():
    scores = {"Fierce Healthcare": {"hit_rate": 0.55, "weeks_tracked": 10}}
    assert get_keyword_threshold("Fierce Healthcare", scores) == 1

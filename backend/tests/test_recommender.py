from modules.recommender import Recommender
from modules.shade_comparison import delta_e_cie76, delta_e_ciede2000


def test_delta_e_is_zero_for_identical_colors():
    assert delta_e_cie76("#c8a07a", "#c8a07a") == 0
    assert delta_e_ciede2000("#c8a07a", "#c8a07a") == 0


def test_recommender_returns_explainable_ranked_matches():
    recommender = Recommender()
    skin_data = {
        "hex_color": "#C8A07A",
        "luminance": 165,
        "undertone": "warm",
        "confidence": 0.9,
    }
    intent = {
        "finish": "matte",
        "coverage": "medium",
    }

    results = recommender.recommend(skin_data, intent, top_n=3, product_type="foundation")

    assert len(results) > 0
    assert results[0]["match_percentage"] == 100
    assert "score_breakdown" in results[0]
    assert "shade" in results[0]["score_breakdown"]
    assert "recommendation_explanation" in results[0]


def test_feedback_prior_changes_score_breakdown():
    recommender = Recommender()
    product_id = recommender.products[0]["id"]
    recommender.feedback_stats = {
        product_id: {
            "count": 3,
            "avg_rating": 5.0,
            "good_match_rate": 1.0,
            "issues": {},
        }
    }

    score, explanation = recommender._score_feedback_prior(recommender.products[0])

    assert score > 0
    assert "feedback" in explanation

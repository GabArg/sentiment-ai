from __future__ import annotations

from src.router_evaluation import MARGIN_THRESHOLDS, evaluate_router_strategies


def test_router_evaluation_reports_baseline_and_all_margin_candidates(predictor):
    strategies, details = evaluate_router_strategies(predictor)
    assert len(details) == 60
    assert len(strategies) == len(MARGIN_THRESHOLDS) + 1
    assert strategies[0]["strategy"] == "confidence_lt_0.80"
    required = {
        "review_count",
        "review_coverage_percentage",
        "local_errors_captured",
        "local_errors_missed",
        "local_correct_sent_to_review",
        "router_error_precision",
    }
    assert required.issubset(strategies[0])
    assert all(item["local_errors_captured"] + item["local_errors_missed"] == 29 for item in strategies)

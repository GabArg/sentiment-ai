"""Offline evaluation of uncertainty-router strategies on the exploratory benchmark."""

from __future__ import annotations

import json

import pandas as pd

from src.evaluation import evaluate_benchmark, load_benchmark
from src.model import PredictionObservability, SentimentPredictor
from src.review_router import ReviewRouterConfig, route_prediction


MARGIN_THRESHOLDS = (0.05, 0.10, 0.15, 0.20, 0.25, 0.30)


def evaluate_router_strategies(predictor: SentimentPredictor) -> tuple[list[dict[str, object]], pd.DataFrame]:
    _, details = evaluate_benchmark(predictor, load_benchmark())
    strategies = [("confidence_lt_0.80", None)] + [
        (f"confidence_lt_0.80_or_margin_lt_{margin:.2f}", margin)
        for margin in MARGIN_THRESHOLDS
    ]
    results = []
    total_errors = int((~details["is_correct"]).sum())
    for name, margin in strategies:
        reviewed = []
        for row in details.itertuples():
            observation = PredictionObservability(
                local_prediction=row.local_prediction,
                local_confidence=row.local_confidence,
                second_best_class=row.second_best_class,
                second_best_probability=row.second_best_probability,
                prediction_margin=row.prediction_margin,
            )
            reviewed.append(
                route_prediction(
                    observation,
                    ReviewRouterConfig(confidence_threshold=0.80, margin_threshold=margin),
                ).should_review
            )
        reviewed_series = pd.Series(reviewed, index=details.index)
        captured = int((reviewed_series & ~details["is_correct"]).sum())
        unnecessary = int((reviewed_series & details["is_correct"]).sum())
        review_count = int(reviewed_series.sum())
        results.append(
            {
                "strategy": name,
                "review_count": review_count,
                "review_coverage_percentage": review_count / len(details) * 100,
                "local_errors_captured": captured,
                "local_errors_missed": total_errors - captured,
                "local_correct_sent_to_review": unnecessary,
                "router_error_precision": captured / review_count if review_count else 0.0,
            }
        )
    return results, details


def main() -> None:
    strategies, _ = evaluate_router_strategies(SentimentPredictor.load())
    print(json.dumps({"exploratory_benchmark": True, "strategies": strategies}, indent=2))


if __name__ == "__main__":
    main()

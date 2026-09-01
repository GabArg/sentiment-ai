"""Experimental hybrid orchestration; never replaces public local inference."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd

from src.model import SentimentPredictor
from src.review_router import ReviewDecision, ReviewRouterConfig, route_prediction
from src.sentiment_review import ReviewResult, SentimentReviewProvider


@dataclass(frozen=True)
class HybridPrediction:
    local_prediction: str
    local_confidence: float
    local_margin: float
    review_requested: bool
    review_reasons: tuple[str, ...]
    second_check_prediction: str | None
    hybrid_prediction: str
    provider_status: str
    state: str
    review_result: ReviewResult | None


def evaluate_hybrid_text(
    text: str,
    predictor: SentimentPredictor,
    config: ReviewRouterConfig = ReviewRouterConfig(),
    provider: SentimentReviewProvider | None = None,
    additional_signals: Iterable[str] = (),
) -> HybridPrediction:
    observation = predictor.observe_one(text)
    decision: ReviewDecision = route_prediction(observation, config, additional_signals)
    if not decision.should_review:
        return HybridPrediction(
            local_prediction=observation.local_prediction,
            local_confidence=observation.local_confidence,
            local_margin=observation.prediction_margin,
            review_requested=False,
            review_reasons=(),
            second_check_prediction=None,
            hybrid_prediction=observation.local_prediction,
            provider_status="not_requested",
            state="local_only",
            review_result=None,
        )

    if provider is None:
        return _fallback(observation.local_prediction, observation.local_confidence, observation.prediction_margin, decision, None, "unavailable")

    result = provider.review_sentiment(text)
    if not result.success:
        return _fallback(observation.local_prediction, observation.local_confidence, observation.prediction_margin, decision, result, result.error_code or "provider_error")

    disagrees = result.sentiment != observation.local_prediction
    return HybridPrediction(
        local_prediction=observation.local_prediction,
        local_confidence=observation.local_confidence,
        local_margin=observation.prediction_margin,
        review_requested=True,
        review_reasons=decision.reasons,
        second_check_prediction=result.sentiment,
        hybrid_prediction=result.sentiment or observation.local_prediction,
        provider_status="reviewed",
        state="disagreement" if disagrees else "reviewed",
        review_result=result,
    )


def evaluate_hybrid_benchmark(
    benchmark: pd.DataFrame,
    predictor: SentimentPredictor,
    config: ReviewRouterConfig = ReviewRouterConfig(),
    provider: SentimentReviewProvider | None = None,
) -> pd.DataFrame:
    """Record local versus experimental hybrid outcomes for each labeled case."""
    required = {"text", "expected_sentiment"}
    if not required.issubset(benchmark.columns):
        raise ValueError("Benchmark must include text and expected_sentiment.")
    records = []
    for row in benchmark.itertuples(index=False):
        result = evaluate_hybrid_text(row.text, predictor, config, provider)
        records.append(
            {
                "text": row.text,
                "expected": row.expected_sentiment,
                "local_prediction": result.local_prediction,
                "local_confidence": result.local_confidence,
                "local_margin": result.local_margin,
                "review_requested": result.review_requested,
                "review_reasons": "|".join(result.review_reasons),
                "second_check_prediction": result.second_check_prediction,
                "hybrid_prediction": result.hybrid_prediction,
                "local_correct": result.local_prediction == row.expected_sentiment,
                "hybrid_correct": result.hybrid_prediction == row.expected_sentiment,
                "provider_status": result.provider_status,
                "state": result.state,
            }
        )
    return pd.DataFrame.from_records(records)


def _fallback(local_prediction: str, confidence: float, margin: float, decision: ReviewDecision, result: ReviewResult | None, status: str) -> HybridPrediction:
    return HybridPrediction(
        local_prediction=local_prediction,
        local_confidence=confidence,
        local_margin=margin,
        review_requested=True,
        review_reasons=decision.reasons,
        second_check_prediction=None,
        hybrid_prediction=local_prediction,
        provider_status=status,
        state="fallback_local",
        review_result=result,
    )

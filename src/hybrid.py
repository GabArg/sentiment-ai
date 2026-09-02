"""Experimental hybrid orchestration; never replaces public local inference."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Iterable

import pandas as pd

from src.model import SentimentPredictor
from src.review_router import ReviewDecision, ReviewRouterConfig, route_prediction
from src.sentiment_review import ReviewResult, SentimentReviewProvider


ALLOWED_REVIEW_STATES = frozenset(
    {"local_only", "review_requested", "reviewed", "disagreement", "fallback_local"}
)


@dataclass(frozen=True)
class HybridPrediction:
    final_prediction: str
    local_prediction: str
    local_confidence: float
    local_margin: float
    review_requested: bool
    review_reasons: tuple[str, ...]
    review_state: str
    review_prediction: str | None
    review_provider: str | None
    review_model: str | None
    review_latency_ms: float | None
    fallback_used: bool
    error_code: str | None
    review_result: ReviewResult | None

    def __post_init__(self) -> None:
        if self.review_state not in ALLOWED_REVIEW_STATES:
            raise ValueError("Unsupported hybrid review state.")

    @property
    def hybrid_prediction(self) -> str:
        return self.final_prediction

    @property
    def second_check_prediction(self) -> str | None:
        return self.review_prediction

    @property
    def state(self) -> str:
        return self.review_state

    @property
    def provider_status(self) -> str:
        if self.review_state == "local_only":
            return "not_requested"
        if self.review_state in {"reviewed", "disagreement"}:
            return "reviewed"
        return self.error_code or "provider_error"


def evaluate_hybrid_text(
    text: str,
    predictor: SentimentPredictor,
    config: ReviewRouterConfig = ReviewRouterConfig(),
    provider: SentimentReviewProvider | None = None,
    additional_signals: Iterable[str] = (),
) -> HybridPrediction:
    observation = predictor.observe_one(text)
    decision: ReviewDecision = route_prediction(observation, config, additional_signals)
    return evaluate_hybrid_observation(text, observation, decision, provider)


def evaluate_hybrid_observation(
    text: str,
    observation,
    decision: ReviewDecision,
    provider: SentimentReviewProvider | None,
) -> HybridPrediction:
    """Consolidate a precomputed local observation with an optional second check."""
    if not decision.should_review:
        return HybridPrediction(
            final_prediction=observation.local_prediction,
            local_prediction=observation.local_prediction,
            local_confidence=observation.local_confidence,
            local_margin=observation.prediction_margin,
            review_requested=False,
            review_reasons=(),
            review_state="local_only",
            review_prediction=None,
            review_provider=None,
            review_model=None,
            review_latency_ms=None,
            fallback_used=False,
            error_code=None,
            review_result=None,
        )

    if provider is None:
        return _fallback(observation.local_prediction, observation.local_confidence, observation.prediction_margin, decision, None, "unavailable", None)

    started = time.perf_counter()
    result = provider.review_sentiment(text)
    latency_ms = (time.perf_counter() - started) * 1000
    if not result.success:
        return _fallback(observation.local_prediction, observation.local_confidence, observation.prediction_margin, decision, result, result.error_code or "provider_error", latency_ms)

    disagrees = result.sentiment != observation.local_prediction
    return HybridPrediction(
        final_prediction=result.sentiment or observation.local_prediction,
        local_prediction=observation.local_prediction,
        local_confidence=observation.local_confidence,
        local_margin=observation.prediction_margin,
        review_requested=True,
        review_reasons=decision.reasons,
        review_state="disagreement" if disagrees else "reviewed",
        review_prediction=result.sentiment,
        review_provider=result.provider,
        review_model=result.model,
        review_latency_ms=latency_ms,
        fallback_used=False,
        error_code=None,
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


def fallback_for_budget(local_prediction: str, confidence: float, margin: float, decision: ReviewDecision) -> HybridPrediction:
    return _fallback(local_prediction, confidence, margin, decision, None, "review_budget_exceeded", None)


def _fallback(local_prediction: str, confidence: float, margin: float, decision: ReviewDecision, result: ReviewResult | None, status: str, latency_ms: float | None) -> HybridPrediction:
    return HybridPrediction(
        final_prediction=local_prediction,
        local_prediction=local_prediction,
        local_confidence=confidence,
        local_margin=margin,
        review_requested=True,
        review_reasons=decision.reasons,
        review_state="fallback_local",
        review_prediction=None,
        review_provider=result.provider if result else None,
        review_model=result.model if result else None,
        review_latency_ms=latency_ms,
        fallback_used=True,
        error_code=status,
        review_result=result,
    )

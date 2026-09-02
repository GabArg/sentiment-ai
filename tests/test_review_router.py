from __future__ import annotations

import pytest

from src.model import PredictionObservability
from src.review_router import (
    LANGUAGE_MISMATCH,
    LOW_CONFIDENCE,
    POSSIBLE_FACTUAL_NEUTRAL,
    SMALL_MARGIN,
    ReviewRouterConfig,
    route_prediction,
)


def observation(confidence: float, margin: float) -> PredictionObservability:
    return PredictionObservability("Negativo", confidence, "Neutro", confidence - margin, margin)


def test_historical_confidence_baseline_routes_below_80_percent():
    decision = route_prediction(observation(0.79, 0.50))
    assert decision.should_review
    assert decision.reasons == (LOW_CONFIDENCE,)


def test_historical_confidence_baseline_does_not_route_at_80_percent():
    decision = route_prediction(observation(0.80, 0.50))
    assert not decision.should_review
    assert decision.reasons == ()


def test_configurable_margin_routes_independently():
    decision = route_prediction(
        observation(0.90, 0.09),
        ReviewRouterConfig(confidence_threshold=0.80, margin_threshold=0.10),
    )
    assert decision.reasons == (SMALL_MARGIN,)


def test_router_preserves_multiple_auditable_reasons():
    decision = route_prediction(
        observation(0.70, 0.05),
        ReviewRouterConfig(margin_threshold=0.10),
        [POSSIBLE_FACTUAL_NEUTRAL, LANGUAGE_MISMATCH],
    )
    assert decision.reasons == (
        LOW_CONFIDENCE,
        SMALL_MARGIN,
        POSSIBLE_FACTUAL_NEUTRAL,
        LANGUAGE_MISMATCH,
    )


def test_unknown_signal_and_invalid_threshold_are_rejected():
    with pytest.raises(ValueError, match="Unsupported"):
        route_prediction(observation(0.90, 0.50), additional_signals=["weekday_rule"])
    with pytest.raises(ValueError, match="between 0 and 1"):
        ReviewRouterConfig(margin_threshold=1.1)


@pytest.mark.parametrize(
    ("local_class", "threshold"),
    [("Negativo", 0.80), ("Neutro", 0.65), ("Positivo", 0.80)],
)
def test_class_thresholds_use_strict_less_than(local_class, threshold):
    config = ReviewRouterConfig(
        confidence_threshold=None,
        class_thresholds={"Negativo": 0.80, "Neutro": 0.65, "Positivo": 0.80},
    )
    exact = PredictionObservability(local_class, threshold, "Neutro", 0.1, threshold - 0.1)
    below = PredictionObservability(local_class, threshold - 0.0001, "Neutro", 0.1, threshold - 0.1001)
    assert not route_prediction(exact, config).should_review
    decision = route_prediction(below, config)
    assert decision.should_review
    assert decision.reasons == (f"low_confidence:{local_class}<{threshold:.2f}",)

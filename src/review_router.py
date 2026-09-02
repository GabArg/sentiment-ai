"""Auditable uncertainty routing for experimental second checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from src.model import PredictionObservability


LOW_CONFIDENCE = "low_confidence"
SMALL_MARGIN = "small_margin"
POSSIBLE_FACTUAL_NEUTRAL = "possible_factual_neutral"
POSSIBLE_OUT_OF_DOMAIN = "possible_out_of_domain"
LANGUAGE_MISMATCH = "language_mismatch"
SUPPORTED_REASONS = frozenset(
    {
        LOW_CONFIDENCE,
        SMALL_MARGIN,
        POSSIBLE_FACTUAL_NEUTRAL,
        POSSIBLE_OUT_OF_DOMAIN,
        LANGUAGE_MISMATCH,
    }
)


@dataclass(frozen=True)
class ReviewRouterConfig:
    confidence_threshold: float | None = 0.80
    margin_threshold: float | None = None
    class_thresholds: Mapping[str, float] | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("confidence_threshold", self.confidence_threshold),
            ("margin_threshold", self.margin_threshold),
        ):
            if value is not None and not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1.")
        if self.class_thresholds is not None:
            expected = {"Negativo", "Neutro", "Positivo"}
            if set(self.class_thresholds) != expected:
                raise ValueError("class_thresholds must define Negativo, Neutro and Positivo.")
            if any(not 0 <= value <= 1 for value in self.class_thresholds.values()):
                raise ValueError("Class thresholds must be between 0 and 1.")

    def threshold_for(self, local_class: str) -> float | None:
        if self.class_thresholds is not None:
            return self.class_thresholds.get(local_class)
        return self.confidence_threshold


@dataclass(frozen=True)
class ReviewDecision:
    should_review: bool
    reasons: tuple[str, ...]
    local_confidence: float
    prediction_margin: float
    local_class: str
    second_best_class: str


def route_prediction(
    observation: PredictionObservability,
    config: ReviewRouterConfig = ReviewRouterConfig(),
    additional_signals: Iterable[str] = (),
) -> ReviewDecision:
    """Route only on configured numeric rules and explicit upstream signals."""
    reasons: list[str] = []
    confidence_threshold = config.threshold_for(observation.local_prediction)
    if confidence_threshold is not None and observation.local_confidence < confidence_threshold:
        reasons.append(
            f"{LOW_CONFIDENCE}:{observation.local_prediction}<{confidence_threshold:.2f}"
            if config.class_thresholds is not None
            else LOW_CONFIDENCE
        )
    if (
        config.margin_threshold is not None
        and observation.prediction_margin < config.margin_threshold
    ):
        reasons.append(SMALL_MARGIN)

    for signal in additional_signals:
        if signal not in SUPPORTED_REASONS:
            raise ValueError(f"Unsupported review reason: {signal}")
        if signal not in reasons:
            reasons.append(signal)

    return ReviewDecision(
        should_review=bool(reasons),
        reasons=tuple(reasons),
        local_confidence=observation.local_confidence,
        prediction_margin=observation.prediction_margin,
        local_class=observation.local_prediction,
        second_best_class=observation.second_best_class,
    )

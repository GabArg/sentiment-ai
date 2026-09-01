"""Opt-in configuration for controlled hybrid sentiment classification."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Mapping, Any

from src.review_router import ReviewRouterConfig


DEFAULT_REVIEW_COST_USD = 0.000178


def _value(name: str, secrets: Mapping[str, Any] | None, environ: Mapping[str, str]) -> Any:
    if secrets is not None:
        try:
            value = secrets.get(name)
        except Exception:
            value = None
        if value is not None:
            return value
    return environ.get(name)


def _boolean(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().casefold()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off", ""}:
        return False
    raise ValueError("ENABLE_HYBRID_SENTIMENT must be true or false.")


def _float(value: Any, default: float, name: str) -> float:
    result = default if value is None else float(value)
    if not 0 <= result <= 1:
        raise ValueError(f"{name} must be between 0 and 1.")
    return result


def _positive_int(value: Any, default: int, name: str) -> int:
    result = default if value is None else int(value)
    if result < 1:
        raise ValueError(f"{name} must be at least 1.")
    return result


@dataclass(frozen=True)
class HybridRoutingConfig:
    """Controlled, reversible settings; thresholds are exploratory, not calibrated."""

    enabled: bool = False
    negative_threshold: float = 0.80
    neutral_threshold: float = 0.65
    positive_threshold: float = 0.60
    max_reviews_per_batch: int = 25
    max_requests: int = 5
    window_seconds: float = 60.0
    pacing_margin_seconds: float = 0.25
    estimated_review_cost_usd: float = DEFAULT_REVIEW_COST_USD

    def __post_init__(self) -> None:
        if self.max_reviews_per_batch < 1 or self.max_requests < 1:
            raise ValueError("Hybrid limits must be at least 1.")
        if self.window_seconds <= 0 or self.pacing_margin_seconds < 0:
            raise ValueError("Invalid hybrid pacing window.")

    def router_config(self) -> ReviewRouterConfig:
        return ReviewRouterConfig(
            confidence_threshold=None,
            class_thresholds={
                "Negativo": self.negative_threshold,
                "Neutro": self.neutral_threshold,
                "Positivo": self.positive_threshold,
            },
        )


def load_hybrid_config(
    secrets: Mapping[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
) -> HybridRoutingConfig:
    values = os.environ if environ is None else environ
    return HybridRoutingConfig(
        enabled=_boolean(_value("ENABLE_HYBRID_SENTIMENT", secrets, values)),
        negative_threshold=_float(_value("HYBRID_THRESHOLD_NEGATIVE", secrets, values), 0.80, "HYBRID_THRESHOLD_NEGATIVE"),
        neutral_threshold=_float(_value("HYBRID_THRESHOLD_NEUTRAL", secrets, values), 0.65, "HYBRID_THRESHOLD_NEUTRAL"),
        positive_threshold=_float(_value("HYBRID_THRESHOLD_POSITIVE", secrets, values), 0.60, "HYBRID_THRESHOLD_POSITIVE"),
        max_reviews_per_batch=_positive_int(_value("HYBRID_MAX_REVIEWS_PER_BATCH", secrets, values), 25, "HYBRID_MAX_REVIEWS_PER_BATCH"),
        max_requests=_positive_int(_value("HYBRID_MAX_REQUESTS", secrets, values), 5, "HYBRID_MAX_REQUESTS"),
        window_seconds=float(_value("HYBRID_WINDOW_SECONDS", secrets, values) or 60.0),
    )

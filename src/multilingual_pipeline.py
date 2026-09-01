"""Controlled multilingual preparation and sentiment orchestration."""

from __future__ import annotations

from dataclasses import dataclass

from src.external_requests import ExternalRequestCoordinator
from src.hybrid import HybridPrediction, evaluate_hybrid_observation, fallback_for_budget
from src.hybrid_config import HybridRoutingConfig
from src.model import SentimentPredictor
from src.multilingual_contracts import (
    LanguageDetector,
    MultilingualPreparationResult,
    TranslationProvider,
)
from src.preprocessing import anonymize_text
from src.review_router import ReviewDecision, route_prediction
from src.sentiment_review import SentimentReviewProvider


@dataclass(frozen=True)
class MultilingualSentimentResult:
    preparation: MultilingualPreparationResult
    sentiment: HybridPrediction

    @property
    def final_sentiment(self) -> str:
        return self.sentiment.final_prediction


def prepare_analysis_text(
    original_text: str,
    enabled: bool,
    detector: LanguageDetector | None,
    translation_provider: TranslationProvider | None,
    coordinator: ExternalRequestCoordinator | None = None,
) -> MultilingualPreparationResult:
    if not enabled:
        return _preparation(original_text, None, None, False, False, "not_needed")
    if detector is None:
        return _preparation(original_text, None, None, False, False, "detection_error", error="unavailable")

    detection = detector.detect(original_text)
    if not detection.success:
        return _preparation(
            original_text, None, None, False, False, "detection_error", error=detection.error_code
        )
    if not detection.supported:
        return _preparation(
            original_text,
            detection.detected_language,
            detection.language_name,
            False,
            False,
            "unsupported_language",
        )
    if detection.detected_language == "es":
        return _preparation(original_text, "es", detection.language_name, True, False, "not_needed")

    if translation_provider is None or not bool(getattr(translation_provider, "api_key", True)):
        return _preparation(
            original_text,
            detection.detected_language,
            detection.language_name,
            True,
            True,
            "fallback_original",
            error="unavailable",
        )
    if coordinator is not None and not coordinator.acquire("translation"):
        return _preparation(
            original_text,
            detection.detected_language,
            detection.language_name,
            True,
            True,
            "fallback_original",
            error="external_budget_exceeded",
        )

    result = translation_provider.translate(
        anonymize_text(original_text), detection.detected_language or "", "es"
    )
    if not result.success:
        return _preparation(
            original_text,
            detection.detected_language,
            detection.language_name,
            True,
            True,
            "fallback_original",
            provider=result.provider,
            model=result.model,
            latency=result.latency_ms,
            error=result.error_code,
        )
    return _preparation(
        original_text,
        detection.detected_language,
        detection.language_name,
        True,
        True,
        "translated",
        translated=result.translated_text,
        provider=result.provider,
        model=result.model,
        latency=result.latency_ms,
        usage=result.usage,
    )


def evaluate_multilingual_sentiment(
    original_text: str,
    predictor: SentimentPredictor,
    multilingual_enabled: bool,
    detector: LanguageDetector | None,
    translation_provider: TranslationProvider | None,
    hybrid_config: HybridRoutingConfig,
    review_provider: SentimentReviewProvider | None,
    coordinator: ExternalRequestCoordinator | None = None,
) -> MultilingualSentimentResult:
    preparation = prepare_analysis_text(
        original_text, multilingual_enabled, detector, translation_provider, coordinator
    )
    observation = predictor.observe_one(preparation.analysis_text)
    if hybrid_config.enabled:
        decision = route_prediction(observation, hybrid_config.router_config())
    else:
        decision = ReviewDecision(
            False,
            (),
            observation.local_confidence,
            observation.prediction_margin,
            observation.local_prediction,
            observation.second_best_class,
        )

    if decision.should_review and review_provider is not None and bool(getattr(review_provider, "api_key", True)):
        if coordinator is not None and not coordinator.acquire("sentiment_review"):
            sentiment = fallback_for_budget(
                observation.local_prediction,
                observation.local_confidence,
                observation.prediction_margin,
                decision,
            )
        else:
            sentiment = evaluate_hybrid_observation(
                preparation.analysis_text, observation, decision, review_provider
            )
    else:
        sentiment = evaluate_hybrid_observation(
            preparation.analysis_text, observation, decision, review_provider
        )
    return MultilingualSentimentResult(preparation, sentiment)


def _preparation(
    original: str,
    language: str | None,
    language_name: str | None,
    supported: bool,
    requested: bool,
    state: str,
    translated: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    latency: float | None = None,
    error: str | None = None,
    usage: dict[str, int] | None = None,
) -> MultilingualPreparationResult:
    return MultilingualPreparationResult(
        original_text=original,
        detected_language=language,
        language_name=language_name,
        language_supported=supported,
        translation_requested=requested,
        translation_state=state,
        translated_text=translated,
        translation_provider=provider,
        translation_model=model,
        translation_latency_ms=latency,
        translation_error_code=error,
        analysis_text=translated if state == "translated" and translated is not None else original,
        translation_usage=usage,
    )

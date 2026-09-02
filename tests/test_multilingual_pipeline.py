from types import SimpleNamespace

import pytest

from src.external_requests import ExternalRequestCoordinator
from src.hybrid_config import HybridRoutingConfig
from src.model import PredictionObservability
from src.multilingual_contracts import LanguageDetectionResult, TranslationResult
from src.multilingual_pipeline import evaluate_multilingual_sentiment, prepare_analysis_text
from src.rate_pacer import RatePacer
from src.sentiment_review import ReviewResult


class Detector:
    def __init__(self, language="en", success=True, supported=True, status="detected"):
        self.language = language
        self.success = success
        self.supported = supported
        self.status = status

    def detect(self, _text):
        names = {"es": "Español", "en": "Inglés", "pt": "Portugués", "it": "Italiano"}
        return LanguageDetectionResult(
            self.language if self.success else None,
            names.get(self.language),
            self.supported,
            None,
            "mock",
            self.success,
            self.status,
            None if self.success else "detector_error",
        )


class Translator:
    api_key = "test"

    def __init__(self, success=True):
        self.success = success
        self.calls = []

    def translate(self, text, source_language, target_language="es"):
        self.calls.append((text, source_language, target_language))
        return TranslationResult(
            source_language,
            target_language,
            text,
            "servicio excelente" if self.success else None,
            "mock-translation",
            "mock-model",
            self.success,
            error_code=None if self.success else "timeout",
        )


class Predictor:
    def __init__(self, confidence=0.9):
        self.confidence = confidence
        self.seen = []

    def observe_one(self, text):
        self.seen.append(text)
        return PredictionObservability("Positivo", self.confidence, "Neutro", 0.08, self.confidence - 0.08)


class Reviewer:
    api_key = "test"

    def __init__(self):
        self.seen = []

    def review_sentiment(self, text):
        self.seen.append(text)
        return ReviewResult("Positivo", None, None, "mock-review", "mock-model", True)


@pytest.mark.parametrize("language", ["en", "pt", "it"])
def test_supported_non_spanish_languages_translate(language):
    translator = Translator()
    result = prepare_analysis_text("Great user@example.com", True, Detector(language), translator)
    assert result.translation_state == "translated" and result.analysis_text == "servicio excelente"
    assert "user@example.com" not in translator.calls[0][0] and "[EMAIL]" in translator.calls[0][0]


def test_multilingual_off_does_not_detect_or_translate():
    result = prepare_analysis_text("Original", False, None, None)
    assert result.analysis_text == "Original" and result.translation_state == "not_needed"


def test_spanish_does_not_translate():
    translator = Translator()
    result = prepare_analysis_text("Excelente", True, Detector("es"), translator)
    assert result.translation_state == "not_needed" and translator.calls == []


def test_translation_failure_falls_back_to_original():
    result = prepare_analysis_text("Very bad", True, Detector("en"), Translator(False))
    assert result.translation_state == "fallback_original" and result.analysis_text == "Very bad"
    assert result.translation_error_code == "timeout"


def test_unsupported_and_detection_error_preserve_original():
    unsupported = prepare_analysis_text("Hallo", True, Detector("de", supported=False, status="unsupported"), Translator())
    failed = prepare_analysis_text("Text", True, Detector(success=False, supported=False, status="error"), Translator())
    assert unsupported.translation_state == "unsupported_language" and unsupported.analysis_text == "Hallo"
    assert failed.translation_state == "detection_error" and failed.analysis_text == "Text"


def test_translation_budget_exhaustion_falls_back_without_call():
    translator = Translator()
    coordinator = ExternalRequestCoordinator(1, RatePacer(5, 60))
    assert coordinator.acquire("sentiment_review")
    result = prepare_analysis_text("Very good", True, Detector("en"), translator, coordinator)
    assert result.translation_error_code == "external_budget_exceeded" and translator.calls == []


def test_hybrid_off_uses_translated_text_locally_without_review():
    predictor, reviewer = Predictor(0.4), Reviewer()
    result = evaluate_multilingual_sentiment(
        "Very good", predictor, True, Detector("en"), Translator(), HybridRoutingConfig(enabled=False), reviewer
    )
    assert predictor.seen == ["servicio excelente"] and reviewer.seen == []
    assert result.sentiment.review_state == "local_only"


def test_hybrid_on_reviews_exact_same_analysis_text():
    predictor, reviewer = Predictor(0.4), Reviewer()
    result = evaluate_multilingual_sentiment(
        "Very good", predictor, True, Detector("en"), Translator(), HybridRoutingConfig(enabled=True), reviewer
    )
    assert predictor.seen == reviewer.seen == ["servicio excelente"]
    assert result.sentiment.review_state == "reviewed"


def test_review_budget_exhaustion_uses_local_fallback():
    coordinator = ExternalRequestCoordinator(1, RatePacer(5, 60))
    translator, reviewer = Translator(), Reviewer()
    result = evaluate_multilingual_sentiment(
        "Very good", Predictor(0.4), True, Detector("en"), translator,
        HybridRoutingConfig(enabled=True), reviewer, coordinator,
    )
    assert coordinator.calls == {"translation": 1}
    assert reviewer.seen == []
    assert result.sentiment.review_state == "fallback_local"
    assert result.sentiment.error_code == "review_budget_exceeded"

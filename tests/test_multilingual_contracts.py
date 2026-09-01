from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest

from src.multilingual_contracts import (
    LanguageDetectionResult,
    MultilingualPreparationResult,
    SUPPORTED_LANGUAGES,
    TranslationResult,
)


FIXTURE = Path(__file__).parent / "fixtures" / "multilingual_sentiment_benchmark.csv"


def test_multilingual_fixture_is_balanced_and_manually_labeled():
    benchmark = pd.read_csv(FIXTURE)

    assert len(benchmark) == 48
    assert set(benchmark.columns) == {"text", "expected_sentiment", "language", "category"}
    assert benchmark["text"].is_unique
    assert benchmark.groupby("language").size().to_dict() == {"en": 12, "es": 12, "it": 12, "pt": 12}
    assert benchmark.groupby(["language", "expected_sentiment"]).size().to_dict() == {
        (language, sentiment): 4
        for language in SUPPORTED_LANGUAGES
        for sentiment in ("Negativo", "Neutro", "Positivo")
    }


def test_supported_detection_contract():
    result = LanguageDetectionResult("en", "Inglés", True, None, "detector", True, "detected")

    assert result.supported
    assert result.confidence is None


def test_unsupported_and_error_detection_contracts():
    unsupported = LanguageDetectionResult("de", "Alemán", False, None, "detector", True, "unsupported")
    failed = LanguageDetectionResult(None, None, False, None, "detector", False, "error", "detector_error")

    assert unsupported.status == "unsupported"
    assert failed.error_code == "detector_error"


def test_detection_contract_rejects_false_confidence_and_inconsistent_state():
    with pytest.raises(ValueError):
        LanguageDetectionResult("en", "Inglés", True, 1.1, "detector", True, "detected")
    with pytest.raises(ValueError):
        LanguageDetectionResult("en", "Inglés", False, None, "detector", True, "detected")


def test_translation_success_and_failure_contracts():
    success = TranslationResult(
        "en", "es", "Great service", "Excelente servicio", "cerebras", "gpt-oss-120b", True,
        latency_ms=125.0, usage={"total_tokens": 20},
    )
    failure = TranslationResult(
        "en", "es", "Great service", None, "cerebras", "gpt-oss-120b", False,
        error_code="timeout",
    )

    assert success.translated_text == "Excelente servicio"
    assert failure.error_code == "timeout"
    with pytest.raises(ValueError):
        replace(failure, translated_text="texto")


def test_preparation_uses_translation_only_after_success():
    translated = MultilingualPreparationResult(
        "Great service", "en", "Inglés", True, True, "translated", "Excelente servicio",
        "cerebras", "gpt-oss-120b", 125.0, None, "Excelente servicio",
    )
    fallback = MultilingualPreparationResult(
        "Great service", "en", "Inglés", True, True, "fallback_original", None,
        "cerebras", "gpt-oss-120b", 30000.0, "timeout", "Great service",
    )

    assert translated.analysis_text == translated.translated_text
    assert fallback.analysis_text == fallback.original_text
    with pytest.raises(ValueError):
        replace(fallback, analysis_text="Excelente servicio")

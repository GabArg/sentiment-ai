from __future__ import annotations

import pandas as pd

from src.batch import analyze_dataframe, analyze_dataframe_hybrid, analyze_dataframe_multilingual
from src.external_requests import ExternalRequestCoordinator
from src.hybrid_config import HybridRoutingConfig
from src.language_detection import LocalLanguageDetector
from src.multilingual_config import MultilingualConfig
from src.multilingual_contracts import TranslationResult
from src.rate_pacer import RatePacer
from src.sentiment_review import ReviewResult


class CountingProvider:
    def __init__(self, sentiment="Neutro", success=True, error_code=None):
        self.sentiment = sentiment
        self.success = success
        self.error_code = error_code
        self.received = []

    def review_sentiment(self, text):
        self.received.append(text)
        return ReviewResult(
            self.sentiment if self.success else None,
            0.99 if self.success else None,
            None,
            "mock",
            "mock-v1",
            self.success,
            self.error_code,
        )


class MockTranslator:
    api_key = "test"

    def __init__(self):
        self.received = []

    def translate(self, text, source_language, target_language="es"):
        self.received.append((text, source_language, target_language))
        translations = {
            "en": "El servicio fue excelente.",
            "pt": "El pedido llegó el martes.",
            "it": "El producto llegó roto.",
        }
        return TranslationResult(
            source_language,
            target_language,
            text,
            translations[source_language],
            "mock",
            "mock-v1",
            True,
        )


def test_dataframe_analysis_filters_nulls_and_returns_probabilities(predictor):
    frame = pd.DataFrame(
        {"opinion": ["Excelente servicio", None, "El producto llegó roto", " "]}
    )
    result, dropped = analyze_dataframe(frame, "opinion", predictor)

    assert len(result) == 2
    assert dropped == 2
    assert set(result["sentiment"]).issubset(set(predictor.classes))
    assert result.filter(like="probability_").shape[1] == 3


def test_processed_csv_export_has_utf8_bom_and_expected_columns(predictor):
    result, _ = analyze_dataframe(
        pd.DataFrame({"comentario": ["Excelente atención", "Producto dañado"]}),
        "comentario",
        predictor,
    )
    payload = result.to_csv(index=False).encode("utf-8-sig")
    assert payload.startswith(b"\xef\xbb\xbf")
    decoded = payload.decode("utf-8-sig")
    assert "Excelente atención" in decoded
    assert decoded.splitlines()[0].split(",") == list(result.columns)


def test_hybrid_batch_calls_only_routed_cases_and_preserves_order(predictor):
    texts = ["Excelente atención, volvería a comprar.", "Me resolvieron el problema de inmediato."]
    provider = CountingProvider("Negativo")
    config = HybridRoutingConfig(max_reviews_per_batch=25)
    result, dropped, summary = analyze_dataframe_hybrid(
        pd.DataFrame({"text": texts}), "text", predictor, provider, config
    )
    assert dropped == 0
    assert result["text"].tolist() == texts
    assert len(provider.received) == summary["reviews_attempted"] == 1
    assert result.loc[0, "review_state"] == "local_only"
    assert result.loc[1, "sentiment"] == "Negativo"
    assert list(result.columns)[-11:] == [
        "local_sentiment", "local_confidence", "review_requested", "review_reasons",
        "review_state", "review_sentiment", "review_provider", "review_model",
        "review_latency_ms", "fallback_used", "review_error_code",
    ]


def test_hybrid_batch_enforces_budget_and_marks_fallback(predictor):
    provider = CountingProvider()
    config = HybridRoutingConfig(max_reviews_per_batch=1)
    frame = pd.DataFrame({"text": ["Me resolvieron el problema de inmediato.", "El pedido llegó el martes por la tarde."]})
    result, _, summary = analyze_dataframe_hybrid(frame, "text", predictor, provider, config)
    assert len(provider.received) == 1
    assert summary["review_budget_exceeded"] == 1
    exceeded = result[result.review_error_code == "review_budget_exceeded"].iloc[0]
    assert exceeded.review_state == "fallback_local"
    assert exceeded.sentiment == exceeded.local_sentiment


def test_hybrid_batch_provider_failure_falls_back(predictor):
    provider = CountingProvider(success=False, error_code="rate_limited")
    result, _, _ = analyze_dataframe_hybrid(
        pd.DataFrame({"text": ["Me resolvieron el problema de inmediato."]}),
        "text", predictor, provider, HybridRoutingConfig(),
    )
    assert result.loc[0, "review_state"] == "fallback_local"
    assert result.loc[0, "review_error_code"] == "rate_limited"
    assert result.loc[0, "sentiment"] == result.loc[0, "local_sentiment"]


def test_missing_key_does_not_wait_or_consume_external_budget(predictor):
    provider = CountingProvider(success=False, error_code="unavailable")
    provider.api_key = None
    waits = []
    pacer = RatePacer(1, 60, sleeper=lambda seconds: waits.append(seconds))
    frame = pd.DataFrame({"text": ["Me resolvieron el problema de inmediato.", "El pedido llegó el martes por la tarde."]})
    result, _, summary = analyze_dataframe_hybrid(
        frame, "text", predictor, provider, HybridRoutingConfig(max_reviews_per_batch=1), pacer=pacer
    )
    assert waits == []
    assert summary["review_budget_exceeded"] == 0
    assert set(result.review_error_code) == {"unavailable"}


def test_multilingual_batch_preserves_original_columns_and_hides_processed_text(predictor):
    frame = pd.DataFrame(
        {
            "comment": ["The service was excellent and delivery was fast.", "El pedido llegó el martes."],
            "region": ["north", "south"],
        }
    )
    translator = MockTranslator()
    coordinator = ExternalRequestCoordinator(25, RatePacer(5, 60))
    result, dropped, summary = analyze_dataframe_multilingual(
        frame,
        "comment",
        predictor,
        LocalLanguageDetector(),
        translator,
        MultilingualConfig(enabled=True),
        HybridRoutingConfig(enabled=False),
        None,
        coordinator,
    )
    assert dropped == 0 and result["region"].tolist() == ["north", "south"]
    assert "translated_text" not in result and "analysis_text" not in result
    assert list(result.columns)[-8:] == [
        "detected_language", "language_supported", "translation_requested", "translation_state",
        "translation_provider", "translation_model", "translation_latency_ms", "translation_error_code",
    ]
    assert summary["translations_attempted"] == summary["external_calls_used"] == 1


def test_multilingual_batch_global_budget_is_shared_with_reviews(predictor):
    frame = pd.DataFrame(
        {"comment": ["The service was excellent and delivery was fast.", "O pedido chegou na terça-feira."]}
    )
    coordinator = ExternalRequestCoordinator(1, RatePacer(5, 60))
    result, _, summary = analyze_dataframe_multilingual(
        frame,
        "comment",
        predictor,
        LocalLanguageDetector(),
        MockTranslator(),
        MultilingualConfig(enabled=True, max_external_calls_per_batch=1),
        HybridRoutingConfig(enabled=True),
        CountingProvider(),
        coordinator,
    )
    assert summary["external_calls_used"] == 1
    assert coordinator.used <= coordinator.max_calls
    assert "external_budget_exceeded" in set(result["translation_error_code"].dropna())

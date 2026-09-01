"""Six-case real multilingual validation. Never prints credentials."""

from __future__ import annotations

import json
from statistics import median

from src.external_requests import ExternalRequestCoordinator
from src.hybrid_config import HybridRoutingConfig
from src.language_detection import LocalLanguageDetector
from src.model import SentimentPredictor
from src.multilingual_pipeline import evaluate_multilingual_sentiment
from src.rate_pacer import RatePacer
from src.sentiment_review import CerebrasSentimentReviewProvider
from src.translation import CerebrasTranslationProvider


CASES = [
    ("en", "The service was excellent and I would buy again.", "Positivo"),
    ("en", "The order arrived on Tuesday afternoon.", "Neutro"),
    ("pt", "O atendimento foi excelente e eu compraria novamente.", "Positivo"),
    ("pt", "O pedido chegou na terça-feira à tarde.", "Neutro"),
    ("it", "Il servizio è stato eccellente e comprerei di nuovo.", "Positivo"),
    ("it", "L'ordine è arrivato martedì pomeriggio.", "Neutro"),
]
INPUT_COST_PER_TOKEN = 0.00000035
OUTPUT_COST_PER_TOKEN = 0.00000075


def _cost(usage: dict[str, int] | None) -> float | None:
    if not usage:
        return None
    return (
        usage.get("prompt_tokens", 0) * INPUT_COST_PER_TOKEN
        + usage.get("completion_tokens", 0) * OUTPUT_COST_PER_TOKEN
    )


def main() -> None:
    predictor = SentimentPredictor.load()
    detector = LocalLanguageDetector()
    waits: list[float] = []
    coordinator = ExternalRequestCoordinator(
        25,
        RatePacer(5, 60, 0.25),
        lambda seconds: waits.append(seconds),
    )
    translator = CerebrasTranslationProvider(max_retries=0)
    reviewer = CerebrasSentimentReviewProvider(max_retries=0)
    rows = []
    for expected_language, text, expected_sentiment in CASES:
        original_local = predictor.predict_one(text)
        combined = evaluate_multilingual_sentiment(
            text,
            predictor,
            True,
            detector,
            translator,
            HybridRoutingConfig(enabled=True),
            reviewer,
            coordinator,
        )
        preparation = combined.preparation
        translated_local = predictor.predict_one(preparation.analysis_text)
        translation_usage = preparation.translation_usage
        rows.append(
            {
                "expected_language": expected_language,
                "detected_language": preparation.detected_language,
                "expected_sentiment": expected_sentiment,
                "original_text": text,
                "translated_text": preparation.translated_text,
                "translation_success": preparation.translation_state == "translated",
                "translation_state": preparation.translation_state,
                "translation_latency_ms": preparation.translation_latency_ms,
                "translation_error_code": preparation.translation_error_code,
                "translation_usage": translation_usage,
                "translation_cost_usd": _cost(translation_usage),
                "local_original": original_local.label,
                "local_translated": translated_local.label,
                "review_requested": combined.sentiment.review_requested,
                "review_state": combined.sentiment.review_state,
                "review_error_code": combined.sentiment.error_code,
                "review_prediction": combined.sentiment.review_prediction,
                "hybrid_final": combined.final_sentiment,
                "review_latency_ms": combined.sentiment.review_latency_ms,
                "review_usage": combined.sentiment.review_result.usage if combined.sentiment.review_result else None,
                "review_cost_usd": _cost(combined.sentiment.review_result.usage)
                if combined.sentiment.review_result else None,
            }
        )
    payload = {
        "model": translator.model,
        "rows": rows,
        "external_calls": dict(coordinator.calls),
        "pacing_waits_seconds": waits,
        "translation_latency_summary_ms": _latency_summary(
            [row["translation_latency_ms"] for row in rows if row["translation_latency_ms"] is not None]
        ),
        "review_latency_summary_ms": _latency_summary(
            [row["review_latency_ms"] for row in rows if row["review_latency_ms"] is not None]
        ),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _latency_summary(values: list[float]) -> dict[str, float] | None:
    if not values:
        return None
    return {"min": min(values), "median": median(values), "max": max(values)}


if __name__ == "__main__":
    main()

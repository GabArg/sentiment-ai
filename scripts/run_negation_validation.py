"""Controlled Phase 3.1 negation validation; never prints credentials."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import median
import time

import pandas as pd

from src.external_requests import ExternalRequestCoordinator
from src.hybrid_config import HybridRoutingConfig
from src.language_detection import LocalLanguageDetector
from src.model import SentimentPredictor
from src.rate_pacer import RatePacer
from src.review_router import route_prediction
from src.sentiment_review import CerebrasSentimentReviewProvider
from src.translation import CerebrasTranslationProvider


FIXTURE = Path("tests/fixtures/multilingual_risk_benchmark.csv")
ORIGINAL_REVIEW_TYPES = frozenset({"contrast", "negative"})
INPUT_COST_PER_TOKEN = 0.00000035
OUTPUT_COST_PER_TOKEN = 0.00000075


def _cost(usage: dict[str, int] | None) -> float | None:
    if not usage:
        return None
    return usage.get("prompt_tokens", 0) * INPUT_COST_PER_TOKEN + usage.get("completion_tokens", 0) * OUTPUT_COST_PER_TOKEN


def _summary(values: list[float]) -> dict[str, float] | None:
    return {"min": min(values), "median": median(values), "max": max(values)} if values else None


def main() -> None:
    cases = pd.read_csv(FIXTURE).query("group == 'negation'")
    predictor = SentimentPredictor.load()
    detector = LocalLanguageDetector()
    waits: list[float] = []
    coordinator = ExternalRequestCoordinator(40, RatePacer(5, 60, 0.25), waits.append)
    translator = CerebrasTranslationProvider(max_retries=0)
    reviewer = CerebrasSentimentReviewProvider(max_retries=0)
    router = HybridRoutingConfig(enabled=True).router_config()
    rows = []
    started = time.perf_counter()

    for case in cases.itertuples(index=False):
        detected = detector.detect(case.text)
        original_local = predictor.predict_one(case.text)
        coordinator.acquire("translation")
        translation = translator.translate(case.text, detected.detected_language or case.language)
        analysis_text = translation.translated_text if translation.success else case.text
        translated_local = predictor.predict_one(analysis_text)
        decision = route_prediction(predictor.observe_one(analysis_text), router)

        translated_review = None
        translated_review_latency_ms = None
        if decision.should_review:
            coordinator.acquire("sentiment_review")
            review_started = time.perf_counter()
            translated_review = reviewer.review_sentiment(analysis_text)
            translated_review_latency_ms = (time.perf_counter() - review_started) * 1000
        hybrid_final = (
            translated_review.sentiment
            if translated_review is not None and translated_review.success
            else translated_local.label
        )

        original_review = None
        original_review_latency_ms = None
        if case.negation_type in ORIGINAL_REVIEW_TYPES:
            coordinator.acquire("sentiment_review")
            review_started = time.perf_counter()
            original_review = reviewer.review_sentiment(case.text)
            original_review_latency_ms = (time.perf_counter() - review_started) * 1000

        rows.append(
            {
                "language": case.language,
                "negation_type": case.negation_type,
                "expected_sentiment": case.expected_sentiment,
                "text": case.text,
                "detected_language": detected.detected_language,
                "translation": translation.translated_text,
                "translation_success": translation.success,
                "translation_error": translation.error_code,
                "translation_latency_ms": translation.latency_ms,
                "translation_usage": translation.usage,
                "translation_cost_usd": _cost(translation.usage),
                "local_original": original_local.label,
                "local_original_confidence": original_local.confidence,
                "local_translated": translated_local.label,
                "local_translated_confidence": translated_local.confidence,
                "translation_changed_local": original_local.label != translated_local.label,
                "review_requested": decision.should_review,
                "review_translated": translated_review.sentiment if translated_review and translated_review.success else None,
                "review_translated_success": translated_review.success if translated_review else None,
                "review_translated_error": translated_review.error_code if translated_review else None,
                "review_translated_latency_ms": translated_review_latency_ms,
                "review_translated_usage": translated_review.usage if translated_review else None,
                "review_translated_cost_usd": _cost(translated_review.usage) if translated_review else None,
                "hybrid_final": hybrid_final,
                "review_original": original_review.sentiment if original_review and original_review.success else None,
                "review_original_success": original_review.success if original_review else None,
                "review_original_error": original_review.error_code if original_review else None,
                "review_original_latency_ms": original_review_latency_ms,
                "review_original_usage": original_review.usage if original_review else None,
                "review_original_cost_usd": _cost(original_review.usage) if original_review else None,
            }
        )

    translation_latencies = [row["translation_latency_ms"] for row in rows if row["translation_latency_ms"] is not None]
    original_review_latencies = [row["review_original_latency_ms"] for row in rows if row["review_original_latency_ms"] is not None]
    translated_review_latencies = [row["review_translated_latency_ms"] for row in rows if row["review_translated_latency_ms"] is not None]
    payload = {
        "model": translator.model,
        "rows": rows,
        "external_calls": dict(coordinator.calls),
        "average_calls_per_comment": coordinator.used / len(rows),
        "pacing_waits_seconds": waits,
        "pacing_wait_total_seconds": sum(waits),
        "elapsed_seconds": time.perf_counter() - started,
        "translation_latency_ms": _summary(translation_latencies),
        "translated_review_latency_ms": _summary(translated_review_latencies),
        "original_review_latency_ms": _summary(original_review_latencies),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

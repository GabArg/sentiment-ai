"""Efficient batch sentiment analysis."""

from __future__ import annotations

import pandas as pd

from src.external_requests import ExternalRequestCoordinator
from src.hybrid import evaluate_hybrid_observation, fallback_for_budget
from src.hybrid_config import HybridRoutingConfig
from src.multilingual_config import MultilingualConfig
from src.multilingual_contracts import LanguageDetector, TranslationProvider
from src.multilingual_pipeline import evaluate_multilingual_sentiment
from src.model import PredictionObservability, SentimentPredictor
from src.preprocessing import prepare_text_column
from src.rate_pacer import RatePacer
from src.review_router import route_prediction
from src.sentiment_review import SentimentReviewProvider
from src.direct_multilingual import evaluate_direct_multilingual


def analyze_dataframe(
    frame: pd.DataFrame,
    text_column: str,
    predictor: SentimentPredictor,
) -> tuple[pd.DataFrame, int]:
    prepared, dropped = prepare_text_column(frame, text_column)
    predictions = predictor.predict_batch(prepared["text"].tolist())
    return predictions, dropped


def estimate_hybrid_reviews(
    frame: pd.DataFrame,
    text_column: str,
    predictor: SentimentPredictor,
    config: HybridRoutingConfig,
) -> tuple[int, int, int]:
    """Estimate requested and capped reviews locally, without provider calls."""
    prepared, dropped = prepare_text_column(frame, text_column)
    predictions = predictor.predict_batch(prepared["text"].tolist())
    router_config = config.router_config()
    requested = sum(
        float(row.confidence) < router_config.threshold_for(str(row.sentiment))
        for row in predictions.itertuples(index=False)
    )
    return requested, min(requested, config.max_reviews_per_batch), dropped


def analyze_dataframe_hybrid(
    frame: pd.DataFrame,
    text_column: str,
    predictor: SentimentPredictor,
    provider: SentimentReviewProvider,
    config: HybridRoutingConfig,
    pacer: RatePacer | None = None,
    on_progress=None,
    on_pacing=None,
) -> tuple[pd.DataFrame, int, dict[str, int | float]]:
    """Run local inference first, then sequential budgeted second checks."""
    prepared, dropped = prepare_text_column(frame, text_column)
    predictions = predictor.predict_batch(prepared["text"].tolist())
    router_config = config.router_config()
    decisions = []
    observations = []
    for row in predictions.itertuples(index=False):
        probabilities = sorted(
            ((label, float(getattr(row, f"probability_{label.casefold()}"))) for label in predictor.classes),
            key=lambda item: item[1],
            reverse=True,
        )
        observation = PredictionObservability(
            local_prediction=probabilities[0][0],
            local_confidence=probabilities[0][1],
            second_best_class=probabilities[1][0],
            second_best_probability=probabilities[1][1],
            prediction_margin=probabilities[0][1] - probabilities[1][1],
        )
        observations.append(observation)
        decisions.append(route_prediction(observation, router_config))

    requested_total = sum(decision.should_review for decision in decisions)
    provider_available = bool(getattr(provider, "api_key", True))
    allowed_total = min(requested_total, config.max_reviews_per_batch) if provider_available else requested_total
    active_pacer = pacer or RatePacer(config.max_requests, config.window_seconds, config.pacing_margin_seconds)
    review_number = 0
    records = []
    for row, observation, decision in zip(predictions.to_dict("records"), observations, decisions):
        if decision.should_review:
            if review_number >= allowed_total:
                result = fallback_for_budget(observation.local_prediction, observation.local_confidence, observation.prediction_margin, decision)
            else:
                review_number += 1
                if on_progress is not None:
                    on_progress(review_number, allowed_total)
                if provider_available:
                    active_pacer.wait_if_needed(on_pacing)
                result = evaluate_hybrid_observation(row["text"], observation, decision, provider)
        else:
            result = evaluate_hybrid_observation(row["text"], observation, decision, None)
        row["local_sentiment"] = result.local_prediction
        row["local_confidence"] = result.local_confidence
        row["review_requested"] = result.review_requested
        row["review_reasons"] = "|".join(result.review_reasons)
        row["review_state"] = result.review_state
        row["review_sentiment"] = result.review_prediction
        row["review_provider"] = result.review_provider
        row["review_model"] = result.review_model
        row["review_latency_ms"] = result.review_latency_ms
        row["fallback_used"] = result.fallback_used
        row["review_error_code"] = result.error_code
        row["sentiment"] = result.final_prediction
        records.append(row)
    results = pd.DataFrame.from_records(records)
    summary = {
        "review_requested": requested_total,
        "reviews_attempted": review_number,
        "review_budget_exceeded": max(0, requested_total - allowed_total),
        "local_only": int((results["review_state"] == "local_only").sum()),
        "reviewed": int((results["review_state"] == "reviewed").sum()),
        "disagreement": int((results["review_state"] == "disagreement").sum()),
        "fallback": int((results["review_state"] == "fallback_local").sum()),
        "estimated_cost_usd": allowed_total * config.estimated_review_cost_usd,
    }
    return results, dropped, summary


def estimate_multilingual_translations(
    frame: pd.DataFrame,
    text_column: str,
    detector: LanguageDetector,
) -> tuple[int, int]:
    """Detect locally how many valid rows request a supported translation."""
    prepared, dropped = prepare_text_column(frame, text_column)
    requested = 0
    for text in prepared["text"]:
        detection = detector.detect(text)
        requested += bool(
            detection.success
            and detection.supported
            and detection.detected_language in {"en", "pt", "it"}
        )
    return requested, dropped


def analyze_dataframe_multilingual(
    frame: pd.DataFrame,
    text_column: str,
    predictor: SentimentPredictor,
    detector: LanguageDetector,
    translation_provider: TranslationProvider,
    multilingual_config: MultilingualConfig,
    hybrid_config: HybridRoutingConfig,
    review_provider: SentimentReviewProvider | None,
    coordinator: ExternalRequestCoordinator,
    on_progress=None,
) -> tuple[pd.DataFrame, int, dict[str, int]]:
    """Sequential multilingual batch using one global request coordinator."""
    prepared, dropped = prepare_text_column(frame, text_column)
    clean = frame[text_column].fillna("").astype(str).str.strip()
    original_rows = frame.loc[clean.str.len() >= 2].reset_index(drop=True)
    records = []
    for index, (original_row, text) in enumerate(
        zip(original_rows.to_dict("records"), prepared["text"]), start=1
    ):
        if on_progress is not None:
            on_progress(index, len(prepared))
        result = evaluate_multilingual_sentiment(
            text,
            predictor,
            multilingual_config.enabled,
            detector,
            translation_provider,
            hybrid_config,
            review_provider,
            coordinator,
        )
        local = predictor.predict_one(result.preparation.analysis_text)
        row = dict(original_row)
        row["text"] = text
        row["sentiment"] = result.final_sentiment
        row["confidence"] = local.confidence
        for label, probability in local.probabilities.items():
            row[f"probability_{label.casefold()}"] = probability
        row["local_sentiment"] = result.sentiment.local_prediction
        row["local_confidence"] = result.sentiment.local_confidence
        row["review_requested"] = result.sentiment.review_requested
        row["review_reasons"] = "|".join(result.sentiment.review_reasons)
        row["review_state"] = result.sentiment.review_state
        row["review_sentiment"] = result.sentiment.review_prediction
        row["review_provider"] = result.sentiment.review_provider
        row["review_model"] = result.sentiment.review_model
        row["review_latency_ms"] = result.sentiment.review_latency_ms
        row["fallback_used"] = result.sentiment.fallback_used
        row["review_error_code"] = result.sentiment.error_code
        row["detected_language"] = result.preparation.detected_language
        row["language_supported"] = result.preparation.language_supported
        row["translation_requested"] = result.preparation.translation_requested
        row["translation_state"] = result.preparation.translation_state
        row["translation_provider"] = result.preparation.translation_provider
        row["translation_model"] = result.preparation.translation_model
        row["translation_latency_ms"] = result.preparation.translation_latency_ms
        row["translation_error_code"] = result.preparation.translation_error_code
        records.append(row)
    results = pd.DataFrame.from_records(records)
    summary = {
        "external_calls_used": coordinator.used,
        "translations_attempted": int(coordinator.calls["translation"]),
        "reviews_attempted": int(coordinator.calls["sentiment_review"]),
        "external_call_limit": coordinator.max_calls,
        "translation_fallbacks": int((results["translation_state"] == "fallback_original").sum()),
        "local_only": int((results["review_state"] == "local_only").sum()),
        "reviewed": int((results["review_state"] == "reviewed").sum()),
        "disagreement": int((results["review_state"] == "disagreement").sum()),
        "fallback": int((results["review_state"] == "fallback_local").sum()),
    }
    return results, dropped, summary


def analyze_dataframe_direct_multilingual(frame, text_column, predictor, detector, provider, coordinator, hybrid_config=None, hybrid_provider=None, on_progress=None):
    """One-call direct reviews for non-Spanish/short text; preserves source order and columns."""
    prepared, dropped = prepare_text_column(frame, text_column)
    clean = frame[text_column].fillna("").astype(str).str.strip()
    original_rows = frame.loc[clean.str.len() >= 2].reset_index(drop=True)
    records=[]
    for index,(original_row,text) in enumerate(zip(original_rows.to_dict("records"),prepared["text"]),start=1):
        if on_progress:on_progress(index,len(prepared))
        result=evaluate_direct_multilingual(text,predictor,detector,provider,coordinator,hybrid_config,hybrid_provider)
        local=predictor.predict_one(text);row=dict(original_row);row["text"]=text;row["sentiment"]=result.final_prediction;row["confidence"]=local.confidence
        for label,probability in local.probabilities.items():row[f"probability_{label.casefold()}"]=probability
        row.update({"local_sentiment":result.local_prediction,"local_confidence":result.local_confidence,
          "detected_language":result.detected_language,"language_state":result.language_state,
          "direct_review_requested":result.direct_review_requested,"direct_review_state":result.direct_review_state,
          "direct_review_provider":result.direct_review_provider,"direct_review_model":result.direct_review_model,
          "direct_review_latency_ms":result.direct_review_latency_ms,"direct_review_finish_reason":result.direct_review_finish_reason,
          "direct_review_error_code":result.direct_review_error_code})
        records.append(row)
    results=pd.DataFrame.from_records(records)
    return results,dropped,{"external_calls_used":coordinator.used,"direct_reviews_attempted":int(coordinator.calls["sentiment_review"]),"external_call_limit":coordinator.max_calls,"direct_review_fallbacks":int((results.direct_review_state=="direct_review_failed").sum())}


"""Persisted comparison of translated hybrid (A) and direct multilingual review (B)."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Any

import pandas as pd

from src.external_requests import ExternalRequestCoordinator
from src.hybrid_config import HybridRoutingConfig
from src.language_detection import LocalLanguageDetector
from src.model import SentimentPredictor
from src.preprocessing import anonymize_text
from src.rate_pacer import RatePacer
from src.review_router import route_prediction
from scripts.experimental_cerebras_caller import ExperimentalCerebrasCaller
from scripts.phase_3_2_persistence import ExperimentJournal


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "multilingual_phase_3_2_benchmark.csv"
ARTIFACTS = ROOT / "artifacts" / "experiments"
RESULTS = ARTIFACTS / "multilingual_phase_3_2_results.jsonl"
SUMMARY = ARTIFACTS / "multilingual_phase_3_2_summary.json"
COSTS = ARTIFACTS / "multilingual_phase_3_2_costs.csv"
MAX_NEW_CALLS = 30
INPUT_COST = 0.00000035
OUTPUT_COST = 0.00000075


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _usage(result: Any) -> tuple[int | None, int | None, int | None]:
    usage = getattr(result, "usage", None) or {}
    return usage.get("prompt_tokens"), usage.get("completion_tokens"), usage.get("total_tokens")


def _cost(input_tokens: int | None, output_tokens: int | None) -> float | None:
    if input_tokens is None and output_tokens is None:
        return None
    return (input_tokens or 0) * INPUT_COST + (output_tokens or 0) * OUTPUT_COST


def _base(case, architecture: str, predictor: SentimentPredictor) -> dict[str, Any]:
    original = predictor.predict_one(case.text)
    return {
        "case_id": case.case_id,
        "architecture": architecture,
        "language": case.language,
        "expected_sentiment": case.expected_sentiment,
        "original_text": case.text,
        "anonymized_original": anonymize_text(case.text),
        "translated_text": None,
        "local_original_prediction": original.label,
        "local_original_confidence": original.confidence,
        "local_translated_prediction": None,
        "local_translated_confidence": None,
        "review_original_requested": architecture == "B",
        "review_original_result": None,
        "review_original_state": "pending" if architecture == "B" else "not_requested",
        "review_original_error_code": None,
        "review_translated_requested": False,
        "review_translated_result": None,
        "review_translated_state": "not_requested",
        "review_translated_error_code": None,
        "translation_latency_ms": None,
        "review_original_latency_ms": None,
        "review_translated_latency_ms": None,
        "translation_input_tokens": None,
        "translation_output_tokens": None,
        "review_original_input_tokens": None,
        "review_original_output_tokens": None,
        "review_translated_input_tokens": None,
        "review_translated_output_tokens": None,
        "timestamps": {},
        "translation_raw_response": None,
        "review_original_raw_response": None,
        "review_translated_raw_response": None,
    }


def _persist_call(journal, record, architecture, call_type, result, started_at, completed_at, latency):
    input_tokens, output_tokens, total_tokens = _usage(result)
    state = "success" if result.success else "error"
    error = result.error_code
    journal.append_cost(
        {
            "case_id": record["case_id"], "architecture": architecture, "call_type": call_type,
            "input_tokens": input_tokens, "output_tokens": output_tokens, "total_tokens": total_tokens,
            "cost_usd": _cost(input_tokens, output_tokens), "latency_ms": latency,
            "state": state, "error_code": error, "started_at": started_at, "completed_at": completed_at,
        }
    )
    record["timestamps"][call_type] = {"started_at": started_at, "completed_at": completed_at}
    journal.append_result(f"{call_type}_{state}", record)


def run() -> dict[str, Any]:
    cases = pd.read_csv(FIXTURE)
    predictor = SentimentPredictor.load()
    caller = ExperimentalCerebrasCaller(max_retries=0)
    waits: list[float] = []
    coordinator = ExternalRequestCoordinator(MAX_NEW_CALLS, RatePacer(5, 60, 0.25), waits.append)
    journal = ExperimentJournal(RESULTS, SUMMARY, COSTS)
    if RESULTS.exists() or COSTS.exists():
        raise RuntimeError("Experiment artifacts already exist; refusing to repeat external calls.")
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    router = HybridRoutingConfig(enabled=True).router_config()
    started = time.perf_counter()

    # B first: one direct multilingual review for all twelve cases.
    for case in cases.itertuples(index=False):
        record = _base(case, "B", predictor)
        coordinator.acquire("sentiment_review")
        call_started, stamp_started = time.perf_counter(), _now()
        result = caller.review(record["anonymized_original"])
        latency, stamp_completed = (time.perf_counter() - call_started) * 1000, _now()
        record["review_original_result"] = result.sentiment
        record["review_original_state"] = "success" if result.success else "error"
        record["review_original_error_code"] = result.error_code
        record["review_original_latency_ms"] = latency
        record["review_original_input_tokens"], record["review_original_output_tokens"], _ = _usage(result)
        record["review_original_raw_response"] = result.raw_response
        _persist_call(journal, record, "B", "review_original", result, stamp_started, stamp_completed, latency)
        latest[(case.case_id, "B")] = dict(record)

    # A on nine preselected paired cases. Worst case is 18 calls, total cap 30.
    for case in cases[cases.paired_a].itertuples(index=False):
        record = _base(case, "A", predictor)
        coordinator.acquire("translation")
        call_started, stamp_started = time.perf_counter(), _now()
        translation = caller.translate(record["anonymized_original"], case.language)
        latency, stamp_completed = (time.perf_counter() - call_started) * 1000, _now()
        record["translated_text"] = translation.translated_text
        record["translation_latency_ms"] = latency
        record["translation_input_tokens"], record["translation_output_tokens"], _ = _usage(translation)
        record["translation_raw_response"] = translation.raw_response
        _persist_call(journal, record, "A", "translation", translation, stamp_started, stamp_completed, latency)

        if translation.success and translation.translated_text:
            local = predictor.predict_one(translation.translated_text)
            record["local_translated_prediction"] = local.label
            record["local_translated_confidence"] = local.confidence
            decision = route_prediction(predictor.observe_one(translation.translated_text), router)
            record["review_translated_requested"] = decision.should_review
            record["review_translated_state"] = "pending" if decision.should_review else "not_requested"
            journal.append_result("local_translated", record)
            if decision.should_review:
                coordinator.acquire("sentiment_review")
                call_started, stamp_started = time.perf_counter(), _now()
                review = caller.review(anonymize_text(translation.translated_text))
                review_latency, stamp_completed = (time.perf_counter() - call_started) * 1000, _now()
                record["review_translated_result"] = review.sentiment
                record["review_translated_state"] = "success" if review.success else "error"
                record["review_translated_error_code"] = review.error_code
                record["review_translated_latency_ms"] = review_latency
                record["review_translated_input_tokens"], record["review_translated_output_tokens"], _ = _usage(review)
                record["review_translated_raw_response"] = review.raw_response
                _persist_call(journal, record, "A", "review_translated", review, stamp_started, stamp_completed, review_latency)
        latest[(case.case_id, "A")] = dict(record)

    summary = build_summary(cases, latest, coordinator, waits, time.perf_counter() - started)
    journal.write_summary(summary)
    print(json.dumps({
        "new_calls": summary["new_calls"], "paired_cases": summary["paired_cases"],
        "architecture_a_accuracy": summary["architecture_a"]["accuracy"],
        "architecture_b_end_to_end_accuracy": summary["architecture_b"]["end_to_end_accuracy"],
        "elapsed_seconds": summary["elapsed_seconds"], "artifacts": summary["artifacts"],
    }, ensure_ascii=False))
    return summary


def build_summary(cases, latest, coordinator, waits, elapsed):
    b = [latest[(case.case_id, "B")] for case in cases.itertuples(index=False)]
    paired_cases = cases[cases.paired_a]
    a = [latest[(case.case_id, "A")] for case in paired_cases.itertuples(index=False)]
    for row in a:
        row["final"] = row["review_translated_result"] if row["review_translated_state"] == "success" else row["local_translated_prediction"]
    b_correct = [row["review_original_result"] == row["expected_sentiment"] for row in b if row["review_original_state"] == "success"]
    a_correct = [row["final"] == row["expected_sentiment"] for row in a if row["final"]]
    costs = pd.read_csv(COSTS)
    short = pd.read_csv(ROOT / "tests" / "fixtures" / "multilingual_short_texts.csv")
    detector = LocalLanguageDetector()
    short["detected"] = short.text.map(lambda text: detector.detect(text).detected_language)
    short["correct"] = short.detected == short.language
    by_architecture = {}
    for architecture, group in costs.groupby("architecture"):
        by_architecture[architecture] = {
            "calls": int(len(group)),
            "calls_per_evaluated_comment": float(len(group) / (len(a) if architecture == "A" else len(b))),
            "cost_usd": float(group.cost_usd.fillna(0).sum()),
            "cost_per_evaluated_comment_usd": float(group.cost_usd.fillna(0).sum() / (len(a) if architecture == "A" else len(b))),
            "mean_external_latency_ms_per_comment": float(group.latency_ms.sum() / (len(a) if architecture == "A" else len(b))),
            "failures": int((group.state != "success").sum()),
        }
    def class_accuracy(rows, prediction_key, state_key=None):
        output = {}
        for sentiment in ("Negativo", "Neutro", "Positivo"):
            selected = [row for row in rows if row["expected_sentiment"] == sentiment and (state_key is None or row[state_key] == "success")]
            output[sentiment] = sum(row[prediction_key] == sentiment for row in selected) / len(selected) if selected else None
        return output
    return {
        "new_calls": coordinator.used,
        "call_breakdown": dict(coordinator.calls),
        "cases_b": len(b), "paired_cases": len(a),
        "architecture_a": {
            "accuracy": sum(a_correct) / len(a_correct) if a_correct else None,
            "evaluated": len(a_correct),
            "local_translated_accuracy": sum(row["local_translated_prediction"] == row["expected_sentiment"] for row in a) / len(a),
            "accuracy_by_class": class_accuracy(a, "final"),
        },
        "architecture_b": {
            "accuracy_on_successful_responses": sum(b_correct) / len(b_correct) if b_correct else None,
            "end_to_end_accuracy": sum(row["review_original_state"] == "success" and row["review_original_result"] == row["expected_sentiment"] for row in b) / len(b),
            "evaluated": len(b_correct),
            "failures": sum(row["review_original_state"] != "success" for row in b),
            "paired_end_to_end_accuracy": sum(row["review_original_state"] == "success" and row["review_original_result"] == row["expected_sentiment"] for row in [latest[(item.case_id, "B")] for item in paired_cases.itertuples(index=False)]) / len(a),
            "accuracy_by_class": class_accuracy(b, "review_original_result", "review_original_state"),
        },
        "operations_by_architecture": by_architecture,
        "total_cost_usd": float(costs.cost_usd.fillna(0).sum()),
        "cost_by_call_type": costs.groupby("call_type").cost_usd.sum().to_dict(),
        "latency_by_call_type_ms": costs.groupby("call_type").latency_ms.agg(["min", "median", "max", "mean"]).to_dict("index"),
        "pacing_wait_seconds": sum(waits), "elapsed_seconds": elapsed,
        "short_text_policy": {
            "cases": len(short), "captured": int(len(short)),
            "language_distribution": short.language.value_counts().to_dict(),
            "detector_accuracy": float(short.correct.mean()),
            "detector_accuracy_by_language": short.groupby("language").correct.mean().to_dict(),
            "default_spanish_would_be_wrong": int((short.language != "es").sum()),
        },
        "artifacts": {"results": str(RESULTS), "summary": str(SUMMARY), "costs": str(COSTS)},
    }


if __name__ == "__main__":
    run()

"""Reproducible evaluation for the fixed, evaluation-only sentiment benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support

from src.model import SentimentPredictor


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_BENCHMARK_PATH = PROJECT_DIR / "tests" / "fixtures" / "sentiment_benchmark.csv"
EXPECTED_COLUMNS = ("text", "expected_sentiment", "category")


def load_benchmark(path: Path = DEFAULT_BENCHMARK_PATH) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if tuple(frame.columns) != EXPECTED_COLUMNS:
        raise ValueError(f"Benchmark columns must be: {', '.join(EXPECTED_COLUMNS)}")
    if frame.empty or frame.isna().any().any():
        raise ValueError("Benchmark must contain complete evaluation cases.")
    return frame


def evaluate_benchmark(
    predictor: SentimentPredictor,
    benchmark: pd.DataFrame,
    confidence_threshold: float = 0.80,
) -> tuple[dict[str, Any], pd.DataFrame]:
    """Evaluate without training or changing the classifier decision."""
    predictions = predictor.predict_batch(benchmark["text"].tolist())
    probability_columns = [f"probability_{name.casefold()}" for name in predictor.classes]
    probability_values = predictions[probability_columns].to_numpy(dtype=float)
    sorted_indices = np.argsort(probability_values, axis=1)
    top_indices = sorted_indices[:, -1]
    second_indices = sorted_indices[:, -2]
    classes = np.asarray(predictor.classes)

    details = benchmark.reset_index(drop=True).copy()
    details["local_prediction"] = predictions["sentiment"]
    details["local_confidence"] = predictions["confidence"]
    details["second_best_class"] = classes[second_indices]
    details["second_best_probability"] = probability_values[
        np.arange(len(details)), second_indices
    ]
    details["prediction_margin"] = (
        probability_values[np.arange(len(details)), top_indices]
        - details["second_best_probability"].to_numpy()
    )
    details["is_correct"] = details["expected_sentiment"] == details["local_prediction"]
    details["below_80_percent"] = details["local_confidence"] < confidence_threshold
    details["high_confidence_error"] = (~details["is_correct"]) & (
        details["local_confidence"] >= confidence_threshold
    )
    for column in probability_columns:
        details[column] = predictions[column]

    expected = details["expected_sentiment"]
    obtained = details["local_prediction"]
    precision, recall, f1, support = precision_recall_fscore_support(
        expected, obtained, labels=predictor.classes, zero_division=0
    )
    per_class = {
        class_name: {
            "accuracy": float(
                details.loc[expected == class_name, "is_correct"].mean()
            ),
            "precision": float(precision[index]),
            "recall": float(recall[index]),
            "f1": float(f1[index]),
            "support": int(support[index]),
        }
        for index, class_name in enumerate(predictor.classes)
    }
    margins = details["prediction_margin"]
    report: dict[str, Any] = {
        "benchmark": str(DEFAULT_BENCHMARK_PATH.relative_to(PROJECT_DIR)),
        "case_count": len(details),
        "classes": list(predictor.classes),
        "accuracy": float(accuracy_score(expected, obtained)),
        "per_class": per_class,
        "confusion_matrix": {
            "labels": list(predictor.classes),
            "values": confusion_matrix(
                expected, obtained, labels=predictor.classes
            ).tolist(),
        },
        "mean_confidence": float(details["local_confidence"].mean()),
        "below_80_percent_count": int(details["below_80_percent"].sum()),
        "below_80_percent_percentage": float(details["below_80_percent"].mean() * 100),
        "high_confidence_error_count": int(details["high_confidence_error"].sum()),
        "margin_distribution": {
            "minimum": float(margins.min()),
            "p25": float(margins.quantile(0.25)),
            "median": float(margins.median()),
            "p75": float(margins.quantile(0.75)),
            "maximum": float(margins.max()),
            "mean": float(margins.mean()),
        },
    }
    return report, details


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK_PATH)
    parser.add_argument("--json", type=Path, help="Optional JSON report output path")
    parser.add_argument("--csv", type=Path, help="Optional per-case CSV output path")
    args = parser.parse_args()
    report, details = evaluate_benchmark(SentimentPredictor.load(), load_benchmark(args.benchmark))
    if args.json:
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.csv:
        details.to_csv(args.csv, index=False, encoding="utf-8-sig")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

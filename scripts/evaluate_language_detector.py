"""Evaluate the Phase 3 detector against the immutable multilingual fixture."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
import time

import pandas as pd

from src.language_detection import LocalLanguageDetector


FIXTURE = Path("tests/fixtures/multilingual_sentiment_benchmark.csv")


def evaluate(repetitions: int = 3) -> dict[str, object]:
    benchmark = pd.read_csv(FIXTURE)
    detector = LocalLanguageDetector()
    runs = [[detector.detect(text).detected_language for text in benchmark["text"]] for _ in range(repetitions)]
    predictions = runs[0]
    correct = [actual == expected for actual, expected in zip(predictions, benchmark["language"])]
    by_language = {
        language: sum(ok for ok, expected in zip(correct, benchmark["language"]) if expected == language)
        / sum(benchmark["language"] == language)
        for language in sorted(benchmark["language"].unique())
    }
    errors = [
        {"text": text, "expected": expected, "detected": actual}
        for text, expected, actual in zip(benchmark["text"], benchmark["language"], predictions)
        if expected != actual
    ]
    confusion = Counter(zip(benchmark["language"], predictions))
    return {
        "cases": len(benchmark),
        "accuracy": sum(correct) / len(correct),
        "accuracy_by_language": by_language,
        "confusion": {f"{expected}->{actual}": count for (expected, actual), count in sorted(confusion.items())},
        "unknown": sum(prediction is None for prediction in predictions),
        "unsupported": sum(prediction not in {"es", "en", "pt", "it", None} for prediction in predictions),
        "errors": errors,
        "repetitions": repetitions,
        "reproducible": all(run == runs[0] for run in runs[1:]),
    }


if __name__ == "__main__":
    started = time.perf_counter()
    result = evaluate()
    result["evaluation_seconds"] = time.perf_counter() - started
    print(json.dumps(result, ensure_ascii=False, indent=2))

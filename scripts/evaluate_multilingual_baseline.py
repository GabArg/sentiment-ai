"""Measure direct local sentiment on the multilingual fixture (no translation)."""

from __future__ import annotations

from pathlib import Path
import json

import pandas as pd

from src.model import SentimentPredictor


FIXTURE = Path("tests/fixtures/multilingual_sentiment_benchmark.csv")


def evaluate() -> dict[str, object]:
    benchmark = pd.read_csv(FIXTURE)
    predictions = SentimentPredictor.load().predict_batch(benchmark["text"].tolist())
    observed = predictions["sentiment"].tolist()
    correct = [actual == expected for actual, expected in zip(observed, benchmark["expected_sentiment"])]
    return {
        "cases": len(benchmark),
        "accuracy": sum(correct) / len(correct),
        "accuracy_by_language": {
            language: sum(ok for ok, item in zip(correct, benchmark["language"]) if item == language)
            / sum(benchmark["language"] == language)
            for language in sorted(benchmark["language"].unique())
        },
        "accuracy_by_class": {
            sentiment: sum(ok for ok, item in zip(correct, benchmark["expected_sentiment"]) if item == sentiment)
            / sum(benchmark["expected_sentiment"] == sentiment)
            for sentiment in sorted(benchmark["expected_sentiment"].unique())
        },
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), ensure_ascii=False, indent=2))

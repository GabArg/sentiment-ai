"""Aggregate metrics for customer-feedback analytics."""

from __future__ import annotations

import math

import pandas as pd


SENTIMENT_ORDER = ("Negativo", "Neutro", "Positivo")


def calculate_metrics(results: pd.DataFrame) -> dict[str, object]:
    required = {"sentiment", "confidence"}
    if results.empty or not required.issubset(results.columns):
        raise ValueError("Results must include sentiment and confidence values.")

    total = len(results)
    counts = {label: int((results["sentiment"] == label).sum()) for label in SENTIMENT_ORDER}
    percentages = {label: counts[label] / total * 100 for label in SENTIMENT_ORDER}
    negative = counts["Negativo"]
    positive = counts["Positivo"]
    ratio = positive / negative if negative else (math.inf if positive else 0.0)
    critical_threshold = float(results["confidence"].quantile(0.75))
    critical = int(
        ((results["sentiment"] == "Negativo") & (results["confidence"] >= critical_threshold)).sum()
    )
    return {
        "total": total,
        "counts": counts,
        "percentages": percentages,
        "mean_confidence": float(results["confidence"].mean()),
        "positive_negative_ratio": ratio,
        "critical_negative_count": critical,
        "critical_confidence_threshold": critical_threshold,
    }


def sentiment_distribution(metrics: dict[str, object]) -> pd.DataFrame:
    counts = metrics["counts"]
    percentages = metrics["percentages"]
    return pd.DataFrame(
        {
            "sentiment": list(SENTIMENT_ORDER),
            "count": [counts[label] for label in SENTIMENT_ORDER],
            "percentage": [percentages[label] for label in SENTIMENT_ORDER],
        }
    )


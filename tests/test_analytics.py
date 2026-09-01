from __future__ import annotations

import math

import pandas as pd
import pytest

from src.analytics import calculate_metrics, sentiment_distribution


def sample_results() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "sentiment": ["Positivo", "Positivo", "Negativo", "Neutro"],
            "confidence": [0.9, 0.8, 0.7, 0.6],
        }
    )


def test_metrics_counts_percentages_and_ratio():
    metrics = calculate_metrics(sample_results())
    assert metrics["total"] == 4
    assert metrics["counts"] == {"Negativo": 1, "Neutro": 1, "Positivo": 2}
    assert metrics["percentages"]["Positivo"] == pytest.approx(50.0)
    assert metrics["positive_negative_ratio"] == pytest.approx(2.0)
    assert metrics["mean_confidence"] == pytest.approx(0.75)


def test_ratio_handles_no_negative_comments():
    metrics = calculate_metrics(pd.DataFrame({"sentiment": ["Positivo"], "confidence": [0.9]}))
    assert math.isinf(metrics["positive_negative_ratio"])


def test_distribution_uses_stable_class_order():
    distribution = sentiment_distribution(calculate_metrics(sample_results()))
    assert distribution["sentiment"].tolist() == ["Negativo", "Neutro", "Positivo"]


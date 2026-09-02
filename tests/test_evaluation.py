from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.evaluation import evaluate_benchmark, load_benchmark


def test_benchmark_has_sixty_balanced_cases():
    benchmark = load_benchmark()
    assert len(benchmark) == 60
    assert benchmark["expected_sentiment"].value_counts().to_dict() == {
        "Positivo": 20,
        "Negativo": 20,
        "Neutro": 20,
    }
    assert benchmark.groupby("expected_sentiment")["category"].nunique().eq(1).all()


def test_benchmark_evaluation_is_deterministic(predictor):
    benchmark = load_benchmark()
    first_report, first_details = evaluate_benchmark(predictor, benchmark)
    second_report, second_details = evaluate_benchmark(predictor, benchmark)
    assert first_report == second_report
    pd.testing.assert_frame_equal(first_details, second_details)


def test_evaluation_probabilities_confidence_and_margin_are_aligned(predictor):
    _, details = evaluate_benchmark(predictor, load_benchmark())
    probability_columns = ["probability_negativo", "probability_neutro", "probability_positivo"]
    probabilities = details[probability_columns].to_numpy()
    ordered = np.sort(probabilities, axis=1)
    assert np.allclose(probabilities.sum(axis=1), 1.0)
    assert np.allclose(details["local_confidence"], ordered[:, -1])
    assert np.allclose(details["prediction_margin"], ordered[:, -1] - ordered[:, -2])


def test_evaluation_report_contains_every_model_class(predictor):
    report, details = evaluate_benchmark(predictor, load_benchmark())
    assert report["classes"] == list(predictor.classes)
    assert set(report["per_class"]) == set(predictor.classes)
    assert report["confusion_matrix"]["labels"] == list(predictor.classes)
    assert np.asarray(report["confusion_matrix"]["values"]).shape == (3, 3)
    assert {"expected_sentiment", "local_prediction"}.issubset(details.columns)


def test_single_prediction_observability_matches_public_prediction(predictor):
    text = "El pedido llegó el martes por la tarde."
    prediction = predictor.predict_one(text)
    observation = predictor.observe_one(text)
    ranked = sorted(prediction.probabilities.items(), key=lambda item: item[1], reverse=True)
    assert observation.local_prediction == prediction.label
    assert observation.local_confidence == pytest.approx(prediction.confidence)
    assert observation.second_best_class == ranked[1][0]
    assert observation.second_best_probability == pytest.approx(ranked[1][1])
    assert observation.prediction_margin == pytest.approx(ranked[0][1] - ranked[1][1])

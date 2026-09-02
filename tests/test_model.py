from __future__ import annotations

import numpy as np
import pytest


def test_loads_original_model_and_class_order(predictor):
    assert predictor.classes == ("Negativo", "Neutro", "Positivo")


def test_individual_prediction_has_aligned_probabilities(predictor):
    result = predictor.predict_one("La atención fue excelente y recomiendo el servicio.")
    assert result.label in predictor.classes
    assert result.confidence == pytest.approx(result.probabilities[result.label])
    assert sum(result.probabilities.values()) == pytest.approx(1.0)


def test_individual_rejects_blank_text(predictor):
    with pytest.raises(ValueError):
        predictor.predict_one(" ")


def test_individual_rejects_too_short_and_too_long_text(predictor):
    with pytest.raises(ValueError):
        predictor.predict_one("x")
    with pytest.raises(ValueError, match="5,000"):
        predictor.predict_one("x" * 5_001)


def test_batch_prediction_is_vectorized_and_complete(predictor):
    texts = [
        "Excelente servicio, todo llegó a tiempo.",
        "El producto llegó roto y la atención fue horrible.",
        "Cumple su función, nada más que agregar.",
    ]
    result = predictor.predict_batch(texts)
    assert len(result) == len(texts)
    assert list(result.columns) == [
        "text",
        "sentiment",
        "confidence",
        "probability_negativo",
        "probability_neutro",
        "probability_positivo",
    ]
    assert np.allclose(
        result[["probability_negativo", "probability_neutro", "probability_positivo"]].sum(axis=1),
        1.0,
    )
    assert result["text"].tolist() == texts


from __future__ import annotations

import pandas as pd
import pytest

from src.pareto import calculate_pareto, extract_negative_topics


def test_topic_extraction_uses_document_frequency():
    topics = extract_negative_topics(
        [
            "La entrega llegó tarde, tarde, tarde",
            "La entrega llegó tarde y el paquete roto",
            "El soporte no respondió y el paquete roto",
        ],
        max_topics=20,
    )
    frequencies = dict(zip(topics["topic"], topics["frequency"], strict=True))
    assert max(frequencies.values()) <= 3
    assert any("entrega" in topic or "paquete" in topic for topic in frequencies)


def test_pareto_percentages_and_cumulative_are_correct():
    result = calculate_pareto(
        pd.DataFrame({"topic": ["entrega", "soporte", "calidad"], "frequency": [5, 3, 2]})
    )
    assert result["percentage"].tolist() == pytest.approx([50, 30, 20])
    assert result["cumulative_percentage"].tolist() == pytest.approx([50, 80, 100])
    assert result["within_80_percent"].tolist() == [True, True, False]


def test_pareto_rejects_invalid_threshold():
    with pytest.raises(ValueError):
        calculate_pareto(pd.DataFrame(), threshold=1.2)


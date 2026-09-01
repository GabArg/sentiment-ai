from __future__ import annotations

import pandas as pd

from src.batch import analyze_dataframe


def test_dataframe_analysis_filters_nulls_and_returns_probabilities(predictor):
    frame = pd.DataFrame(
        {"opinion": ["Excelente servicio", None, "El producto llegó roto", " "]}
    )
    result, dropped = analyze_dataframe(frame, "opinion", predictor)

    assert len(result) == 2
    assert dropped == 2
    assert set(result["sentiment"]).issubset(set(predictor.classes))
    assert result.filter(like="probability_").shape[1] == 3

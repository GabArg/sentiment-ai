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


def test_processed_csv_export_has_utf8_bom_and_expected_columns(predictor):
    result, _ = analyze_dataframe(
        pd.DataFrame({"comentario": ["Excelente atención", "Producto dañado"]}),
        "comentario",
        predictor,
    )
    payload = result.to_csv(index=False).encode("utf-8-sig")
    assert payload.startswith(b"\xef\xbb\xbf")
    decoded = payload.decode("utf-8-sig")
    assert "Excelente atención" in decoded
    assert decoded.splitlines()[0].split(",") == list(result.columns)

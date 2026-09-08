from __future__ import annotations

import pandas as pd
import streamlit as st

from src.ui.batch_view import (
    prepare_batch_display,
    render_batch_file_summary,
    render_batch_stepper,
    selectable_text_columns,
)


def test_evaluation_columns_are_not_offered_as_model_inputs():
    frame = pd.DataFrame(
        {
            "comentario": ["bien"],
            "expected_sentiment": ["Positivo"],
            "tema_esperado": ["atención"],
            "canal": ["web"],
        }
    )

    assert selectable_text_columns(frame) == ["comentario", "canal"]


def test_batch_display_formats_copy_without_mutating_export_data():
    results = pd.DataFrame(
        {
            "text": ["bien"],
            "sentiment": ["Positivo"],
            "confidence": [0.812],
            "probability_positive": [0.812],
            "review_state": ["local_only"],
        }
    )

    display, config = prepare_batch_display(
        results, review_labels={"local_only": "Modelo local"}
    )

    assert results.loc[0, "confidence"] == 0.812
    assert display.loc[0, "Confianza local"] == 81.2
    assert display.loc[0, "Estado de revisión"] == "Modelo local"
    assert "Comentario" in config and "Confianza local" in config


def test_batch_stepper_reflects_real_state(monkeypatch):
    rendered = []
    monkeypatch.setattr(st, "markdown", lambda body, **kwargs: rendered.append(body))

    render_batch_stepper(has_file=True, has_results=False)

    assert rendered[0].count('class="batch-step active"') == 2
    assert "Importar" in rendered[0] and "Configurar" in rendered[0]


def test_batch_file_summary_escapes_uploaded_filename(monkeypatch):
    rendered = []
    monkeypatch.setattr(st, "markdown", lambda body, **kwargs: rendered.append(body))

    render_batch_file_summary(pd.DataFrame({"comentario": ["bien"]}), "<script>x</script>.csv")

    assert "<script>" not in rendered[0]
    assert "&lt;script&gt;x&lt;/script&gt;.csv" in rendered[0]

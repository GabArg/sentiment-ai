from __future__ import annotations

import pandas as pd
import streamlit as st

from src.ui.pareto_view import build_pareto_view_model, render_priority_ranking


def _metrics():
    return {
        "counts": {"Negativo": 79, "Neutro": 2, "Positivo": 23},
        "percentages": {"Negativo": 75.96, "Neutro": 1.92, "Positivo": 22.12},
    }


def _pareto():
    return pd.DataFrame(
        {
            "topic": ["llego", "recibi", "nadie"],
            "frequency": [5, 3, 2],
            "percentage": [50.0, 30.0, 20.0],
            "cumulative_percentage": [50.0, 80.0, 100.0],
            "within_80_percent": [True, True, False],
        }
    )


def test_pareto_view_model_reuses_existing_priority_flags():
    view = build_pareto_view_model(_metrics(), _pareto())

    assert view["negative_count"] == 79
    assert view["priority_topic_count"] == 2
    assert [item["topic"] for item in view["ranking"]] == ["llego", "recibi"]
    assert view["ranking"][-1]["cumulative_percentage"] == 80.0


def test_priority_ranking_preserves_and_escapes_ngram_labels(monkeypatch):
    pareto = _pareto()
    pareto.loc[0, "topic"] = "<script>llego</script>"
    view = build_pareto_view_model(_metrics(), pareto)
    rendered = []
    monkeypatch.setattr(st, "markdown", lambda body, **kwargs: rendered.append(body))

    render_priority_ranking(view)

    assert "<script>" not in rendered[0]
    assert "&lt;script&gt;llego&lt;/script&gt;" in rendered[0]
    assert "problema de negocio" not in rendered[0]
    assert "N-grama frecuente" in rendered[0]

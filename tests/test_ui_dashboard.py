from __future__ import annotations

import pandas as pd
import streamlit as st

from src.analytics import calculate_metrics
from src.pareto import calculate_pareto
from src.ui.dashboard import (
    build_dashboard_view_model,
    build_traceability_text,
    render_attention_panel,
    render_dashboard_kpis,
    render_panel_heading,
)
from src.ui.html import normalize_html


def test_dashboard_view_model_only_formats_existing_analytics():
    metrics = calculate_metrics(
        pd.DataFrame(
            {
                "sentiment": ["Positivo", "Positivo", "Neutro", "Negativo"],
                "confidence": [0.9, 0.8, 0.7, 0.6],
            }
        )
    )
    pareto = calculate_pareto(
        pd.DataFrame({"topic": ["entrega", "soporte"], "frequency": [3, 1]})
    )

    view = build_dashboard_view_model(metrics, pareto)

    assert view["total"] == metrics["total"]
    assert view["negative_count"] == metrics["counts"]["Negativo"]
    assert view["critical_negative_count"] == metrics["critical_negative_count"]
    assert view["topics"][0] == {
        "rank": 1,
        "topic": "entrega",
        "frequency": 3,
        "percentage": 75.0,
    }
    assert "trend" not in view and "period" not in view


def test_dashboard_view_model_handles_no_negative_feedback():
    metrics = calculate_metrics(
        pd.DataFrame({"sentiment": ["Positivo"], "confidence": [0.9]})
    )

    view = build_dashboard_view_model(metrics, calculate_pareto(pd.DataFrame()))

    assert view["negative_count"] == 0
    assert view["ratio"] is None
    assert view["topics"] == []


def test_traceability_text_preserves_human_hybrid_labels():
    results = pd.DataFrame(
        {"review_state": ["local_only", "reviewed", "disagreement", "fallback_local"]}
    )

    trace = build_traceability_text(results)

    assert trace is not None
    assert "Modelo local" in trace
    assert "Confirmados por second check" in trace
    assert "Corregidos por second check" in trace
    assert "Fallback local" in trace
    assert "local_only" not in trace


def test_normalize_html_removes_markdown_code_indentation():
    markup = """
        <section>

            <article>Contenido</article>
        </section>
    """

    normalized = normalize_html(markup)

    assert normalized == "<section> <article>Contenido</article> </section>"
    assert "\n" not in normalized


def test_attention_html_escapes_dynamic_topic_values(monkeypatch):
    rendered = []
    monkeypatch.setattr(
        st,
        "markdown",
        lambda body, **kwargs: rendered.append((body, kwargs)),
    )
    view = {
        "negative_count": 1,
        "critical_negative_count": 1,
        "critical_confidence_threshold": 0.8,
        "topics": [
            {"rank": 1, "topic": "<script>alert('x')</script>", "frequency": 1}
        ],
    }

    render_attention_panel(view)

    body, kwargs = rendered[0]
    assert kwargs == {"unsafe_allow_html": True}
    assert "<script>" not in body
    assert "&lt;script&gt;" in body
    assert '<p class="overview-method-note">' in body
    assert "\n" not in body


def test_kpi_html_is_emitted_as_one_renderable_fragment(monkeypatch):
    rendered = []
    monkeypatch.setattr(
        st,
        "markdown",
        lambda body, **kwargs: rendered.append((body, kwargs)),
    )
    view = {
        "total": 4,
        "positive_count": 2,
        "positive_percentage": 50.0,
        "negative_count": 1,
        "negative_percentage": 25.0,
        "mean_confidence": 0.75,
    }

    render_dashboard_kpis(view)

    body, kwargs = rendered[0]
    assert body.startswith('<section class="overview-kpi-grid">')
    assert body.endswith("</section>")
    assert body.count('<article class="overview-kpi') == 4
    assert "\n" not in body
    assert kwargs == {"unsafe_allow_html": True}


def test_panel_heading_escapes_dynamic_description(monkeypatch):
    rendered = []
    monkeypatch.setattr(
        st,
        "markdown",
        lambda body, **kwargs: rendered.append(body),
    )

    render_panel_heading("Contexto", "Título", '<img src=x onerror="alert(1)">')

    assert "<img" not in rendered[0]
    assert "&lt;img" in rendered[0]

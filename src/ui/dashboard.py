"""Pure presentation models and components for the feedback overview."""

from __future__ import annotations

import html
import math

import pandas as pd
import streamlit as st

from .html import render_html


def build_dashboard_view_model(
    metrics: dict[str, object], pareto: pd.DataFrame
) -> dict[str, object]:
    """Transform existing analytics into display-ready values without new metrics."""
    counts = metrics["counts"]
    percentages = metrics["percentages"]
    ratio = float(metrics["positive_negative_ratio"])
    topics = [
        {
            "rank": rank,
            "topic": str(row.topic),
            "frequency": int(row.frequency),
            "percentage": float(row.percentage),
        }
        for rank, (_, row) in enumerate(pareto.head(3).iterrows(), start=1)
    ]
    priority_count = int(pareto["within_80_percent"].sum()) if not pareto.empty else 0
    return {
        "total": int(metrics["total"]),
        "positive_count": int(counts["Positivo"]),
        "positive_percentage": float(percentages["Positivo"]),
        "negative_count": int(counts["Negativo"]),
        "negative_percentage": float(percentages["Negativo"]),
        "mean_confidence": float(metrics["mean_confidence"]),
        "critical_negative_count": int(metrics["critical_negative_count"]),
        "critical_confidence_threshold": float(metrics["critical_confidence_threshold"]),
        "ratio": None if math.isinf(ratio) else ratio,
        "priority_topic_count": priority_count,
        "topics": topics,
    }


def build_traceability_text(results: pd.DataFrame) -> str | None:
    """Return a human-readable secondary routing summary when trace data exists."""
    if "direct_review_state" in results.columns:
        states = results["direct_review_state"].value_counts(normalize=True).mul(100)
        labels = {
            "local_only": "Modelo local",
            "direct_multilingual_review": "Revisión multilingüe directa",
            "direct_review_failed": "Fallback local",
        }
        parts = [f"{labels.get(state, 'Estado desconocido')} {value:.1f}%" for state, value in states.items()]
        return "Trazabilidad directa: " + " · ".join(parts)
    if "review_state" in results.columns:
        states = results["review_state"].value_counts(normalize=True).mul(100)
        labels = {
            "local_only": "Modelo local",
            "reviewed": "Confirmados por second check",
            "disagreement": "Corregidos por second check",
            "fallback_local": "Fallback local",
        }
        parts = [f"{labels.get(state, 'Estado desconocido')} {value:.1f}%" for state, value in states.items()]
        return "Trazabilidad híbrida: " + " · ".join(parts)
    return None


def render_dashboard_kpis(view: dict[str, object]) -> None:
    """Render the four primary overview indicators."""
    cards = [
        ("Comentarios analizados", f"{view['total']:,}", "Volumen del lote activo", "neutral"),
        (
            "Señal positiva",
            f"{view['positive_percentage']:.1f}%",
            f"{view['positive_count']:,} comentarios",
            "positive",
        ),
        (
            "Feedback negativo",
            f"{view['negative_percentage']:.1f}%",
            f"{view['negative_count']:,} comentarios",
            "negative",
        ),
        (
            "Confianza media local",
            f"{view['mean_confidence']:.1%}",
            "Contexto técnico del modelo",
            "technical",
        ),
    ]
    markup = "".join(
        f"""
        <article class="overview-kpi {tone}">
            <div><span>{html.escape(label)}</span><i></i></div>
            <strong>{html.escape(value)}</strong>
            <small>{html.escape(detail)}</small>
        </article>
        """
        for label, value, detail, tone in cards
    )
    render_html(f'<section class="overview-kpi-grid">{markup}</section>')


def render_panel_heading(kicker: str, title: str, description: str | None = None) -> None:
    """Render a consistent internal heading for an analytics panel."""
    description_markup = f"<p>{html.escape(description)}</p>" if description else ""
    render_html(
        f"""
        <div class="overview-panel-heading">
            <span>{html.escape(kicker)}</span>
            <h3>{html.escape(title)}</h3>
            {description_markup}
        </div>
        """
    )


def render_attention_panel(view: dict[str, object]) -> None:
    """Render critical-volume context and ranked negative topics."""
    critical_count = int(view["critical_negative_count"])
    threshold = float(view["critical_confidence_threshold"])
    topics = view["topics"]
    if int(view["negative_count"]) == 0:
        body = """
        <div class="overview-attention-empty">
            <i>✓</i><strong>No hay feedback negativo en el lote</strong>
            <p>No se generan prioridades negativas sin observaciones que las respalden.</p>
        </div>
        """
    else:
        rows = "".join(
            f"""
            <div class="overview-topic-row">
                <span>{topic['rank']:02d}</span>
                <div><strong>{html.escape(topic['topic'])}</strong><small>Término frecuente en feedback negativo</small></div>
                <b>{topic['frequency']:,}</b>
            </div>
            """
            for topic in topics
        )
        topics_markup = rows or """
            <div class="overview-no-topics">
                No hay suficientes términos repetidos para construir un ranking.
            </div>
        """
        body = f"""
        <div class="overview-critical-summary">
            <i>!</i>
            <div><strong>{critical_count:,} negativos críticos</strong>
            <p>Negativos con confianza local en el cuartil superior del lote (≥ {threshold:.1%}).</p></div>
        </div>
        <div class="overview-topic-list">{topics_markup}</div>
        """
    render_html(
        f"""
        <section class="overview-attention">
            <div class="overview-attention-title"><span>Prioridad operativa</span><h3>Qué requiere atención</h3></div>
            {body}
            <p class="overview-method-note">Los términos son n-gramas frecuentes, no categorías ni causas verificadas.</p>
        </section>
        """
    )


def render_dataset_reading(view: dict[str, object], traceability: str | None) -> None:
    """Render an honest compact reading of signals already calculated."""
    if view["ratio"] is None:
        ratio_value = "Sin negativos"
        ratio_detail = "No se observó feedback negativo en el lote"
    else:
        ratio_value = f"{view['ratio']:.2f}"
        ratio_detail = "positivos por cada negativo"
    if int(view["priority_topic_count"]):
        pareto_value = str(view["priority_topic_count"])
        pareto_detail = "términos forman el primer bloque del Pareto 80/20"
    else:
        pareto_value = "—"
        pareto_detail = "sin Pareto disponible para este lote"
    render_html(
        f"""
        <section class="overview-reading">
            <div class="overview-attention-title"><span>Lectura del lote</span><h3>Contexto para decidir</h3></div>
            <div class="overview-reading-grid">
                <div><strong>{html.escape(ratio_value)}</strong><span>{html.escape(ratio_detail)}</span></div>
                <div><strong>{html.escape(pareto_value)}</strong><span>{html.escape(pareto_detail)}</span></div>
            </div>
        </section>
        """
    )
    if traceability:
        st.caption(traceability)

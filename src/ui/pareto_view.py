"""Presentation model and components for the negative-term Pareto view."""

from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from .html import render_html


def build_pareto_view_model(
    metrics: dict[str, object], pareto: pd.DataFrame
) -> dict[str, object]:
    """Format existing Pareto and sentiment metrics for presentation."""
    priority = pareto[pareto["within_80_percent"]] if not pareto.empty else pareto
    ranking = [
        {
            "rank": rank,
            "topic": str(row.topic),
            "frequency": int(row.frequency),
            "percentage": float(row.percentage),
            "cumulative_percentage": float(row.cumulative_percentage),
        }
        for rank, (_, row) in enumerate(priority.iterrows(), start=1)
    ]
    return {
        "negative_count": int(metrics["counts"]["Negativo"]),
        "negative_percentage": float(metrics["percentages"]["Negativo"]),
        "priority_topic_count": len(priority),
        "total_topic_count": len(pareto),
        "ranking": ranking,
    }


def render_pareto_summary(view: dict[str, object]) -> None:
    """Render the source volume and size of the current priority set."""
    cards = [
        (
            "Feedback negativo",
            f"{view['negative_count']:,}",
            f"{view['negative_percentage']:.1f}% del lote analizado",
            "negative",
        ),
        (
            "Términos en el bloque 80/20",
            f"{view['priority_topic_count']:,}",
            "Mínimo conjunto que alcanza o supera aproximadamente el 80%",
            "priority",
        ),
        (
            "Términos extraídos",
            f"{view['total_topic_count']:,}",
            "N-gramas disponibles en el Pareto completo",
            "neutral",
        ),
    ]
    markup = "".join(
        f"""
        <article class="pareto-summary-card {tone}">
            <span>{html.escape(label)}</span>
            <strong>{html.escape(value)}</strong>
            <small>{html.escape(detail)}</small>
        </article>
        """
        for label, value, detail, tone in cards
    )
    render_html(f'<section class="pareto-summary-grid">{markup}</section>')


def render_priority_ranking(view: dict[str, object]) -> None:
    """Render the terms in the existing 80-percent priority block."""
    ranking = view["ranking"]
    rows = "".join(
        f"""
        <div class="pareto-ranking-row">
            <span>{item['rank']:02d}</span>
            <div>
                <strong>{html.escape(item['topic'])}</strong>
                <small>N-grama frecuente · {item['percentage']:.1f}% de las menciones temáticas</small>
            </div>
            <b>{item['frequency']:,}</b>
            <i>{item['cumulative_percentage']:.1f}% acum.</i>
        </div>
        """
        for item in ranking
    )
    render_html(
        f"""
        <section class="pareto-ranking-panel">
            <div class="pareto-section-heading">
                <span>Foco de revisión</span>
                <h3>Ranking del primer bloque del Pareto</h3>
                <p>Ordenado por frecuencia documental en comentarios negativos.</p>
            </div>
            <div class="pareto-ranking-list">{rows}</div>
            <p class="pareto-ranking-note">La posición indica frecuencia, no impacto, severidad ni causalidad.</p>
        </section>
        """
    )


def render_pareto_methodology() -> None:
    """Explain the existing extraction and threshold without overstating it."""
    render_html(
        """
        <section class="pareto-methodology">
            <div>i</div>
            <p><strong>Cómo leer esta vista.</strong> Los temas son unigramas o bigramas extraídos de comentarios clasificados como negativos. Cada término se cuenta como máximo una vez por comentario. El bloque destacado contiene el mínimo número de términos cuyo acumulado alcanza o supera aproximadamente el 80% de las menciones temáticas. No representa categorías semánticas ni causas verificadas.</p>
        </section>
        """
    )


def render_pareto_detail_table(pareto: pd.DataFrame) -> None:
    """Keep the full calculation available as secondary evidence."""
    display = pareto.copy()
    display["percentage"] = display["percentage"].map(lambda value: f"{value:.1f}%")
    display["cumulative_percentage"] = display["cumulative_percentage"].map(
        lambda value: f"{value:.1f}%"
    )
    display["within_80_percent"] = display["within_80_percent"].map(
        {True: "Bloque prioritario", False: "Cola"}
    )
    display.columns = ["Término", "Frecuencia", "Porcentaje", "Acumulado", "Tramo"]
    with st.expander("Ver detalle completo del cálculo"):
        st.dataframe(display, width="stretch", hide_index=True)

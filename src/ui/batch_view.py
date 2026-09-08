"""Presentation helpers for the batch import and results workflow."""

from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from .html import render_html


RESERVED_EVALUATION_COLUMNS = {"expected_sentiment", "tema_esperado"}


def selectable_text_columns(frame: pd.DataFrame) -> list[str]:
    """Exclude evaluation targets from the columns offered for inference."""
    return [
        str(column)
        for column in frame.columns
        if str(column).strip().casefold() not in RESERVED_EVALUATION_COLUMNS
    ]


def render_batch_stepper(*, has_file: bool, has_results: bool) -> None:
    """Reflect the current import state without adding decorative controls."""
    active = 3 if has_file and has_results else 2 if has_file else 1
    steps = [
        (1, "Importar", "Cargar CSV"),
        (2, "Configurar", "Elegir columna"),
        (3, "Resultados", "Explorar y exportar"),
    ]
    markup = "".join(
        f"""
        <div class="batch-step {'active' if number <= active else ''}">
            <b>{number}</b><span><strong>{title}</strong><small>{detail}</small></span>
        </div>{'<i></i>' if number < 3 else ''}
        """
        for number, title, detail in steps
    )
    render_html(f'<section class="batch-stepper">{markup}</section>')


def render_batch_file_summary(frame: pd.DataFrame, filename: str | None = None) -> None:
    """Render validated file dimensions above configuration and preview."""
    safe_name = html.escape(filename or "Archivo CSV cargado")
    render_html(
        f"""
        <section class="batch-file-summary">
            <div>CSV</div>
            <span><strong>{safe_name}</strong><small>{len(frame):,} filas · {len(frame.columns):,} columnas detectadas</small></span>
            <b>✓ Archivo validado</b>
        </section>
        """
    )


def preview_column_config(frame: pd.DataFrame) -> dict[str, object]:
    """Build readable, non-mutating column presentation for uploaded data."""
    config: dict[str, object] = {}
    for column in frame.columns:
        width = "large" if frame[column].dtype == object else "medium"
        config[str(column)] = st.column_config.TextColumn(str(column), width=width)
    return config


def prepare_batch_display(
    results: pd.DataFrame,
    *,
    review_labels: dict[str, str] | None = None,
    translation_labels: dict[str, str] | None = None,
    direct_labels: dict[str, str] | None = None,
    error_labels: dict[str, str] | None = None,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Format a display copy while leaving exported/session results untouched."""
    display = results.copy()
    mappings = {
        "review_state": review_labels,
        "translation_state": translation_labels,
        "direct_review_state": direct_labels,
    }
    for column, labels in mappings.items():
        if column in display and labels:
            display[column] = display[column].map(labels).fillna("Estado desconocido")
    if "translation_error_code" in display and error_labels:
        display["translation_error_code"] = display["translation_error_code"].map(
            lambda value: error_labels.get(value, value)
        )
    display = display.rename(
        columns={
            "text": "Comentario",
            "sentiment": "Sentimiento",
            "confidence": "Confianza local",
            "local_confidence": "Confianza local inicial",
            "review_state": "Estado de revisión",
            "translation_state": "Estado de traducción",
            "direct_review_state": "Estado de revisión directa",
        }
    )
    config: dict[str, object] = {}
    for column in display.columns:
        if column in {"Confianza local", "Confianza local inicial"} or column.startswith(
            "probability_"
        ):
            display[column] = pd.to_numeric(display[column], errors="coerce") * 100
            config[column] = st.column_config.NumberColumn(
                column.replace("probability_", "Prob. ").replace("_", " ").title(),
                format="%.1f%%",
                width="small",
            )
        elif column == "Comentario":
            config[column] = st.column_config.TextColumn(column, width="large")
        else:
            config[column] = st.column_config.TextColumn(column, width="medium")
    return display, config

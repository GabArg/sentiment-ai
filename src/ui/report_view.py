"""Structured presentation for deterministic and optional AI reports."""

from __future__ import annotations

import html

import streamlit as st

from src.report_contract import AssistedReading
from src.reporting import generate_assisted_markdown

from .html import render_html


def parse_report_sections(report: str) -> tuple[str, dict[str, str]]:
    """Split generated Markdown into presentation sections without rewriting it."""
    title = ""
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in report.splitlines():
        if line.startswith("# "):
            title = line[2:]
            continue
        if line.startswith("## "):
            current = line[3:]
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(line)
    normalized = {name: "\n".join(lines).strip() for name, lines in sections.items()}
    return title, normalized


def render_report_status(title: str) -> None:
    """Render provenance for the deterministic brief."""
    render_html(
        f"""
        <section class="report-status">
            <div><i>✓</i><span><strong>{html.escape(title)}</strong><small>Generado con reglas determinísticas y datos del lote activo</small></span></div>
            <b>Sin IA</b>
        </section>
        """
    )


def render_brief_section(
    title: str, body: str, *, kicker: str, tone: str = "default"
) -> None:
    """Render one original Markdown section inside a styled panel."""
    with st.container(border=True):
        render_html(
            f"""
            <div class="report-section-heading {html.escape(tone)}">
                <span>{html.escape(kicker)}</span>
                <h3>{html.escape(title)}</h3>
            </div>
            """
        )
        st.markdown(body)


def render_deterministic_brief(report: str) -> None:
    """Present the exact deterministic report as a structured executive brief."""
    title, sections = parse_report_sections(report)
    render_report_status(title)
    render_brief_section(
        "Resumen ejecutivo",
        sections["Resumen ejecutivo"],
        kicker="Lectura principal",
        tone="summary",
    )
    distribution, terms = st.columns([0.9, 1.1], gap="medium")
    with distribution:
        render_brief_section(
            "Distribución",
            sections["Distribución"],
            kicker="Composición del lote",
        )
    with terms:
        render_brief_section(
            "Principales términos negativos",
            sections["Principales términos negativos"],
            kicker="Términos negativos frecuentes",
            tone="attention",
        )
    pareto, opportunity = st.columns(2, gap="medium")
    with pareto:
        render_brief_section(
            "Pareto",
            sections["Pareto"],
            kicker="Concentración léxica",
        )
    with opportunity:
        render_brief_section(
            "Oportunidades",
            sections["Oportunidades"],
            kicker="Lectura determinística",
        )
    render_brief_section(
        "Limitaciones",
        sections["Limitaciones"],
        kicker="Alcance metodológico",
        tone="limitations",
    )


def render_ai_report_intro(
    model: str, characters: int, approximate_tokens: int, available: bool
) -> None:
    """Render privacy and availability context for the separate AI workflow."""
    state = "Disponible" if available else "No configurado"
    state_class = "available" if available else "unavailable"
    render_html(
        f"""
        <section class="report-ai-intro">
            <div class="report-ai-heading">
                <span>Informe IA opcional</span>
                <h3>Análisis agregado con Cerebras</h3>
                <p>Funcionalidad separada. La llamada ocurre sólo al pulsar el botón, recibe hechos agregados sin etiquetas textuales de términos y nunca recibe el CSV completo ni comentarios individuales. Las cifras permanecen bajo control local.</p>
            </div>
            <div class="report-ai-meta">
                <div><span>Modelo</span><strong>{html.escape(model)}</strong></div>
                <div><span>Payload estimado</span><strong>{characters:,} caracteres · ~{approximate_tokens:,} tokens</strong></div>
                <b class="{state_class}">{state}</b>
            </div>
        </section>
        """
    )


def render_assisted_reading(reading: AssistedReading) -> None:
    """Render validated assisted content as a clearly separate layer."""
    with st.container(border=True):
        render_html(
            """
            <div class="report-section-heading summary">
                <span>Complemento opcional</span>
                <h3>Lectura asistida</h3>
            </div>
            """
        )
        st.markdown(generate_assisted_markdown(reading))

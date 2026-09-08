"""Presentation components for individual sentiment analysis."""

from __future__ import annotations

import html

from .html import render_html


def render_individual_intro(description: str, detail: str) -> None:
    """Render the processing context beside the input form."""
    render_html(
        f"""
        <section class="individual-intro">
            <span>Análisis de un comentario</span>
            <h3>Evaluá una señal puntual</h3>
            <p>{html.escape(description)}</p>
            <div><i>⌾</i><small>{html.escape(detail)}</small></div>
        </section>
        """
    )


def render_individual_empty_state() -> None:
    """Explain what will appear before the first analysis."""
    render_html(
        """
        <section class="individual-empty">
            <div>◎</div>
            <span><strong>El resultado aparecerá acá</strong><p>Vas a ver la clasificación final, la confianza del modelo local y la distribución de probabilidades. Cuando corresponda, idioma, routing y fallback quedarán disponibles como trazabilidad.</p></span>
        </section>
        """
    )


def render_individual_result_heading() -> None:
    """Introduce the decision and evidence area."""
    render_html(
        """
        <div class="individual-result-heading">
            <span>Resultado del análisis</span>
            <h3>Clasificación y evidencia local</h3>
            <p>El resultado final se presenta separado de la evidencia y la trazabilidad técnica.</p>
        </div>
        """
    )

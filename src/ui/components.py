"""Small Streamlit components shared by presentation flows."""

from __future__ import annotations

import html

import streamlit as st


def render_product_header() -> None:
    """Render the compact global product header."""
    st.markdown(
        """
        <header class="product-header">
            <div class="product-header-main">
                <span class="product-header-eyebrow">Customer Feedback Analytics</span>
                <h1 class="product-header-title">Sentiment AI</h1>
                <p class="product-header-description">Convertí comentarios de clientes en señales accionables.</p>
            </div>
            <div class="product-header-tagline">
                Python · ML local · Analytics · AI-assisted review
            </div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_footer(*, batch_count: int | None = None) -> None:
    """Render the discrete batch status and bottom project branding in the sidebar."""
    if batch_count is not None:
        st.markdown(
            f"""
            <div class="sidebar-batch-status">
                <span class="status-indicator"></span>
                <span class="sidebar-batch-text">Lote activo: <strong>{batch_count:,}</strong> comentarios</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown(
        """
        <div class="sidebar-footer">
            <div class="sidebar-footer-title">Sentiment AI v2 · RC</div>
            <div class="sidebar-footer-badge">Local-first</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_result_card(
    final_prediction: str,
    local_confidence: float,
    origin: str,
    *,
    confidence_help: str,
    state_label: str | None = None,
) -> None:
    """Render the common result metrics while preserving current labels."""
    badge_style = {
        "Positivo": "badge-positive",
        "Negativo": "badge-negative",
        "Neutro": "badge-neutral",
    }.get(final_prediction, "badge-neutral")
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:0.4rem; margin-bottom:0.4rem; flex-wrap:wrap;">
            <span class="sentiment-badge {badge_style}">{final_prediction}</span>
            <span class="origin-badge">{origin}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.metric("Resultado final", final_prediction)
    st.metric(
        "Confianza del modelo local",
        f"{local_confidence:.1%}",
        help=confidence_help,
    )
    st.caption(f"Origen: {origin}")
    if state_label is not None:
        st.markdown(f"**Estado:** {state_label}")


def render_batch_upload_empty(privacy_message: str) -> None:
    """Render the empty-state upload section with a privacy callout."""
    safe_message = html.escape(privacy_message)
    st.markdown(
        """
        <div class="batch-upload-card">
            <div class="batch-upload-title">Analizá feedback en lote</div>
            <div class="batch-upload-description">
                Subí un CSV con comentarios de clientes y obtené la clasificación
                de sentimiento para cada uno.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="batch-privacy-callout">
            <span class="privacy-icon">🔒</span>
            <span>{safe_message}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_batch_csv_preview(
    row_count: int, col_count: int, selected_column: str
) -> None:
    """Render CSV summary chips above the data preview."""
    safe_column = html.escape(selected_column)
    st.markdown(
        f"""
        <div class="batch-csv-summary">
            <span class="batch-csv-chip">Filas detectadas: <strong>{row_count:,}</strong></span>
            <span class="batch-csv-chip">Columnas: <strong>{col_count:,}</strong></span>
            <span class="batch-csv-chip">Columna de comentario: <strong>{safe_column}</strong></span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_batch_summary_band(
    analyzed: int, dropped: int
) -> None:
    """Render a success band summarising the batch processing outcome."""
    parts = [f'<span class="band-item">Analizados: <strong>{analyzed:,}</strong></span>']
    if dropped:
        parts.append(f'<span class="band-item">Omitidos: <strong>{dropped:,}</strong></span>')
    parts.append('<span class="band-item">Estado: <strong>Completado</strong></span>')
    separator = ' <span class="band-separator">|</span> '
    st.markdown(
        f'<div class="batch-summary-band">{separator.join(parts)}</div>',
        unsafe_allow_html=True,
    )


def render_batch_kpi_cards(metrics: dict[str, object]) -> None:
    """Render a row of KPI cards for batch results. Reuses calculate_metrics output."""
    counts = metrics["counts"]
    pcts = metrics["percentages"]
    cards = [
        ("Total", f"{metrics['total']:,}", ""),
        ("Positivos", f"{counts['Positivo']:,}", f"{pcts['Positivo']:.1f}%"),
        ("Neutros", f"{counts['Neutro']:,}", f"{pcts['Neutro']:.1f}%"),
        ("Negativos", f"{counts['Negativo']:,}", f"{pcts['Negativo']:.1f}%"),
        ("Confianza media", f"{metrics['mean_confidence']:.1%}", ""),
    ]
    html_cards = []
    for label, value, sub in cards:
        sub_html = f'<div class="batch-kpi-sub">{sub}</div>' if sub else ""
        html_cards.append(
            f'<div class="batch-kpi-card">'
            f'<div class="batch-kpi-label">{label}</div>'
            f'<div class="batch-kpi-value">{value}</div>'
            f'{sub_html}'
            f'</div>'
        )
    st.markdown(
        f'<div class="batch-kpi-row">{"".join(html_cards)}</div>',
        unsafe_allow_html=True,
    )


def render_batch_results_header() -> None:
    """Render the results section header."""
    st.markdown(
        """
        <div class="batch-section-header">
            <h3>Resultados del análisis</h3>
            <p>Clasificación de sentimiento por comentario. Podés descargar el CSV completo debajo.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

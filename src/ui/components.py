"""Small Streamlit components shared by presentation flows."""

from __future__ import annotations

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

"""Application shell primitives for the Streamlit workspace."""

from __future__ import annotations

import html

import streamlit as st


PAGE_META = {
    "Análisis individual": (
        "Analizar",
        "Análisis individual",
        "Clasificá un comentario y revisá la evidencia del modelo local.",
    ),
    "Análisis masivo": (
        "Importar y analizar",
        "Análisis masivo",
        "Cargá un CSV, elegí la columna de comentarios y procesá el lote.",
    ),
    "Dashboard": (
        "Customer feedback overview",
        "La voz de tus clientes, en foco.",
        "Detectá señales relevantes, entendé el contexto y priorizá dónde actuar.",
    ),
    "Pareto 80/20": (
        "Entender",
        "Prioridades del feedback negativo",
        "Identificá los temas que concentran la mayor parte de las menciones negativas.",
    ),
    "Informe ejecutivo": (
        "Comunicar",
        "Informe ejecutivo",
        "Convertí métricas agregadas en un resumen claro, trazable y descargable.",
    ),
    "Acerca del proyecto": (
        "Proyecto",
        "Cómo funciona Sentiment AI",
        "Arquitectura, privacidad, metodología, límites y atribución del producto.",
    ),
}

NAV_LABELS = {
    "Análisis individual": "◉  Análisis individual",
    "Análisis masivo": "⇧  Análisis masivo",
    "Dashboard": "▦  Dashboard",
    "Pareto 80/20": "◫  Pareto 80/20",
    "Informe ejecutivo": "≡  Informe ejecutivo",
    "Acerca del proyecto": "◇  Acerca del proyecto",
}

PAGE_ANCHORS = {
    "Análisis individual": "individual",
    "Análisis masivo": "batch",
    "Dashboard": "dashboard",
    "Pareto 80/20": "pareto",
    "Informe ejecutivo": "report",
    "Acerca del proyecto": "about",
}


def format_navigation_label(page: str) -> str:
    """Return a visual label while preserving the radio option value."""
    return NAV_LABELS.get(page, page)


def render_sidebar_brand() -> None:
    """Render product identity and the information architecture legend."""
    st.markdown(
        """
        <div class="workspace-brand">
            <div class="workspace-mark" aria-hidden="true">
                <i></i><i></i><i></i>
            </div>
            <div>
                <strong>Sentiment AI</strong>
                <span>Customer intelligence</span>
            </div>
        </div>
        <div class="workspace-nav-groups" aria-label="Áreas del workspace">
            <span>Analizar</span><i></i><span>Entender</span><i></i><span>Comunicar</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dataset_context(batch_count: int | None) -> None:
    """Render honest, persistent context for the current in-session dataset."""
    if batch_count is None:
        title = "Sin dataset activo"
        detail = "Importá un CSV para habilitar analytics"
        state_class = "is-empty"
    else:
        title = "Lote de la sesión"
        detail = f"{batch_count:,} comentarios analizados"
        state_class = "is-active"
    st.markdown(
        f"""
        <section class="workspace-dataset {state_class}">
            <div class="workspace-dataset-label"><i></i> Dataset activo</div>
            <strong>{html.escape(title)}</strong>
            <span>{html.escape(detail)}</span>
            <small>Session state · procesamiento local-first</small>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_signature() -> None:
    """Render the compact workspace footer."""
    st.markdown(
        """
        <div class="workspace-signature">
            <span>SA</span>
            <div><strong>Workspace local</strong><small>Privacidad primero</small></div>
            <b>v2 · RC</b>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(page: str) -> None:
    """Render the contextual page heading for the active route."""
    eyebrow, title, description = PAGE_META[page]
    st.markdown(
        f'<div class="workspace-page-eyebrow">{html.escape(eyebrow)}</div>',
        unsafe_allow_html=True,
    )
    st.header(title, anchor=f"workspace-page-{PAGE_ANCHORS[page]}")
    st.markdown(
        f'<div class="workspace-page-description">{html.escape(description)}</div>',
        unsafe_allow_html=True,
    )


def render_workspace_empty_state(message: str) -> None:
    """Render a consistent empty analytics state without decorative actions."""
    st.markdown(
        f"""
        <section class="workspace-empty-state">
            <div class="workspace-empty-icon">▦</div>
            <div>
                <strong>El workspace todavía no tiene datos</strong>
                <p>{html.escape(message)}</p>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

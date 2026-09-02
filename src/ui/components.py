"""Small Streamlit components shared by presentation flows."""

from __future__ import annotations

import streamlit as st


def render_result_card(
    final_prediction: str,
    local_confidence: float,
    origin: str,
    *,
    confidence_help: str,
    state_label: str | None = None,
) -> None:
    """Render the common result metrics while preserving current labels."""
    st.metric("Resultado final", final_prediction)
    st.metric(
        "Confianza del modelo local",
        f"{local_confidence:.1%}",
        help=confidence_help,
    )
    st.caption(f"Origen: {origin}")
    if state_label is not None:
        st.markdown(f"**Estado:** {state_label}")

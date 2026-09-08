"""Explicit rendering for trusted UI markup."""

from __future__ import annotations

import streamlit as st


def normalize_html(markup: str) -> str:
    """Remove Markdown-significant indentation from controlled HTML fragments."""
    return " ".join(line.strip() for line in markup.splitlines() if line.strip())


def render_html(markup: str) -> None:
    """Render one explicitly trusted fragment after normalizing its whitespace."""
    st.markdown(normalize_html(markup), unsafe_allow_html=True)

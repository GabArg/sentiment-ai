from __future__ import annotations

import streamlit as st

from src.ui.individual import render_individual_intro


def test_individual_intro_escapes_dynamic_context(monkeypatch):
    rendered = []
    monkeypatch.setattr(st, "markdown", lambda body, **kwargs: rendered.append(body))

    render_individual_intro("<script>mode</script>", "<img src=x>")

    assert "<script>" not in rendered[0]
    assert "&lt;script&gt;mode&lt;/script&gt;" in rendered[0]
    assert "<img" not in rendered[0]
    assert "&lt;img src=x&gt;" in rendered[0]
    assert "\n" not in rendered[0]

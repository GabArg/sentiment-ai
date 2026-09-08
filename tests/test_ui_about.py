from __future__ import annotations

import streamlit as st

from src.ui.about import build_privacy_copy, render_about_overview


def test_direct_privacy_copy_preserves_external_review_guarantees():
    copy = build_privacy_copy(direct=True, multilingual=False, hybrid=False).casefold()

    assert "comentario anonimizado" in copy
    assert "nunca otras columnas del csv" in copy
    assert "original permanece en la aplicación" in copy
    assert "proveedor externo" in copy
    assert "informe ia agregado es una funcionalidad separada" in copy


def test_local_privacy_copy_does_not_claim_comments_are_sent():
    copy = build_privacy_copy(direct=False, multilingual=False, hybrid=False).casefold()

    assert "nunca se envían comentarios" in copy
    assert "métricas y frecuencias agregadas" in copy


def test_about_renders_as_one_controlled_normalized_fragment(monkeypatch):
    rendered = []
    monkeypatch.setattr(st, "markdown", lambda body, **kwargs: rendered.append((body, kwargs)))

    render_about_overview(direct=False, multilingual=False, hybrid=True)

    body, kwargs = rendered[0]
    assert kwargs == {"unsafe_allow_html": True}
    assert "about-pipeline" in body
    assert "proyecto original fue un desarrollo grupal" in body.casefold()
    assert "ATTRIBUTION.md" in body

from __future__ import annotations

import streamlit as st

from src.ui.about import build_privacy_copy, render_about_overview


def test_direct_privacy_copy_describes_external_review_and_aggregate_report():
    copy = build_privacy_copy(direct=True, multilingual=False, hybrid=False).casefold()

    assert "comentario anonimizado" in copy
    assert "excluye las demás columnas del csv" in copy
    assert "revisión directa" in copy
    assert "informe agregado es una acción opcional y separada" in copy
    assert "no comentarios individuales ni el archivo csv" in copy
    assert "no existe una garantía" in copy


def test_local_privacy_copy_distinguishes_current_and_optional_data_flows():
    copy = build_privacy_copy(direct=False, multilingual=False, hybrid=False).casefold()

    assert "análisis local" in copy
    assert "revisión externa de comentarios está desactivada" in copy
    assert "si se habilita" in copy
    assert "conteos, porcentajes y métricas resumidas" in copy
    assert "desidentificación completa" in copy
    assert "nunca se envían comentarios" not in copy


def test_privacy_copy_reports_concurrent_direct_and_hybrid_routes():
    copy = build_privacy_copy(direct=True, multilingual=True, hybrid=True).casefold()

    assert "revisión directa" in copy
    assert "revisión híbrida" in copy
    assert "ruta multilingüe" not in copy


def test_about_renders_clear_product_scope_before_technical_detail(monkeypatch):
    rendered = []
    monkeypatch.setattr(st, "markdown", lambda body, **kwargs: rendered.append((body, kwargs)))

    render_about_overview(direct=False, multilingual=False, hybrid=True)

    body, kwargs = rendered[0]
    assert kwargs == {"unsafe_allow_html": True}
    assert body.index("QUÉ PUEDE HACER") < body.index("CÓMO SE PROCESA")
    assert "Qué permite revisar" in body
    assert "Qué no determina" in body
    assert "Privacidad y tratamiento de datos" in body
    assert "Pareto ordena n-gramas frecuentes" in body
    assert "neutrales factuales" in body
    assert "ATTRIBUTION.md" in body


def test_about_shows_confirmed_original_team_and_separates_project_stages(monkeypatch):
    rendered = []
    monkeypatch.setattr(st, "markdown", lambda body, **kwargs: rendered.append(body))

    render_about_overview(direct=False, multilingual=False, hybrid=False)

    body = rendered[0]
    assert "H12-25-L-Equipo-72" in body
    for member in (
        "Carlos Mauricio Rondón",
        "Juan Carlos Vanegas Molina",
        "Guido Arturo Broccoli",
        "Neldy Rolando Velásquez Samolo",
        "José Julián Gómez Brizuela",
    ):
        assert member in body
    assert "Proyecto original" in body
    assert "Recuperación técnica" in body
    assert "Evolución posterior" in body
    assert "No se asignan roles técnicos individuales" in body

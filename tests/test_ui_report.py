from __future__ import annotations

import streamlit as st

from src.report_contract import build_report_facts, parse_assisted_reading
from src.reporting import generate_assisted_markdown, generate_deterministic_report
from src.ui.report_view import (
    parse_report_sections,
    render_ai_report_intro,
    render_assisted_reading,
)
from tests.test_reporting import metrics_fixture, pareto_fixture, structured_response


def test_structured_brief_parser_preserves_deterministic_content():
    report = generate_deterministic_report(metrics_fixture(), pareto_fixture())

    title, sections = parse_report_sections(report)

    assert title == "Informe ejecutivo determinístico"
    assert list(sections) == [
        "Resumen ejecutivo",
        "Distribución",
        "Principales términos negativos",
        "Pareto",
        "Oportunidades",
        "Limitaciones",
    ]
    for heading, body in sections.items():
        assert f"## {heading}\n{body}" in report
    assert "entrega tarde" in sections["Principales términos negativos"]


def test_ai_intro_escapes_model_and_keeps_privacy_boundary(monkeypatch):
    rendered = []
    monkeypatch.setattr(st, "markdown", lambda body, **kwargs: rendered.append(body))

    render_ai_report_intro("<script>model</script>", 120, 30, False)

    assert "<script>" not in rendered[0]
    assert "&lt;script&gt;model&lt;/script&gt;" in rendered[0]
    assert "nunca recibe el CSV completo ni comentarios individuales" in rendered[0]
    assert "Las cifras permanecen bajo control local" in rendered[0]
    assert "No configurado" in rendered[0]


def test_assisted_view_renders_exact_validated_local_markdown(monkeypatch):
    rendered = []
    monkeypatch.setattr(st, "markdown", lambda body, **kwargs: rendered.append(body))
    reading = parse_assisted_reading(
        structured_response(), build_report_facts(metrics_fixture(), pareto_fixture())
    )

    render_assisted_reading(reading)

    assert rendered[-1] == generate_assisted_markdown(reading)
    assert "Recomendaciones condicionadas" in rendered[-1]

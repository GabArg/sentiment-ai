from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from src.sentiment_review import CerebrasSentimentReviewProvider, ReviewResult


def test_all_plotly_charts_use_supported_streamlit_150_arguments():
    tree = ast.parse((Path(__file__).parents[1] / "app.py").read_text(encoding="utf-8"))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "plotly_chart"
    ]
    assert len(calls) == 5
    for call in calls:
        keywords = {keyword.arg for keyword in call.keywords}
        assert "width" not in keywords
        assert keywords == {"use_container_width"}


def _mock_review(sentiment, *, success=True, error_code=None):
    return ReviewResult(
        sentiment if success else None,
        0.99 if success else None,
        "breve",
        "mock",
        "mock-v1",
        success,
        error_code,
    )


def _run_hybrid_case(monkeypatch, text, review_result):
    monkeypatch.setenv("ENABLE_HYBRID_SENTIMENT", "true")
    monkeypatch.setattr(
        CerebrasSentimentReviewProvider,
        "review_sentiment",
        lambda _provider, _text: review_result,
    )
    app = AppTest.from_file("../app.py", default_timeout=20).run()
    app.text_area[0].set_value(text)
    app.button[0].click().run()
    assert not app.exception
    return app


def test_app_starts_and_individual_analysis_works():
    app = AppTest.from_file("../app.py", default_timeout=20).run()
    assert not app.exception

    app.text_area[0].set_value("La atención fue excelente y llegó a tiempo.")
    app.button[0].click().run()

    assert not app.exception
    assert any(item.label == "Resultado final" for item in app.metric)
    assert any(item.label == "Confianza del modelo local" for item in app.metric)
    assert any(item.value == "Probabilidades del modelo local" for item in app.subheader)
    assert any("Origen: Modelo local" in item.value for item in app.caption)
    assert len(app.get("plotly_chart")) == 1
    assert not any("keyword arguments have been deprecated" in item.value for item in app.warning)


def test_batch_page_can_be_opened_without_data():
    app = AppTest.from_file("../app.py", default_timeout=20).run()
    app.radio[0].set_value(app.radio[0].options[1]).run()

    assert not app.exception
    assert any(item.value == "Análisis masivo" for item in app.header)
    assert any("Subí un CSV" in item.value for item in app.markdown)
    assert any("no se envía a Cerebras" in item.value for item in app.info)


def test_hybrid_individual_without_key_falls_back_cleanly(monkeypatch):
    monkeypatch.setenv("ENABLE_HYBRID_SENTIMENT", "true")
    monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
    app = AppTest.from_file("../app.py", default_timeout=20).run()
    app.text_area[0].set_value("Me resolvieron el problema de inmediato.")
    app.button[0].click().run()
    assert not app.exception
    assert any(item.label == "Resultado final" for item in app.metric)
    assert any("Origen: Fallback local" in item.value for item in app.caption)
    assert any("revisión externa no estuvo disponible" in item.value for item in app.warning)


def test_hybrid_batch_privacy_message_is_precise(monkeypatch):
    monkeypatch.setenv("ENABLE_HYBRID_SENTIMENT", "true")
    app = AppTest.from_file("../app.py", default_timeout=20).run()
    app.radio[0].set_value(app.radio[0].options[1]).run()
    assert not app.exception
    assert any("Sólo comentarios derivados" in item.value for item in app.info)
    assert not any("no se envía a Cerebras" in item.value for item in app.info)


def test_hybrid_local_only_distinguishes_final_and_local_evidence(monkeypatch):
    monkeypatch.setenv("ENABLE_HYBRID_SENTIMENT", "true")
    monkeypatch.setattr(
        CerebrasSentimentReviewProvider,
        "review_sentiment",
        lambda *_: (_ for _ in ()).throw(AssertionError("provider should not be called")),
    )
    app = AppTest.from_file("../app.py", default_timeout=20).run()
    app.text_area[0].set_value("El producto llegó roto y nadie respondió mi reclamo.")
    app.button[0].click().run()
    assert not app.exception
    assert any(item.label == "Resultado final" and item.value == "Negativo" for item in app.metric)
    assert any(item.label == "Confianza del modelo local" for item in app.metric)
    assert any(item.value == "Probabilidades del modelo local" for item in app.subheader)
    assert any("Origen: Modelo local" in item.value for item in app.caption)
    assert any("Estado:** Modelo local" in item.value for item in app.markdown)
    assert any("no alcanzó los criterios" in item.value for item in app.markdown)


def test_hybrid_disagreement_is_presented_as_correction(monkeypatch):
    app = _run_hybrid_case(
        monkeypatch,
        "La calidad es terrible.",
        _mock_review("Negativo"),
    )
    assert any(item.label == "Resultado final" and item.value == "Negativo" for item in app.metric)
    assert any("Origen: Revisión híbrida" in item.value for item in app.caption)
    assert any("Estado:** Corregido por second check" in item.value for item in app.markdown)
    assert any("modificó la clasificación inicial" in item.value for item in app.info)
    assert any("Predicción local: **Positivo**" in item.value for item in app.markdown)
    assert not any(item.value == "99.0%" for item in app.metric)


def test_hybrid_same_class_is_presented_as_confirmed_not_certain(monkeypatch):
    app = _run_hybrid_case(
        monkeypatch,
        "Me resolvieron el problema de inmediato.",
        _mock_review("Negativo"),
    )
    assert any("Estado:** Validado por second check" in item.value for item in app.markdown)
    assert any("confirmó la clasificación local" in item.value for item in app.success)
    visible = " ".join(
        str(item.value)
        for collection in (app.markdown, app.caption, app.info, app.success, app.warning)
        for item in collection
    )
    assert "99%" not in visible and "100% validado" not in visible
    assert "reviewed" not in visible and "disagreement" not in visible and "fallback_local" not in visible


def test_dashboard_uses_human_hybrid_traceability_labels(monkeypatch):
    monkeypatch.setenv("ENABLE_HYBRID_SENTIMENT", "true")
    app = AppTest.from_file("../app.py", default_timeout=20).run()
    app.session_state["batch_results"] = pd.DataFrame(
        {
            "text": ["Producto roto", "Excelente atención", "Pedido recibido", "Sin respuesta"],
            "sentiment": ["Negativo", "Positivo", "Neutro", "Negativo"],
            "confidence": [0.8, 0.9, 0.7, 0.6],
            "review_state": ["local_only", "reviewed", "disagreement", "fallback_local"],
        }
    )
    app.radio[0].set_value("Dashboard").run()
    assert not app.exception
    trace = " ".join(item.value for item in app.caption if "Trazabilidad híbrida" in item.value)
    assert "Modelo local" in trace
    assert "Confirmados por second check" in trace
    assert "Corregidos por second check" in trace
    assert "Fallback local" in trace
    assert "local_only" not in trace and "disagreement" not in trace

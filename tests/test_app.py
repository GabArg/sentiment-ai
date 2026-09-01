from __future__ import annotations

from streamlit.testing.v1 import AppTest


def test_app_starts_and_individual_analysis_works():
    app = AppTest.from_file("../app.py", default_timeout=20).run()
    assert not app.exception

    app.text_area[0].set_value("La atención fue excelente y llegó a tiempo.")
    app.button[0].click().run()

    assert not app.exception
    assert any(item.label == "Sentimiento" for item in app.metric)
    assert any(item.label == "Confianza" for item in app.metric)


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
    assert any("Origen: Modelo local" in item.value for item in app.caption)
    assert any("revisión externa no estuvo disponible" in item.value for item in app.warning)


def test_hybrid_batch_privacy_message_is_precise(monkeypatch):
    monkeypatch.setenv("ENABLE_HYBRID_SENTIMENT", "true")
    app = AppTest.from_file("../app.py", default_timeout=20).run()
    app.radio[0].set_value(app.radio[0].options[1]).run()
    assert not app.exception
    assert any("Sólo comentarios derivados" in item.value for item in app.info)
    assert not any("no se envía a Cerebras" in item.value for item in app.info)

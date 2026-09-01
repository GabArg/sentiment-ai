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
    assert len(app.file_uploader) == 1

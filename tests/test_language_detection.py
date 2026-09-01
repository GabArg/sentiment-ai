import pytest

from src.language_detection import LocalLanguageDetector


@pytest.mark.parametrize(
    ("text", "language"),
    [
        ("La atención fue excelente y el pedido llegó rápido.", "es"),
        ("The service was excellent and delivery was fast.", "en"),
        ("O atendimento foi excelente e a entrega foi rápida.", "pt"),
        ("Il servizio è stato eccellente e la consegna rapida.", "it"),
    ],
)
def test_detector_recognizes_supported_languages(text, language):
    result = LocalLanguageDetector().detect(text)
    assert result.success and result.status == "detected"
    assert result.detected_language == language and result.confidence is None


def test_detector_marks_unsupported_language():
    result = LocalLanguageDetector().detect("Die Lieferung kam am Dienstag an.")
    assert result.success and result.status == "unsupported" and not result.supported
    assert result.detected_language == "de"


def test_detector_returns_unknown_for_empty_or_undetectable_text():
    assert LocalLanguageDetector().detect("").status == "unknown"
    assert LocalLanguageDetector().detect("12345 !!!").status == "unknown"


def test_detector_normalizes_unexpected_error(monkeypatch):
    monkeypatch.setattr("src.language_detection.detect", lambda _text: (_ for _ in ()).throw(RuntimeError()))
    result = LocalLanguageDetector().detect("valid text")
    assert not result.success and result.status == "error" and result.error_code == "detector_error"

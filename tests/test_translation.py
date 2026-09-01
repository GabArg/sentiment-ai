import json
from types import SimpleNamespace

import pytest

from src.translation import CerebrasTranslationProvider, build_translation_prompt


def factory_for(content=None, exception=None, captured=None):
    def create(**kwargs):
        if captured is not None:
            captured.update(kwargs)
        if exception is not None:
            raise exception
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))], usage=None)

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    return lambda **_kwargs: client


def test_translation_provider_accepts_exact_contract():
    provider = CerebrasTranslationProvider(
        api_key="test", client_factory=factory_for(json.dumps({"source_language": "en", "translated_text": "Muy bueno"}))
    )
    result = provider.translate("Very good", "en")
    assert result.success and result.translated_text == "Muy bueno" and result.model == "gpt-oss-120b"


@pytest.mark.parametrize(
    ("content", "code"),
    [
        ("not-json", "invalid_json"),
        ("", "empty_response"),
        (json.dumps({"source_language": "en", "translated_text": ""}), "empty_translation"),
        (json.dumps({"source_language": "pt", "translated_text": "Bueno"}), "source_mismatch"),
        (json.dumps({"source_language": "en", "translated_text": "Bueno", "sentiment": "Positivo"}), "invalid_schema"),
    ],
)
def test_translation_provider_rejects_invalid_contract(content, code):
    provider = CerebrasTranslationProvider(api_key="test", client_factory=factory_for(content))
    assert provider.translate("Very good", "en").error_code == code


@pytest.mark.parametrize(
    ("exception", "code"),
    [
        (TimeoutError(), "timeout"),
        (type("RateLimit", (RuntimeError,), {"status_code": 429})(), "rate_limited"),
        (RuntimeError(), "provider_error"),
        (type("APITimeoutError", (RuntimeError,), {})(), "timeout"),
    ],
)
def test_translation_provider_normalizes_errors(exception, code):
    provider = CerebrasTranslationProvider(api_key="test", client_factory=factory_for(exception=exception))
    assert provider.translate("Very good", "en").error_code == code


def test_translation_provider_returns_unavailable_without_key(monkeypatch):
    monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
    assert CerebrasTranslationProvider().translate("Very good", "en").error_code == "unavailable"


def test_translation_prompt_is_separate_strict_and_private():
    source = "Email me@example.com, tel +54 11 5555-1234, https://x.test, id 12345678"
    prompt = build_translation_prompt(source, "en")
    assert all(secret not in prompt for secret in ("me@example.com", "5555", "https://", "12345678"))
    assert all(marker in prompt for marker in ("[EMAIL]", "[PHONE]", "[URL]", "[ID]"))
    assert "no infieras sentimiento" in prompt and '"source_language"' in prompt


def test_translation_provider_sends_only_prompt_contract():
    captured = {}
    provider = CerebrasTranslationProvider(
        api_key="test",
        client_factory=factory_for(json.dumps({"source_language": "en", "translated_text": "Bien"}), captured=captured),
    )
    provider.translate("Good", "en")
    serialized = str(captured["messages"])
    assert all(field not in serialized for field in ("expected", "local_prediction", "confidence", "channel", "region", "customer_id"))

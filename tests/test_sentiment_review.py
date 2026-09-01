from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from src.sentiment_review import (
    CerebrasSentimentReviewProvider,
    ReviewResult,
    build_review_prompt,
)


def client_factory_for(content, *, exception=None, usage=None, captured=None):
    def create(**kwargs):
        if captured is not None:
            captured.update(kwargs)
        if exception is not None:
            raise exception
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
            usage=usage,
        )

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    return lambda **kwargs: client


def test_missing_key_returns_structured_unavailable(monkeypatch):
    monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
    result = CerebrasSentimentReviewProvider(api_key=None).review_sentiment("texto")
    assert not result.success and result.error_code == "unavailable"
    assert result.sentiment is None


@pytest.mark.parametrize(
    ("exception", "error_code"),
    [
        (TimeoutError("late"), "timeout"),
        (type("RateLimit", (RuntimeError,), {"status_code": 429})("quota"), "rate_limited"),
    ],
)
def test_provider_normalizes_timeout_and_rate_limit(exception, error_code):
    provider = CerebrasSentimentReviewProvider(
        api_key="test-key", client_factory=client_factory_for(None, exception=exception)
    )
    assert provider.review_sentiment("texto").error_code == error_code


@pytest.mark.parametrize(
    ("content", "error_code"),
    [
        ("", "empty_response"),
        ("not-json", "invalid_json"),
        (json.dumps({"sentiment": "Mixto"}), "invalid_sentiment"),
        (json.dumps({"sentiment": "Neutro", "business_action": "refund"}), "invalid_sentiment"),
    ],
)
def test_provider_rejects_invalid_structured_responses(content, error_code):
    provider = CerebrasSentimentReviewProvider(
        api_key="test-key", client_factory=client_factory_for(content)
    )
    result = provider.review_sentiment("texto")
    assert not result.success and result.error_code == error_code


@pytest.mark.parametrize("sentiment", ["Negativo", "Neutro", "Positivo"])
def test_provider_accepts_only_contract_sentiments(sentiment):
    content = json.dumps({"sentiment": sentiment, "confidence": 0.9, "rationale": "breve"})
    provider = CerebrasSentimentReviewProvider(
        api_key="test-key", client_factory=client_factory_for(content)
    )
    result = provider.review_sentiment("texto")
    assert result.success and result.sentiment == sentiment


def test_prompt_anonymizes_pii_and_sends_no_business_columns():
    captured = {}
    content = json.dumps({"sentiment": "Neutro", "confidence": 0.8})
    provider = CerebrasSentimentReviewProvider(
        api_key="test-key",
        client_factory=client_factory_for(content, captured=captured),
    )
    source = "Ana ana@example.com +54 11 5555-1234 https://x.test caso 12345678"
    provider.review_sentiment(source)
    serialized = str(captured["messages"])
    assert "ana@example.com" not in serialized
    assert "5555" not in serialized and "https://" not in serialized and "12345678" not in serialized
    assert all(marker in serialized for marker in ("[EMAIL]", "[PHONE]", "[URL]", "[ID]"))
    assert "canal" not in serialized and "region" not in serialized and "segmento" not in serialized


def test_prompt_defines_factual_neutral_and_is_classification_only():
    prompt = build_review_prompt("El pedido llegó el martes.")
    assert "información factual" in prompt
    assert "Negativo|Neutro|Positivo" in prompt
    assert "No agregues categorías" in prompt


def test_review_result_validates_success_contract():
    with pytest.raises(ValueError, match="allowed sentiment"):
        ReviewResult("Mixto", None, None, "mock", "mock", True)

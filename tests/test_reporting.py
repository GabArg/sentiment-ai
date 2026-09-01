from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import pytest

from src.ai_provider import generate_report_with_fallback
from src.reporting import (
    build_ai_prompt,
    generate_deterministic_report,
    prepare_ai_context,
)


def metrics_fixture() -> dict[str, object]:
    return {
        "total": 10,
        "counts": {"Negativo": 4, "Neutro": 2, "Positivo": 4},
        "percentages": {"Negativo": 40.0, "Neutro": 20.0, "Positivo": 40.0},
        "mean_confidence": 0.82,
        "positive_negative_ratio": 1.0,
        "critical_negative_count": 2,
        "critical_confidence_threshold": 0.9,
    }


def pareto_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "topic": ["entrega tarde", "soporte"],
            "frequency": [3, 1],
            "percentage": [75.0, 25.0],
            "cumulative_percentage": [75.0, 100.0],
            "within_80_percent": [True, True],
        }
    )


def test_deterministic_report_contains_calculated_sections():
    report = generate_deterministic_report(metrics_fixture(), pareto_fixture())
    assert "# Informe ejecutivo determinístico" in report
    assert "Positivos: **4** (40.0%)" in report
    assert "entrega tarde" in report
    assert "Limitaciones" in report


def test_ai_context_contains_only_aggregates():
    context = prepare_ai_context(metrics_fixture(), pareto_fixture())
    serialized = str(context)
    assert set(context) == {
        "total_comments",
        "sentiment_counts",
        "sentiment_percentages",
        "mean_model_confidence",
        "critical_negative_count",
        "negative_topic_pareto",
        "methodology",
    }
    assert "private@example.com" not in serialized
    assert "name" not in context and "email" not in context


def test_versioned_prompt_forbids_inventing_metrics():
    prompt = build_ai_prompt(prepare_ai_context(metrics_fixture(), pareto_fixture()))
    assert "No inventes métricas" in prompt
    assert "exclusivamente" in prompt
    assert "## Limitaciones del análisis" in prompt


def test_fallback_without_api_key(monkeypatch):
    monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
    report, used_ai, error = generate_report_with_fallback(
        "deterministic", {"total": 1}, api_key=None
    )
    assert report == "deterministic"
    assert used_ai is False
    assert "not configured" in error


def test_valid_provider_response_is_returned():
    content = "## Resumen ejecutivo\n" + "Informe válido y basado exclusivamente en datos. " * 3
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )
    completions = SimpleNamespace(create=lambda **kwargs: response)
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    report, used_ai, error = generate_report_with_fallback(
        "deterministic",
        {"total": 1},
        api_key="test-key",
        client_factory=lambda **kwargs: client,
    )
    assert report == content.strip()
    assert used_ai is True and error is None


def test_invalid_provider_response_uses_fallback():
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="short"))]
    )
    client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: response))
    )
    report, used_ai, error = generate_report_with_fallback(
        "deterministic",
        {"total": 1},
        api_key="test-key",
        client_factory=lambda **kwargs: client,
    )
    assert report == "deterministic"
    assert used_ai is False
    assert "valid report" in error


@pytest.mark.parametrize(
    "provider_error",
    [TimeoutError("timed out"), RuntimeError("429 quota"), RuntimeError("provider failed")],
)
def test_provider_exceptions_use_safe_deterministic_fallback(provider_error):
    def failing_factory(**kwargs):
        raise provider_error

    report, used_ai, error = generate_report_with_fallback(
        "deterministic",
        {"total": 1},
        api_key="secret-value-must-not-leak",
        client_factory=failing_factory,
    )
    assert report == "deterministic"
    assert used_ai is False
    assert error == "Cerebras could not generate a valid report."
    assert "secret-value" not in error


@pytest.mark.parametrize("content", [None, "", "too short"])
def test_empty_or_short_provider_responses_use_fallback(content):
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )
    client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: response))
    )
    report, used_ai, error = generate_report_with_fallback(
        "deterministic",
        {"total": 1},
        api_key="test-key",
        client_factory=lambda **kwargs: client,
    )
    assert (report, used_ai) == ("deterministic", False)
    assert error == "Cerebras could not generate a valid report."


def test_missing_choices_uses_fallback():
    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=lambda **kwargs: SimpleNamespace(choices=[]))
        )
    )
    report, used_ai, error = generate_report_with_fallback(
        "deterministic", {"total": 1}, api_key="test-key", client_factory=lambda **kwargs: client
    )
    assert (report, used_ai) == ("deterministic", False)
    assert error == "Cerebras could not generate a valid report."


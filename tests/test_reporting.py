from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import pytest

from src.ai_provider import generate_report_with_fallback
from src.reporting import (
    build_ai_prompt,
    generate_deterministic_report,
    prepare_ai_context,
    validate_ai_report,
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
    assert report.encode("utf-8").decode("utf-8") == report


def test_ai_context_contains_only_aggregates():
    pareto = pareto_fixture()
    pareto.loc[0, "topic"] = "Ana private@example.com +54 11 5555-1234 DNI 12345678"
    context = prepare_ai_context(metrics_fixture(), pareto)
    serialized = str(context)
    assert set(context) == {
        "evidence_contract_version",
        "total_comments",
        "sentiment_counts",
        "sentiment_percentages",
        "mean_local_model_confidence",
        "technical_high_confidence_negative_signal",
        "negative_ngram_mention_pareto",
        "pareto_denominator",
        "topic_labels_withheld",
        "available_business_objectives",
        "available_time_comparison",
        "methodology",
    }
    assert "private@example.com" not in serialized
    assert "Ana" not in serialized and "5555" not in serialized and "12345678" not in serialized
    assert "name" not in context and "email" not in context
    assert context["negative_ngram_mention_pareto"][0]["topic_rank"] == 1
    assert context["available_business_objectives"] is None
    assert "not validated business severity" in str(
        context["technical_high_confidence_negative_signal"]["meaning"]
    )


def test_ai_context_handles_imbalanced_distribution_without_lexical_terms():
    metrics = metrics_fixture()
    metrics.update(
        {
            "total": 5,
            "counts": {"Negativo": 0, "Neutro": 1, "Positivo": 4},
            "percentages": {"Negativo": 0.0, "Neutro": 20.0, "Positivo": 80.0},
            "mean_confidence": 0.51,
            "critical_negative_count": 0,
            "critical_confidence_threshold": 0.6,
        }
    )
    context = prepare_ai_context(metrics, pd.DataFrame())

    assert context["sentiment_counts"]["Negativo"] == 0
    assert context["negative_ngram_mention_pareto"] == []
    assert context["mean_local_model_confidence"] == 0.51
    assert context["available_business_objectives"] is None
    assert context["available_time_comparison"] is None


def test_prompt_makes_insufficient_evidence_and_missing_objectives_explicit():
    metrics = metrics_fixture()
    metrics.update(
        {
            "total": 1,
            "counts": {"Negativo": 0, "Neutro": 1, "Positivo": 0},
            "percentages": {"Negativo": 0.0, "Neutro": 100.0, "Positivo": 0.0},
            "critical_negative_count": 0,
        }
    )
    prompt = build_ai_prompt(prepare_ai_context(metrics, pd.DataFrame()))

    assert '"available_business_objectives": null' in prompt
    assert '"available_time_comparison": null' in prompt
    assert '"negative_ngram_mention_pareto": []' in prompt
    assert "Si falta evidencia" in prompt


def test_versioned_prompt_forbids_inventing_metrics():
    prompt = build_ai_prompt(prepare_ai_context(metrics_fixture(), pareto_fixture()))
    assert "No inventes métricas" in prompt
    assert "exclusivamente" in prompt
    assert "## Limitaciones del análisis" in prompt
    assert "denominador el total de menciones" in prompt
    assert "No es accuracy, precisión" in prompt


def valid_ai_report() -> str:
    return """## Resumen ejecutivo
Se analizaron 10 comentarios; la lectura requiere validación cualitativa.

## Distribución observada
Los comentarios se distribuyen en 40% negativo, 20% neutro y 40% positivo.

## Señales léxicas
El primer rango reúne 75% de las menciones de n-gramas, no de los comentarios.

## Interpretación y próximos pasos
Conviene revisar una muestra y validar manualmente posibles categorías.

## Limitaciones del análisis
La confianza local es una estimación interna, no una medida de precisión. Los n-gramas no prueban causas.
"""


def test_evidence_validator_accepts_supported_report():
    context = prepare_ai_context(metrics_fixture(), pareto_fixture())
    assert validate_ai_report(valid_ai_report(), context) == []


@pytest.mark.parametrize(
    "supported_statement",
    [
        "La confianza local no equivale a precisión ni garantiza corrección.",
        "Los términos frecuentes no son causas verificadas.",
        "La señal técnica no representa casos críticos para el negocio.",
        "El 75% corresponde a menciones de n-gramas, no de los comentarios.",
    ],
)
def test_evidence_validator_accepts_explicit_evidence_limitations(supported_statement):
    context = prepare_ai_context(metrics_fixture(), pareto_fixture())
    report = valid_ai_report().replace(
        "La confianza local es una estimación interna, no una medida de precisión. Los n-gramas no prueban causas.",
        supported_statement,
    )
    assert validate_ai_report(report, context) == []


@pytest.mark.parametrize(
    ("unsafe_sentence", "expected_violation"),
    [
        ("La meta es reducir reclamos un 15%.", "invented_numeric_target"),
        ("Elevar la confianza mejorará la precisión.", "confidence_as_accuracy"),
        (
            "El Pareto indica que 75% de los comentarios pertenece a estos términos.",
            "lexical_share_as_comments",
        ),
        ("Estas son causas raíz confirmadas.", "verified_root_cause"),
        ("Se detectaron casos críticos.", "validated_business_severity"),
        ("El equipo de soporte deberá resolverlo.", "invented_responsibility"),
        ("Debe completarse en el próximo trimestre.", "invented_deadline"),
    ],
)
def test_evidence_validator_rejects_unsupported_interpretations(
    unsafe_sentence, expected_violation
):
    context = prepare_ai_context(metrics_fixture(), pareto_fixture())
    report = valid_ai_report().replace(
        "Conviene revisar una muestra y validar manualmente posibles categorías.",
        unsafe_sentence,
    )
    assert expected_violation in validate_ai_report(report, context)


def test_evidence_validator_rejects_number_not_present_in_payload():
    context = prepare_ai_context(metrics_fixture(), pareto_fixture())
    report = valid_ai_report().replace(
        "Conviene revisar una muestra y validar manualmente posibles categorías.",
        "Conviene alcanzar una mejora del 37%.",
    )
    violations = validate_ai_report(report, context)
    assert "unsupported_percentage:37%" in violations


def test_evidence_validator_rejects_unsupported_deadline():
    context = prepare_ai_context(metrics_fixture(), pareto_fixture())
    report = valid_ai_report().replace(
        "Conviene revisar una muestra y validar manualmente posibles categorías.",
        "Conviene completar la revisión en 30 días.",
    )
    assert "unsupported_number:30" in validate_ai_report(report, context)


def test_evidence_validator_accepts_pending_business_decisions():
    context = prepare_ai_context(metrics_fixture(), pareto_fixture())
    report = valid_ai_report().replace(
        "Conviene revisar una muestra y validar manualmente posibles categorías.",
        "Queda pendiente definir objetivos, plazos y responsables con datos de referencia.",
    )
    assert validate_ai_report(report, context) == []


def test_fallback_without_api_key(monkeypatch):
    monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
    report, used_ai, error = generate_report_with_fallback(
        "deterministic", {"total": 1}, api_key=None
    )
    assert report == "deterministic"
    assert used_ai is False
    assert "not configured" in error


def test_valid_provider_response_is_returned():
    content = valid_ai_report()
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )
    completions = SimpleNamespace(create=lambda **kwargs: response)
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    factory_kwargs = {}

    def factory(**kwargs):
        factory_kwargs.update(kwargs)
        return client

    report, used_ai, error = generate_report_with_fallback(
        "deterministic",
        prepare_ai_context(metrics_fixture(), pareto_fixture()),
        api_key="test-key",
        client_factory=factory,
    )
    assert report == content.strip()
    assert used_ai is True and error is None
    assert factory_kwargs == {"api_key": "test-key", "timeout": 30.0}


@pytest.mark.parametrize(
    "unsafe_sentence",
    [
        "La meta es reducir los reclamos un 15%.",
        "Aumentar la confianza media elevará la precisión.",
        "El Pareto demuestra que 75% de los comentarios comparte cinco problemas.",
        "Estas son causas raíz verificadas.",
    ],
)
def test_provider_uses_fallback_for_evidence_contract_violations(unsafe_sentence):
    content = valid_ai_report().replace(
        "Conviene revisar una muestra y validar manualmente posibles categorías.",
        unsafe_sentence,
    )
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )
    client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: response))
    )
    report, used_ai, error = generate_report_with_fallback(
        "deterministic",
        prepare_ai_context(metrics_fixture(), pareto_fixture()),
        api_key="test-key",
        client_factory=lambda **kwargs: client,
    )
    assert (report, used_ai) == ("deterministic", False)
    assert error == "Cerebras could not generate a valid report."


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


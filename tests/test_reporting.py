from __future__ import annotations

import json
from types import SimpleNamespace

import pandas as pd
import pytest

from src.ai_provider import generate_report_with_fallback
from src.report_contract import build_report_facts
from src.reporting import (
    build_ai_prompt,
    compose_report_document,
    estimate_payload,
    generate_assisted_markdown,
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


def structured_response() -> str:
    return json.dumps(
        {
            "schema_version": "2.0",
            "interpretations": [
                {
                    "interpretation_id": "lexical_concentration_for_review",
                    "fact_refs": ["lexical.selected_frequency_sum"],
                }
            ],
            "hypotheses": [],
            "recommendation_ids": ["inspect_ranked_ngrams"],
            "evidence_needed_ids": ["qualitative_comment_review"],
            "insufficient_evidence_ids": ["no_semantic_categories"],
        }
    )


def client_for(content):
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )
    return SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: response))
    )


def test_deterministic_report_renders_values_from_fact_registry():
    report = generate_deterministic_report(metrics_fixture(), pareto_fixture())

    assert "# Informe ejecutivo determinístico" in report
    assert "Positivos: **4** (40.0%)" in report
    assert "entrega tarde" in report
    assert "n-gramas frecuentes, no categorías semánticas" in report
    assert report.encode("utf-8").decode("utf-8") == report


def test_ai_context_contains_typed_aggregates_and_no_topic_labels_or_pii():
    pareto = pareto_fixture()
    pareto.loc[0, "topic"] = "Ana private@example.com +54 11 5555-1234 DNI 12345678"
    context = prepare_ai_context(metrics_fixture(), pareto)
    serialized = json.dumps(context, ensure_ascii=False)

    assert set(context) == {"contract", "evidence"}
    assert "private@example.com" not in serialized
    assert "Ana" not in serialized and "5555" not in serialized and "12345678" not in serialized
    assert "topic" not in serialized
    denominator = context["evidence"]["facts"]["lexical.selected_frequency_sum"]
    assert denominator["unit"] == "selected_ngram_document_mentions"
    assert "not unique comments" in denominator["definition"]


def test_structured_prompt_forbids_rewriting_facts_and_markdown():
    prompt = build_ai_prompt(prepare_ai_context(metrics_fixture(), pareto_fixture()))

    assert "únicamente con un objeto JSON" in prompt
    assert "No calcules, combines, reformules ni repitas valores" in prompt
    assert "no categorías ni causas" in prompt
    assert "interpretation_id" in prompt


def test_payload_estimate_uses_structured_context():
    context = prepare_ai_context(metrics_fixture(), pareto_fixture())
    size = estimate_payload(context)
    assert size["characters"] > 0
    assert size["approximate_tokens"] == size["characters"] // 4


def test_valid_provider_response_returns_typed_reading():
    facts = build_report_facts(metrics_fixture(), pareto_fixture())
    context = prepare_ai_context(metrics_fixture(), pareto_fixture())
    factory_kwargs = {}

    def factory(**kwargs):
        factory_kwargs.update(kwargs)
        return client_for(structured_response())

    reading, used_ai, error = generate_report_with_fallback(
        context,
        facts,
        api_key="test-key",
        client_factory=factory,
    )

    assert reading is not None
    assert reading.recommendation_ids == ("inspect_ranked_ngrams",)
    assert used_ai is True and error is None
    assert factory_kwargs == {"api_key": "test-key", "timeout": 30.0}


def test_composed_document_uses_local_catalog_and_matches_its_two_visible_layers():
    facts = build_report_facts(metrics_fixture(), pareto_fixture())
    reading, used_ai, _ = generate_report_with_fallback(
        prepare_ai_context(metrics_fixture(), pareto_fixture()),
        facts,
        api_key="test-key",
        client_factory=lambda **kwargs: client_for(structured_response()),
    )
    deterministic = generate_deterministic_report(metrics_fixture(), pareto_fixture())
    assisted = generate_assisted_markdown(reading)
    composed = compose_report_document(deterministic, reading)

    assert used_ai is True
    assert composed == f"{deterministic.rstrip()}\n\n---\n\n{assisted}\n"
    assert "Examinar los comentarios asociados" in composed
    assert "entrega tarde" in deterministic
    assert "entrega tarde" not in assisted


def test_composed_document_cannot_turn_lexical_sum_into_unique_comments():
    pareto = pd.DataFrame(
        {
            "topic": ["uno", "dos", "tres", "cuatro", "cinco"],
            "frequency": [14, 9, 8, 7, 5],
            "percentage": [32.56, 20.93, 18.6, 16.28, 11.63],
            "cumulative_percentage": [32.56, 53.49, 72.09, 88.37, 100.0],
            "within_80_percent": [True, True, True, True, False],
        }
    )
    facts = build_report_facts(metrics_fixture(), pareto)
    response = json.loads(structured_response())
    response["hypotheses"] = [
        {
            "hypothesis_id": "lexical_patterns_may_reflect_shared_issue",
            "fact_refs": ["lexical.selected_frequency_sum"],
            "validation_needed_id": "qualitative_comment_review",
        }
    ]
    reading, _, _ = generate_report_with_fallback(
        prepare_ai_context(metrics_fixture(), pareto),
        facts,
        api_key="test-key",
        client_factory=lambda **kwargs: client_for(json.dumps(response)),
    )
    composed = compose_report_document(
        generate_deterministic_report(metrics_fixture(), pareto), reading
    )

    assert facts.facts["lexical.selected_frequency_sum"].value == 43
    assert facts.facts["lexical.selected_frequency_sum"].unit == "selected_ngram_document_mentions"
    assert "43 comentarios" not in composed
    assert "Hipótesis no verificada" in composed


def test_fallback_without_api_key_returns_no_assisted_content(monkeypatch):
    monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
    facts = build_report_facts(metrics_fixture(), pareto_fixture())
    reading, used_ai, error = generate_report_with_fallback(
        prepare_ai_context(metrics_fixture(), pareto_fixture()), facts, api_key=None
    )
    assert reading is None
    assert used_ai is False
    assert "not configured" in error


@pytest.mark.parametrize(
    "content",
    [None, "", "not json", "{}", '{"schema_version": "1.0"}'],
)
def test_invalid_provider_response_uses_safe_fallback(content):
    facts = build_report_facts(metrics_fixture(), pareto_fixture())
    reading, used_ai, error = generate_report_with_fallback(
        prepare_ai_context(metrics_fixture(), pareto_fixture()),
        facts,
        api_key="test-key",
        client_factory=lambda **kwargs: client_for(content),
    )
    assert reading is None and used_ai is False
    assert error == "Cerebras could not generate a valid report."


@pytest.mark.parametrize(
    "provider_error",
    [TimeoutError("timed out"), RuntimeError("429 quota"), RuntimeError("provider failed")],
)
def test_provider_exceptions_use_safe_fallback_without_secret(provider_error):
    def failing_factory(**kwargs):
        raise provider_error

    facts = build_report_facts(metrics_fixture(), pareto_fixture())
    reading, used_ai, error = generate_report_with_fallback(
        prepare_ai_context(metrics_fixture(), pareto_fixture()),
        facts,
        api_key="secret-value-must-not-leak",
        client_factory=failing_factory,
    )
    assert reading is None and used_ai is False
    assert error == "Cerebras could not generate a valid report."
    assert "secret-value" not in error


def test_missing_choices_uses_safe_fallback():
    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=lambda **kwargs: SimpleNamespace(choices=[]))
        )
    )
    facts = build_report_facts(metrics_fixture(), pareto_fixture())
    reading, used_ai, error = generate_report_with_fallback(
        prepare_ai_context(metrics_fixture(), pareto_fixture()),
        facts,
        api_key="test-key",
        client_factory=lambda **kwargs: client,
    )
    assert reading is None and used_ai is False
    assert error == "Cerebras could not generate a valid report."


def test_fallback_log_distinguishes_contract_rejection_without_content(caplog):
    secret = "secret-value-must-not-leak"
    generated_content = "not json private generated text"
    facts = build_report_facts(metrics_fixture(), pareto_fixture())

    with caplog.at_level("WARNING", logger="src.ai_provider"):
        reading, used_ai, error = generate_report_with_fallback(
            prepare_ai_context(metrics_fixture(), pareto_fixture()),
            facts,
            api_key=secret,
            client_factory=lambda **kwargs: client_for(generated_content),
        )

    assert reading is None and used_ai is False
    assert error == "Cerebras could not generate a valid report."
    diagnostic = caplog.messages[-1]
    assert "stage=contract_validation" in diagnostic
    assert "code=contract_response_rejected" in diagnostic
    assert "exception_type=ReportContractError" in diagnostic
    assert "contract_version=2.0" in diagnostic
    assert secret not in diagnostic
    assert generated_content not in diagnostic


def test_fallback_log_records_safe_http_diagnostics(caplog):
    class RateLimitError(RuntimeError):
        status_code = 429

    def client_with_failed_request(**kwargs):
        def create(**request_kwargs):
            raise RateLimitError("sensitive provider response")

        return SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        )

    facts = build_report_facts(metrics_fixture(), pareto_fixture())
    with caplog.at_level("WARNING", logger="src.ai_provider"):
        reading, used_ai, _ = generate_report_with_fallback(
            prepare_ai_context(metrics_fixture(), pareto_fixture()),
            facts,
            api_key="test-key",
            client_factory=client_with_failed_request,
        )

    assert reading is None and used_ai is False
    diagnostic = caplog.messages[-1]
    assert "stage=provider_request" in diagnostic
    assert "code=provider_request_failed" in diagnostic
    assert "exception_type=RateLimitError" in diagnostic
    assert "http_status=429" in diagnostic
    assert "sensitive provider response" not in diagnostic


def test_fallback_log_distinguishes_client_initialization(caplog):
    def failing_factory(**kwargs):
        raise RuntimeError("private initialization detail")

    facts = build_report_facts(metrics_fixture(), pareto_fixture())
    with caplog.at_level("WARNING", logger="src.ai_provider"):
        generate_report_with_fallback(
            prepare_ai_context(metrics_fixture(), pareto_fixture()),
            facts,
            api_key="test-key",
            client_factory=failing_factory,
        )

    diagnostic = caplog.messages[-1]
    assert "stage=client_initialization" in diagnostic
    assert "code=client_initialization_failed" in diagnostic
    assert "private initialization detail" not in diagnostic


def test_fallback_log_distinguishes_invalid_response_shape(caplog):
    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=lambda **kwargs: SimpleNamespace(choices=[]))
        )
    )
    facts = build_report_facts(metrics_fixture(), pareto_fixture())
    with caplog.at_level("WARNING", logger="src.ai_provider"):
        generate_report_with_fallback(
            prepare_ai_context(metrics_fixture(), pareto_fixture()),
            facts,
            api_key="test-key",
            client_factory=lambda **kwargs: client,
        )

    diagnostic = caplog.messages[-1]
    assert "stage=provider_response" in diagnostic
    assert "code=invalid_response_shape" in diagnostic


@pytest.mark.parametrize(
    ("content", "expected_code"),
    [(None, "missing_response_content"), ("", "missing_response_content")],
)
def test_fallback_log_distinguishes_missing_provider_content(
    content, expected_code, caplog
):
    facts = build_report_facts(metrics_fixture(), pareto_fixture())
    with caplog.at_level("WARNING", logger="src.ai_provider"):
        generate_report_with_fallback(
            prepare_ai_context(metrics_fixture(), pareto_fixture()),
            facts,
            api_key="test-key",
            client_factory=lambda **kwargs: client_for(content),
        )

    diagnostic = caplog.messages[-1]
    assert "stage=provider_response" in diagnostic
    assert f"code={expected_code}" in diagnostic

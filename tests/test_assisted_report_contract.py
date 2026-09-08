from __future__ import annotations

import json

import pandas as pd
import pytest

from src.report_contract import (
    ReportContractError,
    build_assisted_context,
    build_report_facts,
    parse_assisted_reading,
)
from tests.test_reporting import metrics_fixture, pareto_fixture


def valid_response() -> dict[str, object]:
    return {
        "schema_version": "2.0",
        "interpretations": [
            {
                "interpretation_id": "lexical_concentration_for_review",
                "fact_refs": ["lexical.selected_frequency_sum"],
            }
        ],
        "hypotheses": [
            {
                "statement": "La concentración léxica podría orientar una revisión cualitativa inicial.",
                "fact_refs": ["lexical.rank.1.share"],
                "validation_needed": "Revisar los comentarios asociados y validar categorías manualmente.",
            }
        ],
        "recommendation_ids": ["inspect_ranked_ngrams"],
        "evidence_needed_ids": ["qualitative_comment_review"],
        "insufficient_evidence_ids": ["no_semantic_categories"],
    }


def facts():
    return build_report_facts(metrics_fixture(), pareto_fixture())


def test_context_exposes_only_eligible_catalog_ids_and_aggregate_facts():
    context = build_assisted_context(facts())

    assert set(context) == {"contract", "evidence"}
    assert "inspect_ranked_ngrams" in context["contract"]["recommendation_ids"]
    assert "no_negative_comments" not in context["contract"]["insufficient_evidence_ids"]
    assert "topic" not in str(context)


def test_valid_structured_reading_is_parsed_without_provider_numbers():
    reading = parse_assisted_reading(json.dumps(valid_response()), facts())

    assert reading.schema_version == "2.0"
    assert reading.interpretations[0].interpretation_id == "lexical_concentration_for_review"
    assert reading.recommendation_ids == ("inspect_ranked_ngrams",)


@pytest.mark.parametrize("extra", [{"metric": 41}, {"deadline": "soon"}, {"category": "delivery"}])
def test_additional_fields_are_rejected(extra):
    response = valid_response() | extra
    with pytest.raises(ReportContractError, match="additional fields"):
        parse_assisted_reading(json.dumps(response), facts())


def test_unknown_fact_reference_is_rejected():
    response = valid_response()
    response["hypotheses"][0]["fact_refs"] = ["sentiment.cause.delivery"]
    with pytest.raises(ReportContractError, match="does not exist"):
        parse_assisted_reading(json.dumps(response), facts())


@pytest.mark.parametrize(
    "unsafe_text",
    [
        "Estas señales explican el 41% de los comentarios.",
        "La meta debería ser reducir la negatividad a la mitad en 30 días.",
        "El impacto esperado es USD cinco mil.",
        "Consultar https://example.com para validar.",
    ],
)
def test_numbers_money_percentages_and_urls_are_rejected_in_free_text(unsafe_text):
    response = valid_response()
    response["hypotheses"][0]["statement"] = unsafe_text
    with pytest.raises(ReportContractError, match="forbidden"):
        parse_assisted_reading(json.dumps(response), facts())


def test_hypothesis_without_validation_needed_is_rejected():
    response = valid_response()
    del response["hypotheses"][0]["validation_needed"]
    with pytest.raises(ReportContractError, match="hypothesis fields"):
        parse_assisted_reading(json.dumps(response), facts())


def test_ineligible_recommendation_is_rejected_without_negative_or_lexical_data():
    metrics = metrics_fixture()
    metrics.update(
        {
            "counts": {"Negativo": 0, "Neutro": 2, "Positivo": 8},
            "percentages": {"Negativo": 0.0, "Neutro": 20.0, "Positivo": 80.0},
            "critical_negative_count": 0,
        }
    )
    empty_facts = build_report_facts(metrics, pd.DataFrame())
    response = valid_response()
    response.update(
        {
            "interpretations": [],
            "hypotheses": [],
            "recommendation_ids": ["inspect_ranked_ngrams"],
            "evidence_needed_ids": [],
            "insufficient_evidence_ids": ["no_negative_comments", "no_lexical_terms"],
        }
    )
    with pytest.raises(ReportContractError, match="ineligible"):
        parse_assisted_reading(json.dumps(response), empty_facts)


def test_empty_batch_signals_can_report_insufficient_evidence_without_free_text():
    metrics = metrics_fixture()
    metrics.update(
        {
            "counts": {"Negativo": 0, "Neutro": 2, "Positivo": 8},
            "percentages": {"Negativo": 0.0, "Neutro": 20.0, "Positivo": 80.0},
            "critical_negative_count": 0,
        }
    )
    empty_facts = build_report_facts(metrics, pd.DataFrame())
    response = valid_response()
    response.update(
        {
            "interpretations": [],
            "hypotheses": [],
            "recommendation_ids": ["independent_model_evaluation"],
            "evidence_needed_ids": ["independent_labeled_evaluation"],
            "insufficient_evidence_ids": ["no_negative_comments", "no_lexical_terms"],
        }
    )

    reading = parse_assisted_reading(json.dumps(response), empty_facts)
    assert reading.insufficient_evidence_ids == ("no_negative_comments", "no_lexical_terms")


@pytest.mark.parametrize("raw", ["not json", "[]", "{}", '{"schema_version": "1.0"}'])
def test_malformed_or_incompatible_response_is_rejected(raw):
    with pytest.raises(ReportContractError):
        parse_assisted_reading(raw, facts())

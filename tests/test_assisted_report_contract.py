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
                "hypothesis_id": "lexical_patterns_may_reflect_shared_issue",
                "fact_refs": ["lexical.selected_frequency_sum"],
                "validation_needed_id": "qualitative_comment_review",
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
    assert "lexical_concentration_for_review" in context["contract"]["interpretations"]
    assert context["contract"]["hypotheses"]["lexical_patterns_may_reflect_shared_issue"] == {
        "fact_refs": ["lexical.selected_frequency_sum"],
        "validation_needed_ids": [
            "qualitative_comment_review",
            "semantic_category_validation",
        ],
    }
    assert "topic" not in str(context)


def minimal_response_from_context(context: dict[str, object]) -> dict[str, object]:
    contract = context["contract"]
    return {
        "schema_version": contract["schema_version"],
        "interpretations": [],
        "hypotheses": [],
        "recommendation_ids": [],
        "evidence_needed_ids": [],
        "insufficient_evidence_ids": [],
    }


def test_minimal_valid_response_can_be_built_only_from_context():
    report_facts = facts()
    context = build_assisted_context(report_facts)

    reading = parse_assisted_reading(
        json.dumps(minimal_response_from_context(context)), report_facts
    )

    assert reading.schema_version == context["contract"]["schema_version"]


def test_every_offered_structured_option_is_accepted_with_its_documented_relations():
    report_facts = facts()
    context = build_assisted_context(report_facts)
    contract = context["contract"]

    for item_id, specification in contract["interpretations"].items():
        response = minimal_response_from_context(context)
        response["interpretations"] = [
            {"interpretation_id": item_id, "fact_refs": specification["fact_refs"]}
        ]
        parse_assisted_reading(json.dumps(response), report_facts)

    for item_id, specification in contract["hypotheses"].items():
        response = minimal_response_from_context(context)
        response["hypotheses"] = [
            {
                "hypothesis_id": item_id,
                "fact_refs": specification["fact_refs"],
                "validation_needed_id": specification["validation_needed_ids"][0],
            }
        ]
        parse_assisted_reading(json.dumps(response), report_facts)

    for field in (
        "recommendation_ids",
        "evidence_needed_ids",
        "insufficient_evidence_ids",
    ):
        for item_id in contract[field]:
            response = minimal_response_from_context(context)
            response[field] = [item_id]
            parse_assisted_reading(json.dumps(response), report_facts)


def test_context_relations_reference_only_available_facts():
    context = build_assisted_context(facts())
    available = set(context["evidence"]["facts"])

    for specification in context["contract"]["interpretations"].values():
        assert set(specification["fact_refs"]) <= available
    for specification in context["contract"]["hypotheses"].values():
        assert set(specification["fact_refs"]) <= available


def test_context_documents_exact_shape_limits_duplicates_and_empty_lists():
    contract = build_assisted_context(facts())["contract"]
    response = contract["response"]

    assert response["additional_fields_allowed"] is False
    assert response["empty_lists_allowed"] is True
    assert response["duplicate_items_allowed"] is False
    assert set(response["required_fields"]) == set(valid_response())
    assert set(response["interpretation_fields"]) == {"interpretation_id", "fact_refs"}
    assert set(response["hypothesis_fields"]) == {
        "hypothesis_id",
        "fact_refs",
        "validation_needed_id",
    }
    assert contract["limits"] == {
        "interpretations": 3,
        "hypotheses": 2,
        "recommendations": 3,
        "evidence_needed": 4,
        "insufficient_evidence": 4,
        "fact_refs_per_item": 4,
    }


def test_valid_structured_reading_is_parsed_without_provider_numbers():
    reading = parse_assisted_reading(json.dumps(valid_response()), facts())

    assert reading.schema_version == "2.0"
    assert reading.interpretations[0].interpretation_id == "lexical_concentration_for_review"
    assert reading.recommendation_ids == ("inspect_ranked_ngrams",)


def test_multiple_distinct_interpretations_are_valid():
    response = valid_response()
    response["interpretations"].append(
        {
            "interpretation_id": "confidence_requires_independent_evaluation",
            "fact_refs": ["model.mean_local_confidence"],
        }
    )
    reading = parse_assisted_reading(json.dumps(response), facts())
    assert len(reading.interpretations) == 2


def test_duplicate_interpretations_are_rejected():
    response = valid_response()
    response["interpretations"].append(dict(response["interpretations"][0]))
    with pytest.raises(ReportContractError, match="Duplicate") as exc_info:
        parse_assisted_reading(json.dumps(response), facts())
    assert exc_info.value.code == "duplicate_interpretation"


def test_duplicates_for_other_structured_lists_are_rejected():
    response = valid_response()
    response["hypotheses"].append(dict(response["hypotheses"][0]))
    with pytest.raises(ReportContractError) as exc_info:
        parse_assisted_reading(json.dumps(response), facts())
    assert exc_info.value.code == "duplicate_hypothesis"

    response = valid_response()
    response["recommendation_ids"] *= 2
    with pytest.raises(ReportContractError) as exc_info:
        parse_assisted_reading(json.dumps(response), facts())
    assert exc_info.value.code == "duplicate_recommendation"

    response = valid_response()
    response["interpretations"][0]["fact_refs"] *= 2
    with pytest.raises(ReportContractError) as exc_info:
        parse_assisted_reading(json.dumps(response), facts())
    assert exc_info.value.code == "duplicate_fact_ref"


@pytest.mark.parametrize("extra", [{"metric": 41}, {"deadline": "soon"}, {"category": "delivery"}])
def test_additional_fields_are_rejected(extra):
    response = valid_response() | extra
    with pytest.raises(ReportContractError, match="additional fields"):
        parse_assisted_reading(json.dumps(response), facts())


def test_unknown_fact_reference_is_rejected():
    response = valid_response()
    response["hypotheses"][0]["fact_refs"] = ["sentiment.cause.delivery"]
    with pytest.raises(ReportContractError, match="does not exist") as exc_info:
        parse_assisted_reading(json.dumps(response), facts())
    assert exc_info.value.code == "unknown_fact_ref"


@pytest.mark.parametrize(
    "forbidden_field",
    [
        "Estas señales explican el 41% de los comentarios.",
        "La meta debería ser reducir la negatividad a la mitad en 30 días.",
        "El impacto esperado es USD cinco mil.",
        "Consultar https://example.com para validar.",
    ],
)
def test_any_provider_authored_free_text_is_rejected(forbidden_field):
    response = valid_response()
    response["hypotheses"][0]["statement"] = forbidden_field
    with pytest.raises(ReportContractError, match="hypothesis fields"):
        parse_assisted_reading(json.dumps(response), facts())


def test_hypothesis_without_validation_needed_is_rejected():
    response = valid_response()
    del response["hypotheses"][0]["validation_needed_id"]
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
    with pytest.raises(ReportContractError, match="ineligible") as exc_info:
        parse_assisted_reading(json.dumps(response), empty_facts)
    assert exc_info.value.code == "ineligible_recommendation"


def test_schema_version_rejection_has_safe_rule_code():
    response = valid_response()
    response["schema_version"] = "1.0"

    with pytest.raises(ReportContractError) as exc_info:
        parse_assisted_reading(json.dumps(response), facts())

    assert exc_info.value.code == "invalid_schema_version"


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
    contract = build_assisted_context(empty_facts)["contract"]
    assert "lexical_concentration_for_review" not in contract["interpretations"]
    assert "lexical_patterns_may_reflect_shared_issue" not in contract["hypotheses"]
    assert "inspect_ranked_ngrams" not in contract["recommendation_ids"]
    assert "no_negative_comments" in contract["insufficient_evidence_ids"]
    assert "no_lexical_terms" in contract["insufficient_evidence_ids"]
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

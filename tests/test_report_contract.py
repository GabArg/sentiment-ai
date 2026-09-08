from __future__ import annotations

import pandas as pd

from src.report_contract import build_report_facts, fact_value
from tests.test_reporting import metrics_fixture, pareto_fixture


def test_fact_registry_types_sentiment_values_and_denominators():
    facts = build_report_facts(metrics_fixture(), pareto_fixture())

    assert fact_value(facts, "dataset.total_comments") == 10
    negative_share = facts.facts["sentiment.negative.share"]
    assert negative_share.value == 40.0
    assert negative_share.unit == "percent"
    assert negative_share.numerator_fact == "sentiment.negative.count"
    assert negative_share.denominator_fact == "dataset.total_comments"


def test_lexical_denominator_is_selected_document_frequency_sum():
    pareto = pareto_fixture()
    facts = build_report_facts(metrics_fixture(), pareto)

    denominator = facts.facts["lexical.selected_frequency_sum"]
    assert denominator.value == 4
    assert denominator.unit == "selected_ngram_document_mentions"
    assert "not unique comments" in denominator.definition
    assert "up to 15" in denominator.definition
    assert facts.facts["lexical.rank.1.share"].denominator_fact == denominator.fact_id


def test_overlapping_ngram_frequencies_are_never_typed_as_unique_comments():
    pareto = pd.DataFrame(
        {
            "topic": ["llego tarde", "tarde"],
            "frequency": [3, 2],
            "percentage": [60.0, 40.0],
            "cumulative_percentage": [60.0, 100.0],
            "within_80_percent": [True, True],
        }
    )
    metrics = metrics_fixture()
    metrics["total"] = 3
    facts = build_report_facts(metrics, pareto)

    assert fact_value(facts, "lexical.selected_frequency_sum") == 5
    assert facts.facts["lexical.selected_frequency_sum"].unit != "comments"


def test_empty_pareto_has_explicit_zero_denominator_and_no_rank_facts():
    facts = build_report_facts(metrics_fixture(), pd.DataFrame())

    assert fact_value(facts, "lexical.selected_frequency_sum") == 0
    assert not any(fact_id.startswith("lexical.rank.") for fact_id in facts.facts)


def test_ai_payload_contains_no_comment_text_csv_columns_or_topic_labels():
    pareto = pareto_fixture()
    pareto.loc[0, "topic"] = "private@example.com entrega tarde"
    payload = build_report_facts(metrics_fixture(), pareto).as_ai_payload()
    serialized = str(payload)

    assert "private@example.com" not in serialized
    assert "entrega tarde" not in serialized
    assert "topic" not in serialized
    assert set(payload) == {"schema_version", "facts", "capabilities"}


def test_technical_signal_is_not_business_severity():
    facts = build_report_facts(metrics_fixture(), pareto_fixture())
    signal = facts.facts["technical.high_confidence_negative.count"]

    assert signal.value == 2
    assert signal.unit == "comments"
    assert "technical signal" in signal.definition
    assert "not validated business severity" in signal.definition

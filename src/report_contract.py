"""Typed evidence and structured assisted-reading contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class ReportFact:
    """One locally calculated fact with explicit evidence semantics."""

    fact_id: str
    value: int | float
    unit: str
    population: str
    definition: str
    numerator_fact: str | None = None
    denominator_fact: str | None = None

    def as_payload(self) -> dict[str, object]:
        return {key: value for key, value in asdict(self).items() if value is not None}


@dataclass(frozen=True)
class ReportFacts:
    """Versioned registry of facts available to reporting code."""

    schema_version: str
    facts: dict[str, ReportFact]
    capabilities: dict[str, bool]

    def as_ai_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "facts": {fact_id: fact.as_payload() for fact_id, fact in self.facts.items()},
            "capabilities": dict(self.capabilities),
        }


def build_report_facts(metrics: dict[str, object], pareto: pd.DataFrame) -> ReportFacts:
    """Build immutable reporting facts without changing analytical calculations."""
    facts: dict[str, ReportFact] = {}
    total = int(metrics["total"])
    facts["dataset.total_comments"] = ReportFact(
        fact_id="dataset.total_comments",
        value=total,
        unit="comments",
        population="rows successfully analyzed in the active batch",
        definition="Number of comments included in the current analysis.",
    )

    counts = metrics["counts"]
    percentages = metrics["percentages"]
    for label, slug in (("Negativo", "negative"), ("Neutro", "neutral"), ("Positivo", "positive")):
        count_id = f"sentiment.{slug}.count"
        facts[count_id] = ReportFact(
            fact_id=count_id,
            value=int(counts[label]),
            unit="comments",
            population="comments classified by the final sentiment pipeline",
            definition=f"Comments classified as {label.casefold()}.",
        )
        share_id = f"sentiment.{slug}.share"
        facts[share_id] = ReportFact(
            fact_id=share_id,
            value=round(float(percentages[label]), 2),
            unit="percent",
            population="comments classified by the final sentiment pipeline",
            numerator_fact=count_id,
            denominator_fact="dataset.total_comments",
            definition=f"Share of analyzed comments classified as {label.casefold()}.",
        )

    facts["model.mean_local_confidence"] = ReportFact(
        fact_id="model.mean_local_confidence",
        value=round(float(metrics["mean_confidence"]), 4),
        unit="probability",
        population="local model predictions in the active batch",
        definition=(
            "Mean internal confidence of the local classifier; not accuracy, precision, "
            "calibration, business severity, or a guarantee of correctness."
        ),
    )
    facts["technical.high_confidence_negative.threshold"] = ReportFact(
        fact_id="technical.high_confidence_negative.threshold",
        value=round(float(metrics["critical_confidence_threshold"]), 4),
        unit="probability",
        population="local model predictions in the active batch",
        definition="Upper-quartile local-confidence threshold calculated over the full active batch.",
    )
    facts["technical.high_confidence_negative.count"] = ReportFact(
        fact_id="technical.high_confidence_negative.count",
        value=int(metrics["critical_negative_count"]),
        unit="comments",
        population="comments classified as negative in the active batch",
        definition=(
            "Negative predictions at or above the batch upper-quartile local-confidence "
            "threshold; a technical signal, not validated business severity."
        ),
        denominator_fact="dataset.total_comments",
    )

    selected_frequency_sum = int(pareto["frequency"].sum()) if not pareto.empty else 0
    facts["lexical.selected_frequency_sum"] = ReportFact(
        fact_id="lexical.selected_frequency_sum",
        value=selected_frequency_sum,
        unit="selected_ngram_document_mentions",
        population="selected n-grams from comments classified as negative",
        definition=(
            "Sum of document frequencies for the selected n-grams (up to 15 by default, "
            "after redundant-unigram suppression); not unique comments and not every "
            "initially extracted mention."
        ),
    )
    for rank, (_, row) in enumerate(pareto.head(15).iterrows(), start=1):
        frequency_id = f"lexical.rank.{rank}.frequency"
        facts[frequency_id] = ReportFact(
            fact_id=frequency_id,
            value=int(row.frequency),
            unit="selected_ngram_document_mentions",
            population="selected n-grams from comments classified as negative",
            definition="Document frequency of this ranked selected n-gram.",
        )
        facts[f"lexical.rank.{rank}.share"] = ReportFact(
            fact_id=f"lexical.rank.{rank}.share",
            value=round(float(row.percentage), 2),
            unit="percent",
            population="selected n-gram document mentions",
            numerator_fact=frequency_id,
            denominator_fact="lexical.selected_frequency_sum",
            definition="Share of the selected n-gram document-frequency sum.",
        )
        facts[f"lexical.rank.{rank}.cumulative_share"] = ReportFact(
            fact_id=f"lexical.rank.{rank}.cumulative_share",
            value=round(float(row.cumulative_percentage), 2),
            unit="percent",
            population="selected n-gram document mentions",
            denominator_fact="lexical.selected_frequency_sum",
            definition="Cumulative share through this rank using the selected-frequency sum.",
        )

    return ReportFacts(
        schema_version="2.0",
        facts=facts,
        capabilities={
            "semantic_categories": False,
            "unique_comment_union_by_terms": False,
            "time_comparison": False,
            "business_targets": False,
            "business_severity": False,
        },
    )


def fact_value(facts: ReportFacts, fact_id: str) -> Any:
    """Return a fact value and fail loudly for an internal unknown identifier."""
    return facts.facts[fact_id].value

"""Typed evidence and structured assisted-reading contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import Any

import pandas as pd


ASSISTED_READING_SCHEMA_VERSION = "2.0"
MAX_INTERPRETATIONS = 3
MAX_HYPOTHESES = 2
MAX_RECOMMENDATIONS = 3


class ReportContractError(ValueError):
    """A provider response does not satisfy the assisted-reading contract."""


@dataclass(frozen=True)
class ReportFact:
    """One locally calculated fact with explicit evidence semantics."""

    fact_id: str
    value: int | float | str
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


@dataclass(frozen=True)
class InterpretationSelection:
    interpretation_id: str
    fact_refs: tuple[str, ...]


@dataclass(frozen=True)
class ReportHypothesis:
    hypothesis_id: str
    fact_refs: tuple[str, ...]
    validation_needed_id: str


@dataclass(frozen=True)
class AssistedReading:
    schema_version: str
    interpretations: tuple[InterpretationSelection, ...]
    hypotheses: tuple[ReportHypothesis, ...]
    recommendation_ids: tuple[str, ...]
    evidence_needed_ids: tuple[str, ...]
    insufficient_evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class CatalogEntry:
    text: str
    fact_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class HypothesisCatalogEntry:
    text: str
    fact_refs: tuple[str, ...]
    validation_needed_ids: tuple[str, ...]


INTERPRETATION_CATALOG = {
    "review_negative_distribution": CatalogEntry(
        "La distribución observada permite identificar el volumen clasificado como negativo; su evaluación requiere contraste humano.",
        ("sentiment.negative.count", "sentiment.negative.share"),
    ),
    "lexical_concentration_for_review": CatalogEntry(
        "La concentración léxica puede orientar una revisión cualitativa inicial, sin identificar categorías ni causas.",
        ("lexical.selected_frequency_sum",),
    ),
    "confidence_requires_independent_evaluation": CatalogEntry(
        "La confianza local aporta contexto técnico, pero la calidad del modelo debe evaluarse con etiquetas independientes y métricas por clase.",
        ("model.mean_local_confidence",),
    ),
    "technical_signal_requires_human_review": CatalogEntry(
        "La señal de negativos de alta confianza sirve para priorizar una revisión técnica, no para medir severidad de negocio.",
        ("technical.high_confidence_negative.count",),
    ),
}


HYPOTHESIS_CATALOG = {
    "lexical_patterns_may_reflect_shared_issue": HypothesisCatalogEntry(
        "Los patrones léxicos observados podrían corresponder a situaciones relacionadas, pero no permiten definir una categoría.",
        ("lexical.selected_frequency_sum",),
        ("qualitative_comment_review", "semantic_category_validation"),
    ),
    "negative_predictions_may_include_model_errors": HypothesisCatalogEntry(
        "Parte de las predicciones negativas podría requerir corrección después de una revisión humana.",
        ("sentiment.negative.count",),
        ("independent_labeled_evaluation", "qualitative_comment_review"),
    ),
    "technical_signal_may_support_sample_review": HypothesisCatalogEntry(
        "La señal técnica podría ser útil para seleccionar una muestra de revisión, sin indicar severidad empresarial.",
        ("technical.high_confidence_negative.count",),
        ("qualitative_comment_review", "independent_labeled_evaluation"),
    ),
}


RECOMMENDATION_CATALOG = {
    "review_negative_sample": "Revisar una muestra de comentarios clasificados como negativos y contrastar sus etiquetas con criterio humano.",
    "inspect_ranked_ngrams": "Examinar los comentarios asociados a los términos frecuentes antes de interpretar su significado.",
    "validate_lexical_groups_manually": "Validar manualmente si varios términos describen una categoría útil para el negocio.",
    "investigate_causes_with_evidence": "Investigar posibles causas mediante evidencia adicional antes de definir acciones específicas.",
    "independent_model_evaluation": "Evaluar el modelo con un conjunto independiente y métricas por clase.",
    "define_business_objectives": "Definir objetivos, responsables y datos de referencia antes de establecer metas.",
    "collect_temporal_baseline": "Incorporar períodos comparables antes de interpretar tendencias.",
}


EVIDENCE_NEEDED_CATALOG = {
    "independent_labeled_evaluation": "Etiquetas humanas independientes para medir desempeño por clase.",
    "qualitative_comment_review": "Revisión cualitativa de comentarios asociados a las señales observadas.",
    "semantic_category_validation": "Taxonomía y anotación humana para validar categorías semánticas.",
    "temporal_baseline": "Períodos comparables para evaluar cambios en el tiempo.",
    "business_objectives": "Objetivos y línea de base definidos por responsables del negocio.",
}


INSUFFICIENT_EVIDENCE_CATALOG = {
    "no_negative_comments": "No hay comentarios clasificados como negativos en el lote.",
    "no_lexical_terms": "No hay términos seleccionados suficientes para una lectura léxica.",
    "no_semantic_categories": "No se calcularon categorías semánticas verificadas.",
    "no_time_comparison": "No hay períodos comparables para interpretar tendencias.",
    "no_business_targets": "No se proporcionaron objetivos ni metas de negocio.",
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

    ratio = float(metrics["positive_negative_ratio"])
    facts["sentiment.positive_negative_ratio"] = ReportFact(
        fact_id="sentiment.positive_negative_ratio",
        value=ratio if ratio != float("inf") else "undefined_no_negative_comments",
        unit="positive_comments_per_negative_comment",
        population="comments classified by the final sentiment pipeline",
        numerator_fact="sentiment.positive.count",
        denominator_fact="sentiment.negative.count",
        definition="Ratio of positive predictions to negative predictions.",
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
    )

    selected_frequency_sum = int(pareto["frequency"].sum()) if not pareto.empty else 0
    facts["lexical.selected_frequency_sum"] = ReportFact(
        fact_id="lexical.selected_frequency_sum",
        value=selected_frequency_sum,
        unit="selected_ngram_document_mentions",
        population="selected n-grams from comments classified as negative",
        definition=(
            "Sum of document frequencies for the selected n-grams supplied by the Pareto "
            "pipeline (up to 15 by default, after redundant-unigram suppression); not "
            "unique comments and not every initially extracted mention."
        ),
    )
    within = pareto[pareto.get("within_80_percent", False)] if not pareto.empty else pareto
    facts["lexical.pareto_block_term_count"] = ReportFact(
        fact_id="lexical.pareto_block_term_count",
        value=len(within),
        unit="selected_ngrams",
        population="selected n-grams from comments classified as negative",
        definition="Number of ranked selected n-grams in the existing Pareto 80 percent block.",
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


def eligible_interpretation_ids(facts: ReportFacts) -> set[str]:
    eligible = {"confidence_requires_independent_evaluation"}
    if fact_value(facts, "sentiment.negative.count") > 0:
        eligible.add("review_negative_distribution")
    if fact_value(facts, "lexical.selected_frequency_sum") > 0:
        eligible.add("lexical_concentration_for_review")
    if fact_value(facts, "technical.high_confidence_negative.count") > 0:
        eligible.add("technical_signal_requires_human_review")
    return eligible


def eligible_recommendation_ids(facts: ReportFacts) -> set[str]:
    eligible = {"independent_model_evaluation", "define_business_objectives"}
    if not facts.capabilities["time_comparison"]:
        eligible.add("collect_temporal_baseline")
    if fact_value(facts, "sentiment.negative.count") > 0:
        eligible.update({"review_negative_sample", "investigate_causes_with_evidence"})
    if fact_value(facts, "lexical.selected_frequency_sum") > 0:
        eligible.update({"inspect_ranked_ngrams", "validate_lexical_groups_manually"})
    return eligible


def eligible_hypothesis_ids(facts: ReportFacts) -> set[str]:
    eligible = set()
    if fact_value(facts, "sentiment.negative.count") > 0:
        eligible.add("negative_predictions_may_include_model_errors")
    if fact_value(facts, "lexical.selected_frequency_sum") > 0:
        eligible.add("lexical_patterns_may_reflect_shared_issue")
    if fact_value(facts, "technical.high_confidence_negative.count") > 0:
        eligible.add("technical_signal_may_support_sample_review")
    return eligible


def eligible_insufficient_evidence_ids(facts: ReportFacts) -> set[str]:
    eligible = set()
    if fact_value(facts, "sentiment.negative.count") == 0:
        eligible.add("no_negative_comments")
    if fact_value(facts, "lexical.selected_frequency_sum") == 0:
        eligible.add("no_lexical_terms")
    if not facts.capabilities["semantic_categories"]:
        eligible.add("no_semantic_categories")
    if not facts.capabilities["time_comparison"]:
        eligible.add("no_time_comparison")
    if not facts.capabilities["business_targets"]:
        eligible.add("no_business_targets")
    return eligible


def build_assisted_context(facts: ReportFacts) -> dict[str, object]:
    """Expose facts and only the catalog choices eligible for this batch."""
    return {
        "contract": {
            "schema_version": ASSISTED_READING_SCHEMA_VERSION,
            "interpretation_ids": sorted(eligible_interpretation_ids(facts)),
            "hypothesis_ids": sorted(eligible_hypothesis_ids(facts)),
            "recommendation_ids": sorted(eligible_recommendation_ids(facts)),
            "evidence_needed_ids": sorted(EVIDENCE_NEEDED_CATALOG),
            "insufficient_evidence_ids": sorted(eligible_insufficient_evidence_ids(facts)),
            "limits": {
                "interpretations": MAX_INTERPRETATIONS,
                "hypotheses": MAX_HYPOTHESES,
                "recommendations": MAX_RECOMMENDATIONS,
            },
        },
        "evidence": facts.as_ai_payload(),
    }


def parse_assisted_reading(raw: str, facts: ReportFacts) -> AssistedReading:
    """Parse and validate a provider response without repairing it."""
    try:
        data = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ReportContractError("The provider response is not valid JSON.") from exc
    if not isinstance(data, dict):
        raise ReportContractError("The provider response must be an object.")

    expected_keys = {
        "schema_version",
        "interpretations",
        "hypotheses",
        "recommendation_ids",
        "evidence_needed_ids",
        "insufficient_evidence_ids",
    }
    if set(data) != expected_keys:
        raise ReportContractError("The provider response has missing or additional fields.")
    if data["schema_version"] != ASSISTED_READING_SCHEMA_VERSION:
        raise ReportContractError("Unsupported assisted-reading schema version.")

    interpretations = _parse_interpretations(data["interpretations"], facts)
    hypotheses = _parse_hypotheses(data["hypotheses"], facts)
    recommendation_ids = _parse_id_list(
        data["recommendation_ids"],
        "recommendation_ids",
        eligible_recommendation_ids(facts),
        MAX_RECOMMENDATIONS,
    )
    evidence_ids = _parse_id_list(
        data["evidence_needed_ids"],
        "evidence_needed_ids",
        set(EVIDENCE_NEEDED_CATALOG),
        4,
    )
    insufficient_ids = _parse_id_list(
        data["insufficient_evidence_ids"],
        "insufficient_evidence_ids",
        eligible_insufficient_evidence_ids(facts),
        4,
    )
    return AssistedReading(
        schema_version=ASSISTED_READING_SCHEMA_VERSION,
        interpretations=interpretations,
        hypotheses=hypotheses,
        recommendation_ids=recommendation_ids,
        evidence_needed_ids=evidence_ids,
        insufficient_evidence_ids=insufficient_ids,
    )


def _parse_interpretations(value: object, facts: ReportFacts) -> tuple[InterpretationSelection, ...]:
    if not isinstance(value, list) or len(value) > MAX_INTERPRETATIONS:
        raise ReportContractError("Invalid interpretations collection.")
    eligible = eligible_interpretation_ids(facts)
    parsed = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {"interpretation_id", "fact_refs"}:
            raise ReportContractError("Invalid interpretation fields.")
        interpretation_id = item["interpretation_id"]
        if not isinstance(interpretation_id, str) or interpretation_id not in eligible:
            raise ReportContractError("Unknown or ineligible interpretation.")
        refs = _parse_fact_refs(item["fact_refs"], facts)
        allowed_refs = set(INTERPRETATION_CATALOG[interpretation_id].fact_refs)
        if not refs or not set(refs).issubset(allowed_refs):
            raise ReportContractError("Interpretation references do not match its catalog entry.")
        parsed.append(InterpretationSelection(interpretation_id, refs))
    if len({item.interpretation_id for item in parsed}) != len(parsed):
        raise ReportContractError("Duplicate interpretations are not allowed.")
    return tuple(parsed)


def _parse_hypotheses(value: object, facts: ReportFacts) -> tuple[ReportHypothesis, ...]:
    if not isinstance(value, list) or len(value) > MAX_HYPOTHESES:
        raise ReportContractError("Invalid hypotheses collection.")
    parsed = []
    eligible = eligible_hypothesis_ids(facts)
    for item in value:
        expected = {"hypothesis_id", "fact_refs", "validation_needed_id"}
        if not isinstance(item, dict) or set(item) != expected:
            raise ReportContractError("Invalid hypothesis fields.")
        hypothesis_id = item["hypothesis_id"]
        validation_id = item["validation_needed_id"]
        if not isinstance(hypothesis_id, str) or hypothesis_id not in eligible:
            raise ReportContractError("Unknown or ineligible hypothesis.")
        if not isinstance(validation_id, str):
            raise ReportContractError("Invalid hypothesis validation identifier.")
        refs = _parse_fact_refs(item["fact_refs"], facts)
        catalog = HYPOTHESIS_CATALOG[hypothesis_id]
        if not refs or not set(refs).issubset(set(catalog.fact_refs)):
            raise ReportContractError("Hypothesis references do not match its catalog entry.")
        if validation_id not in catalog.validation_needed_ids:
            raise ReportContractError("Hypothesis validation is not eligible for its catalog entry.")
        parsed.append(ReportHypothesis(hypothesis_id, refs, validation_id))
    return tuple(parsed)


def _parse_fact_refs(value: object, facts: ReportFacts) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) > 4 or not all(isinstance(item, str) for item in value):
        raise ReportContractError("Invalid fact references.")
    refs = tuple(dict.fromkeys(value))
    if any(ref not in facts.facts for ref in refs):
        raise ReportContractError("A referenced fact does not exist.")
    return refs


def _parse_id_list(
    value: object, field: str, allowed: set[str], maximum: int
) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) > maximum or not all(isinstance(item, str) for item in value):
        raise ReportContractError(f"Invalid {field} collection.")
    result = tuple(dict.fromkeys(value))
    if any(item not in allowed for item in result):
        raise ReportContractError(f"Unknown or ineligible value in {field}.")
    return result

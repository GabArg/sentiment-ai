"""Deterministic and AI-ready executive reporting."""

from __future__ import annotations

import json

import pandas as pd

from src.report_contract import (
    EVIDENCE_NEEDED_CATALOG,
    HYPOTHESIS_CATALOG,
    INSUFFICIENT_EVIDENCE_CATALOG,
    INTERPRETATION_CATALOG,
    RECOMMENDATION_CATALOG,
    AssistedReading,
    build_assisted_context,
    build_report_facts,
    fact_value,
)

REPORT_PROMPT = """Seleccioná una lectura asistida breve a partir del contexto agregado.

Respondé únicamente con un objeto JSON, sin Markdown ni texto adicional, con exactamente estas claves:
schema_version, interpretations, hypotheses, recommendation_ids, evidence_needed_ids, insufficient_evidence_ids.

Reglas:
- Usá solamente identificadores elegibles incluidos en CONTEXTO.contract.
- Cada interpretación contiene sólo interpretation_id y fact_refs.
- Cada hipótesis contiene sólo hypothesis_id, fact_refs y validation_needed_id.
- No generes texto libre. Todo el contenido visible pertenece a catálogos locales versionados.
- No calcules, combines, reformules ni repitas valores. La aplicación renderiza todos los hechos localmente.
- Los n-gramas son señales léxicas, no categorías ni causas.
- La confianza local no es accuracy, precisión ni garantía de corrección.
- Si falta evidencia, seleccioná los identificadores correspondientes; no completes supuestos.

Ejemplo de forma, no de contenido:
{{
  "schema_version": "2.0",
  "interpretations": [{{"interpretation_id": "identificador_elegible", "fact_refs": ["hecho.existente"]}}],
  "hypotheses": [],
  "recommendation_ids": ["identificador_elegible"],
  "evidence_needed_ids": ["identificador_elegible"],
  "insufficient_evidence_ids": ["identificador_elegible"]
}}

CONTEXTO:
{context}
"""


def generate_deterministic_report(
    metrics: dict[str, object],
    pareto: pd.DataFrame,
) -> str:
    facts = build_report_facts(metrics, pareto)
    total = int(fact_value(facts, "dataset.total_comments"))
    principal = pareto.head(3)
    within = pareto[pareto.get("within_80_percent", False)] if not pareto.empty else pareto

    term_lines = (
        [f"{index + 1}. **{row.topic}** — {int(row.frequency)} menciones." for index, row in principal.iterrows()]
        if not principal.empty
        else ["No hay suficientes comentarios negativos para extraer términos frecuentes."]
    )
    negative_pct = float(fact_value(facts, "sentiment.negative.share"))
    positive_pct = float(fact_value(facts, "sentiment.positive.share"))
    if negative_pct >= 40:
        opportunity = "El volumen negativo merece una revisión de los términos más frecuentes y de una muestra de comentarios asociados."
    elif negative_pct >= 20:
        opportunity = "Existe un bloque negativo relevante; conviene revisar los términos dominantes y validar posibles categorías manualmente."
    else:
        opportunity = "La señal negativa es acotada; conviene revisar una muestra de los comentarios clasificados como negativos."

    ratio = fact_value(facts, "sentiment.positive_negative_ratio")
    ratio_text = (
        "sin negativos observados"
        if isinstance(ratio, str)
        else f"{float(ratio):.2f} positivos por cada negativo"
    )
    pareto_text = (
        f"{len(within)} términos forman el bloque que alcanza aproximadamente el 80% acumulado de las menciones de n-gramas."
        if not within.empty
        else "No se pudo calcular un Pareto por falta de temas negativos."
    )
    return "\n".join(
        [
            "# Informe ejecutivo determinístico",
            "",
            "## Resumen ejecutivo",
            f"Se analizaron **{total:,} comentarios**. La confianza media del modelo fue **{float(fact_value(facts, 'model.mean_local_confidence')):.1%}**.",
            "",
            "## Distribución",
            f"- Positivos: **{int(fact_value(facts, 'sentiment.positive.count')):,}** ({positive_pct:.1f}%).",
            f"- Neutros: **{int(fact_value(facts, 'sentiment.neutral.count')):,}** ({float(fact_value(facts, 'sentiment.neutral.share')):.1f}%).",
            f"- Negativos: **{int(fact_value(facts, 'sentiment.negative.count')):,}** ({negative_pct:.1f}%).",
            f"- Ratio positivo/negativo: **{ratio_text}**.",
            "",
            "## Principales términos negativos",
            *term_lines,
            "",
            "## Pareto",
            pareto_text,
            "",
            "## Oportunidades",
            opportunity,
            "",
            "## Limitaciones",
            "Las etiquetas y probabilidades provienen de un modelo TF-IDF + regresión logística y pueden contener errores. "
            "Los términos son n-gramas frecuentes, no categorías semánticas ni causas verificadas. "
            "La confianza local no es una medida de precisión. La señal técnica de negativos de alta confianza no valida severidad de negocio. "
            "Este informe no reemplaza una revisión cualitativa ni una evaluación independiente del modelo.",
        ]
    )


def prepare_ai_context(
    metrics: dict[str, object],
    pareto: pd.DataFrame,
) -> dict[str, object]:
    return build_assisted_context(build_report_facts(metrics, pareto))


def build_ai_prompt(context: dict[str, object]) -> str:
    return REPORT_PROMPT.format(context=json.dumps(context, ensure_ascii=False, indent=2))


def generate_assisted_markdown(reading: AssistedReading) -> str:
    """Render validated assisted content exclusively from local catalogs."""
    lines = ["## Lectura asistida", "", "Contenido complementario generado a partir de datos agregados."]
    if reading.interpretations:
        lines.extend(["", "### Interpretaciones descriptivas"])
        lines.extend(
            f"- {INTERPRETATION_CATALOG[item.interpretation_id].text}"
            for item in reading.interpretations
        )
    if reading.hypotheses:
        lines.extend(["", "### Hipótesis no verificadas"])
        for hypothesis in reading.hypotheses:
            lines.append(
                f"- **Hipótesis no verificada:** {HYPOTHESIS_CATALOG[hypothesis.hypothesis_id].text}"
            )
            lines.append(
                f"  - Validación necesaria: {EVIDENCE_NEEDED_CATALOG[hypothesis.validation_needed_id]}"
            )
    if reading.recommendation_ids:
        lines.extend(["", "### Recomendaciones condicionadas"])
        lines.extend(f"- {RECOMMENDATION_CATALOG[item]}" for item in reading.recommendation_ids)
    if reading.evidence_needed_ids:
        lines.extend(["", "### Evidencia adicional necesaria"])
        lines.extend(f"- {EVIDENCE_NEEDED_CATALOG[item]}" for item in reading.evidence_needed_ids)
    if reading.insufficient_evidence_ids:
        lines.extend(["", "### Evidencia no disponible"])
        lines.extend(
            f"- {INSUFFICIENT_EVIDENCE_CATALOG[item]}"
            for item in reading.insufficient_evidence_ids
        )
    lines.extend(
        [
            "",
            "### Alcance",
            "La lectura asistida no modifica los hechos calculados y no valida categorías, causas ni impacto de negocio.",
        ]
    )
    return "\n".join(lines)


def compose_report_document(deterministic_report: str, reading: AssistedReading) -> str:
    """Compose the downloadable document from local deterministic content."""
    return f"{deterministic_report.rstrip()}\n\n---\n\n{generate_assisted_markdown(reading)}\n"


def estimate_payload(context: dict[str, object]) -> dict[str, int]:
    serialized = json.dumps(context, ensure_ascii=False)
    return {"characters": len(serialized), "approximate_tokens": max(1, len(serialized) // 4)}


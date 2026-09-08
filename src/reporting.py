"""Deterministic and AI-ready executive reporting."""

from __future__ import annotations

import json
import math
import re

import pandas as pd


REPORT_SECTIONS = (
    "Resumen ejecutivo",
    "Distribución observada",
    "Señales léxicas",
    "Interpretación y próximos pasos",
    "Limitaciones del análisis",
)


REPORT_PROMPT = """Actuá como analista de experiencia del cliente y redactá un informe ejecutivo en español.

Usá exclusivamente los datos agregados incluidos en CONTEXTO y respetá su CONTRATO_DE_EVIDENCIA:
- Los conteos y porcentajes de sentimiento son hechos calculados sobre los comentarios clasificados.
- La confianza media es una estimación interna del modelo local. No es accuracy, precisión, calibración ni garantía de corrección.
- El Pareto cuenta menciones de n-gramas en comentarios clasificados como negativos. Sus porcentajes usan como denominador el total de menciones de n-gramas, no el total de comentarios.
- Los n-gramas no son categorías semánticas, causas raíz ni severidad de negocio. No conviertas rangos o menciones en problemas de negocio.
- La señal técnica de negativos de alta confianza responde únicamente a la regla indicada; no significa que sean casos críticos para el negocio.
- No hay tendencias, períodos comparables, impacto económico, objetivos, plazos, responsables ni presupuestos salvo que CONTEXTO los declare expresamente.
- No inventes métricas, cifras ni metas numéricas. Si falta evidencia, indicá que la decisión o validación queda pendiente.
- Podés formular hipótesis sólo si las marcás como hipótesis a validar. Las recomendaciones deben proponer revisión o investigación, no afirmar decisiones ya tomadas.
- No solicites ni supongas datos personales.

Entregá Markdown breve, profesional y accionable con exactamente estas secciones:
## Resumen ejecutivo
## Distribución observada
## Señales léxicas
## Interpretación y próximos pasos
## Limitaciones del análisis

Usá viñetas, no listas numeradas. Cada cifra debe coincidir con CONTEXTO. Al citar un porcentaje, nombrá su denominador. Evitá lenguaje promocional.

CONTEXTO:
{context}
"""


def generate_deterministic_report(
    metrics: dict[str, object],
    pareto: pd.DataFrame,
) -> str:
    counts = metrics["counts"]
    percentages = metrics["percentages"]
    total = int(metrics["total"])
    principal = pareto.head(3)
    within = pareto[pareto.get("within_80_percent", False)] if not pareto.empty else pareto

    term_lines = (
        [f"{index + 1}. **{row.topic}** — {int(row.frequency)} menciones." for index, row in principal.iterrows()]
        if not principal.empty
        else ["No hay suficientes comentarios negativos para extraer términos frecuentes."]
    )
    negative_pct = float(percentages["Negativo"])
    positive_pct = float(percentages["Positivo"])
    if negative_pct >= 40:
        opportunity = "El volumen negativo merece una revisión de los términos más frecuentes y de una muestra de comentarios asociados."
    elif negative_pct >= 20:
        opportunity = "Existe un bloque negativo relevante; conviene revisar los términos dominantes y validar posibles categorías manualmente."
    else:
        opportunity = "La señal negativa es acotada; conviene revisar una muestra de los comentarios clasificados como negativos."

    ratio = metrics["positive_negative_ratio"]
    ratio_text = "sin negativos observados" if math.isinf(float(ratio)) else f"{float(ratio):.2f} positivos por cada negativo"
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
            f"Se analizaron **{total:,} comentarios**. La confianza media del modelo fue **{metrics['mean_confidence']:.1%}**.",
            "",
            "## Distribución",
            f"- Positivos: **{counts['Positivo']:,}** ({positive_pct:.1f}%).",
            f"- Neutros: **{counts['Neutro']:,}** ({float(percentages['Neutro']):.1f}%).",
            f"- Negativos: **{counts['Negativo']:,}** ({negative_pct:.1f}%).",
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
    topics = [
        {
            "topic_rank": rank,
            "frequency": int(row.frequency),
            "percentage": round(float(row.percentage), 2),
            "cumulative_percentage": round(float(row.cumulative_percentage), 2),
        }
        for rank, (_, row) in enumerate(pareto.head(10).iterrows(), start=1)
    ]
    context: dict[str, object] = {
        "evidence_contract_version": "1.0",
        "total_comments": int(metrics["total"]),
        "sentiment_counts": {key: int(value) for key, value in metrics["counts"].items()},
        "sentiment_percentages": {
            key: round(float(value), 2) for key, value in metrics["percentages"].items()
        },
        "mean_local_model_confidence": round(float(metrics["mean_confidence"]), 4),
        "technical_high_confidence_negative_signal": {
            "count": int(metrics["critical_negative_count"]),
            "local_confidence_threshold": round(
                float(metrics["critical_confidence_threshold"]), 4
            ),
            "meaning": "Negative predictions at or above the batch upper-quartile local-confidence threshold; not validated business severity.",
        },
        "negative_ngram_mention_pareto": topics,
        "pareto_denominator": "Total document-frequency n-gram mentions extracted from comments classified as negative.",
        "topic_labels_withheld": True,
        "available_business_objectives": None,
        "available_time_comparison": None,
        "methodology": "TF-IDF + logistic regression. Pareto rows are lexical n-gram mention frequencies, not semantic categories or verified causes.",
    }
    return context


def build_ai_prompt(context: dict[str, object]) -> str:
    return REPORT_PROMPT.format(context=json.dumps(context, ensure_ascii=False, indent=2))


def validate_ai_report(report: str, context: dict[str, object]) -> list[str]:
    """Return evidence-contract violations detectable without semantic inference."""
    if not isinstance(report, str) or len(report.strip()) < 80:
        return ["response_too_short"]

    normalized = report.casefold()
    violations = [
        f"missing_section:{section}"
        for section in REPORT_SECTIONS
        if f"## {section}".casefold() not in normalized
    ]

    forbidden_patterns = {
        "invented_numeric_target": r"(?:reducir|aumentar|mejorar|alcanzar|objetivo|meta).{0,60}\d+(?:[.,]\d+)?\s*%",
        "confidence_as_accuracy": r"(?:confianza.{0,40}(?:equivale|mide|mejora|mejorar[aá]|aumenta|eleva|garantiza).{0,30}(?:accuracy|precisi[oó]n|exactitud)|(?:accuracy|precisi[oó]n|exactitud).{0,40}(?:depende|equivale).{0,30}confianza)",
        "lexical_share_as_comments": r"(?:pareto|n-?gramas?|menciones?|t[eé]rminos?).{0,90}\d+(?:[.,]\d+)?\s*%.{0,40}(?:comentarios?|casos?)",
        "verified_root_cause": r"(?:causas?\s+ra[ií]z\s+(?:verificadas?|confirmadas?|son)|causas?\s+(?:verificadas?|confirmadas?))",
        "validated_business_severity": r"(?:casos?|comentarios?|problemas?)\s+cr[ií]ticos",
    }
    for code, pattern in forbidden_patterns.items():
        if re.search(pattern, normalized, flags=re.DOTALL):
            violations.append(code)

    allowed_percentages = _allowed_percentages(context)
    percentage_spans: list[tuple[int, int]] = []
    for match in re.finditer(r"(?<![\w#])\d+(?:[.,]\d+)?\s*%", report):
        percentage_spans.append(match.span())
        value = float(match.group().rstrip("% ").replace(",", "."))
        if not any(math.isclose(value, allowed, abs_tol=0.011) for allowed in allowed_percentages):
            violations.append(f"unsupported_percentage:{match.group().strip()}")

    allowed_numbers = _allowed_numbers(context) | allowed_percentages
    for match in re.finditer(r"(?<![\w#])\d+(?:[.,]\d+)?", report):
        if any(start <= match.start() < end for start, end in percentage_spans):
            continue
        value = float(match.group().replace(",", "."))
        if not any(math.isclose(value, allowed, abs_tol=0.0001) for allowed in allowed_numbers):
            violations.append(f"unsupported_number:{match.group()}")

    return list(dict.fromkeys(violations))


def _allowed_percentages(context: dict[str, object]) -> set[float]:
    allowed = {80.0}
    allowed.update(float(value) for value in context.get("sentiment_percentages", {}).values())
    confidence = context.get("mean_local_model_confidence")
    if isinstance(confidence, (int, float)):
        allowed.add(round(float(confidence) * 100, 2))
    signal = context.get("technical_high_confidence_negative_signal", {})
    threshold = signal.get("local_confidence_threshold") if isinstance(signal, dict) else None
    if isinstance(threshold, (int, float)):
        allowed.add(round(float(threshold) * 100, 2))
    for row in context.get("negative_ngram_mention_pareto", []):
        if isinstance(row, dict):
            for key in ("percentage", "cumulative_percentage"):
                value = row.get(key)
                if isinstance(value, (int, float)):
                    allowed.add(float(value))
    return allowed


def _allowed_numbers(value: object) -> set[float]:
    if isinstance(value, bool):
        return set()
    if isinstance(value, (int, float)):
        return {float(value)}
    if isinstance(value, dict):
        return set().union(*(_allowed_numbers(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_allowed_numbers(item) for item in value), set())
    return set()


def estimate_payload(context: dict[str, object]) -> dict[str, int]:
    serialized = json.dumps(context, ensure_ascii=False)
    return {"characters": len(serialized), "approximate_tokens": max(1, len(serialized) // 4)}


"""Deterministic and AI-ready executive reporting."""

from __future__ import annotations

import json
import math

import pandas as pd


REPORT_PROMPT = """Actuá como analista senior de Customer Experience y redactá un informe ejecutivo en español.

Usá exclusivamente los datos agregados incluidos en CONTEXTO. No inventes métricas, causas, segmentos ni hechos. Si una causa no está demostrada, presentala sólo como hipótesis y marcala explícitamente. Diferenciá observaciones de hipótesis. No solicites ni supongas datos personales.

Entregá Markdown breve, profesional y accionable con exactamente estas secciones:
## Resumen ejecutivo
## Principales problemas
## Interpretación del Pareto
## Fortalezas
## Oportunidades de mejora
## Recomendaciones accionables
## Prioridades
## Limitaciones del análisis

Cada cifra debe coincidir con CONTEXTO. Evitá lenguaje promocional y basate exclusivamente en los datos proporcionados.

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

    problem_lines = (
        [f"{index + 1}. **{row.topic}** — {int(row.frequency)} menciones." for index, row in principal.iterrows()]
        if not principal.empty
        else ["No hay suficientes comentarios negativos para extraer temas frecuentes."]
    )
    negative_pct = float(percentages["Negativo"])
    positive_pct = float(percentages["Positivo"])
    if negative_pct >= 40:
        opportunity = "El volumen negativo merece revisión prioritaria de los temas más frecuentes."
    elif negative_pct >= 20:
        opportunity = "Existe un bloque negativo relevante; conviene monitorear su evolución y temas dominantes."
    else:
        opportunity = "La señal negativa es acotada; conviene sostener fortalezas y revisar casos críticos puntuales."

    ratio = metrics["positive_negative_ratio"]
    ratio_text = "sin negativos observados" if math.isinf(float(ratio)) else f"{float(ratio):.2f} positivos por cada negativo"
    pareto_text = (
        f"{len(within)} temas concentran aproximadamente el primer 80% de las menciones negativas analizadas."
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
            "## Principales problemas",
            *problem_lines,
            "",
            "## Pareto",
            pareto_text,
            "",
            "## Oportunidades",
            opportunity,
            "",
            "## Limitaciones",
            "Las etiquetas y probabilidades provienen de un modelo TF-IDF + regresión logística y pueden contener errores. "
            "Los temas son n-gramas frecuentes, no causas verificadas. Este informe no reemplaza una revisión cualitativa.",
        ]
    )


def prepare_ai_context(
    metrics: dict[str, object],
    pareto: pd.DataFrame,
) -> dict[str, object]:
    topics = [
        {
            "topic": str(row.topic),
            "frequency": int(row.frequency),
            "percentage": round(float(row.percentage), 2),
            "cumulative_percentage": round(float(row.cumulative_percentage), 2),
        }
        for _, row in pareto.head(10).iterrows()
    ]
    context: dict[str, object] = {
        "total_comments": int(metrics["total"]),
        "sentiment_counts": {key: int(value) for key, value in metrics["counts"].items()},
        "sentiment_percentages": {
            key: round(float(value), 2) for key, value in metrics["percentages"].items()
        },
        "mean_model_confidence": round(float(metrics["mean_confidence"]), 4),
        "critical_negative_count": int(metrics["critical_negative_count"]),
        "negative_topic_pareto": topics,
        "methodology": "TF-IDF + logistic regression; negative topics are document-frequency n-grams.",
    }
    return context


def build_ai_prompt(context: dict[str, object]) -> str:
    return REPORT_PROMPT.format(context=json.dumps(context, ensure_ascii=False, indent=2))


def estimate_payload(context: dict[str, object]) -> dict[str, int]:
    serialized = json.dumps(context, ensure_ascii=False)
    return {"characters": len(serialized), "approximate_tokens": max(1, len(serialized) // 4)}


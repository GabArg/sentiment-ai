"""Offline evaluation of the frozen local model on the user-supplied 104 cases.

This runner is evaluation-only: ``comentario`` is the sole model input. Reference
labels are joined only after predictions have been produced.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)


PROJECT_DIR = Path(__file__).resolve().parents[3]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from src.model import SentimentPredictor  # noqa: E402


DEFAULT_SOURCE = PROJECT_DIR / "artifacts/experiments/sentiment_ai_demo_pareto_104.csv"
OUTPUT_DIR = Path(__file__).resolve().parent
EXPECTED_COLUMNS = (
    "case_id",
    "comentario",
    "expected_sentiment",
    "tema_esperado",
    "dataset_type",
)
EXPECTED_DISTRIBUTION = {"Negativo": 74, "Positivo": 15, "Neutro": 15}
NEGATION_PATTERN = re.compile(r"\b(?:no|nunca|nadie|sin|tampoco|ni|jam[aá]s)\b", re.IGNORECASE)
HIGH_CONFIDENCE_THRESHOLD = 0.80


def load_and_validate(path: Path) -> pd.DataFrame:
    """Load the exact supplied dataset and enforce its evaluation contract."""
    frame = pd.read_csv(path, encoding="utf-8-sig")
    if tuple(frame.columns) != EXPECTED_COLUMNS:
        raise ValueError(f"Expected columns in this order: {', '.join(EXPECTED_COLUMNS)}")
    if len(frame) != 104:
        raise ValueError(f"Expected 104 rows, found {len(frame)}.")
    if frame["case_id"].isna().any() or not frame["case_id"].is_unique:
        raise ValueError("case_id must be complete and unique.")
    if frame["comentario"].isna().any() or frame["comentario"].astype(str).str.strip().str.len().lt(2).any():
        raise ValueError("Every comentario must contain at least two characters.")
    distribution = frame["expected_sentiment"].value_counts().to_dict()
    if distribution != EXPECTED_DISTRIBUTION:
        raise ValueError(f"Unexpected reference distribution: {distribution}")
    if set(frame["dataset_type"].dropna()) != {"synthetic"}:
        raise ValueError("Every row must be explicitly identified as synthetic.")
    return frame


def predict_without_references(
    predictor: SentimentPredictor, inputs: pd.DataFrame
) -> pd.DataFrame:
    """Predict from comentario only; case_id is carried solely for traceability."""
    raw_predictions = predictor.predict_batch(inputs["comentario"].tolist())
    predictions = pd.DataFrame(
        {
            "case_id": inputs["case_id"].to_numpy(),
            "comentario": inputs["comentario"].to_numpy(),
            "predicted_sentiment": raw_predictions["sentiment"].to_numpy(),
            "local_confidence": raw_predictions["confidence"].to_numpy(),
        }
    )
    for class_name in predictor.classes:
        column = f"probability_{class_name.casefold()}"
        predictions[column] = raw_predictions[column].to_numpy()
    return predictions


def evaluate_predictions(
    predictions: pd.DataFrame, references: pd.DataFrame, classes: tuple[str, ...]
) -> tuple[dict[str, Any], pd.DataFrame]:
    """Join references after inference and calculate deterministic diagnostics."""
    details = predictions.merge(references, on="case_id", how="inner", validate="one_to_one")
    expected = details["expected_sentiment"]
    predicted = details["predicted_sentiment"]
    details["is_correct"] = expected.eq(predicted)
    details["is_negation"] = details["comentario"].str.contains(NEGATION_PATTERN, na=False)
    details["is_factual_neutral"] = expected.eq("Neutro")
    details["high_confidence_error"] = (
        ~details["is_correct"]
        & details["local_confidence"].ge(HIGH_CONFIDENCE_THRESHOLD)
    )

    precision, recall, f1, support = precision_recall_fscore_support(
        expected, predicted, labels=classes, zero_division=0
    )
    per_class = {
        label: {
            "precision": float(precision[index]),
            "recall": float(recall[index]),
            "f1": float(f1[index]),
            "support": int(support[index]),
        }
        for index, label in enumerate(classes)
    }
    errors = details.loc[~details["is_correct"]].copy()
    correct = details.loc[details["is_correct"], "local_confidence"]
    incorrect = errors["local_confidence"]
    neutral = details.loc[details["is_factual_neutral"]]
    negations = details.loc[details["is_negation"]]
    error_flows = (
        errors.groupby(["expected_sentiment", "predicted_sentiment"])
        .size()
        .sort_values(ascending=False)
    )
    report: dict[str, Any] = {
        "case_count": int(len(details)),
        "classes": list(classes),
        "accuracy": float(accuracy_score(expected, predicted)),
        "macro_f1": float(np.mean(f1)),
        "weighted_f1": float(np.average(f1, weights=support)),
        "per_class": per_class,
        "confusion_matrix": {
            "labels": list(classes),
            "values": confusion_matrix(expected, predicted, labels=classes).tolist(),
        },
        "distribution": {
            "expected": {label: int((expected == label).sum()) for label in classes},
            "predicted": {label: int((predicted == label).sum()) for label in classes},
        },
        "errors": {
            "count": int(len(errors)),
            "by_flow": [
                {"expected": key[0], "predicted": key[1], "count": int(value)}
                for key, value in error_flows.items()
            ],
            "high_confidence_threshold": HIGH_CONFIDENCE_THRESHOLD,
            "high_confidence_count": int(errors["high_confidence_error"].sum()),
        },
        "confidence": {
            "correct_mean": float(correct.mean()),
            "correct_median": float(correct.median()),
            "error_mean": float(incorrect.mean()),
            "error_median": float(incorrect.median()),
        },
        "factual_neutral": {
            "definition": "All rows whose reference label is Neutro in this synthetic dataset.",
            "count": int(len(neutral)),
            "correct": int(neutral["is_correct"].sum()),
            "accuracy": float(neutral["is_correct"].mean()),
            "predicted_distribution": {
                label: int((neutral["predicted_sentiment"] == label).sum()) for label in classes
            },
        },
        "negation": {
            "definition": f"Regex lexical audit: {NEGATION_PATTERN.pattern}",
            "count": int(len(negations)),
            "correct": int(negations["is_correct"].sum()),
            "accuracy": float(negations["is_correct"].mean()) if len(negations) else None,
            "errors": int((~negations["is_correct"]).sum()),
        },
    }
    return report, errors


def markdown_report(metrics: dict[str, Any], errors: pd.DataFrame, metadata: dict[str, str]) -> str:
    labels = metrics["classes"]
    matrix = metrics["confusion_matrix"]["values"]
    lines = [
        "# Evaluación offline — Sentiment Demo 104",
        "",
        "> Dataset sintético de evaluación. No se utilizó para entrenamiento, selección de modelo ni ajuste de thresholds.",
        "",
        "## Reproducibilidad",
        "",
        f"- Fuente: `{metadata['source']}`",
        f"- SHA-256: `{metadata['source_sha256']}`",
        "- Feature enviada al modelo: `comentario` exclusivamente.",
        "- `expected_sentiment` se incorporó únicamente después de generar predicciones.",
        "- `tema_esperado` no fue utilizado por el modelo ni por esta evaluación de sentimiento.",
        "- Modelo: artefactos locales congelados TF-IDF + regresión logística.",
        "",
        "## Métricas globales",
        "",
        f"- Accuracy: **{metrics['accuracy']:.4f}**",
        f"- Macro-F1: **{metrics['macro_f1']:.4f}**",
        f"- Weighted-F1: **{metrics['weighted_f1']:.4f}**",
        f"- Errores: **{metrics['errors']['count']} / {metrics['case_count']}**",
        "",
        "| Clase | Precision | Recall | F1 | Support |",
        "|---|---:|---:|---:|---:|",
    ]
    for label in labels:
        row = metrics["per_class"][label]
        lines.append(
            f"| {label} | {row['precision']:.4f} | {row['recall']:.4f} | {row['f1']:.4f} | {row['support']} |"
        )
    lines += [
        "",
        "## Matriz de confusión",
        "",
        "Filas = referencia; columnas = predicción.",
        "",
        f"| Referencia \\ Predicción | {' | '.join(labels)} |",
        f"|---|{'|'.join(['---:'] * len(labels))}|",
    ]
    for label, values in zip(labels, matrix, strict=True):
        lines.append(f"| {label} | {' | '.join(str(value) for value in values)} |")
    lines += [
        "",
        "## Distribución",
        "",
        "| Clase | Esperada | Predicha |",
        "|---|---:|---:|",
    ]
    for label in labels:
        lines.append(
            f"| {label} | {metrics['distribution']['expected'][label]} | {metrics['distribution']['predicted'][label]} |"
        )
    lines += [
        "",
        "## Confianza local",
        "",
        f"- Media en aciertos: {metrics['confidence']['correct_mean']:.4f}",
        f"- Media en errores: {metrics['confidence']['error_mean']:.4f}",
        f"- Errores con confidence ≥ {metrics['errors']['high_confidence_threshold']:.2f}: {metrics['errors']['high_confidence_count']}",
        "",
        "## Flujos de error",
        "",
        "| Esperada | Predicha | Casos |",
        "|---|---|---:|",
    ]
    for flow in metrics["errors"]["by_flow"]:
        lines.append(f"| {flow['expected']} | {flow['predicted']} | {flow['count']} |")
    factual = metrics["factual_neutral"]
    negation = metrics["negation"]
    lines += [
        "",
        "## Neutrales factuales",
        "",
        f"- Casos: {factual['count']}",
        f"- Aciertos: {factual['correct']}",
        f"- Accuracy: {factual['accuracy']:.4f}",
        f"- Distribución predicha: {factual['predicted_distribution']}",
        "",
        "## Negaciones",
        "",
        f"- Detección para auditoría: `{negation['definition']}`",
        f"- Casos detectados: {negation['count']}",
        f"- Aciertos: {negation['correct']}",
        f"- Errores: {negation['errors']}",
        f"- Accuracy: {negation['accuracy']:.4f}" if negation["accuracy"] is not None else "- Accuracy: no aplica",
        "",
        "## Ejemplos representativos de errores",
        "",
        "Selección determinística: error de mayor confianza por cada flujo referencia→predicción.",
        "",
        "| case_id | Comentario | Esperada | Predicha | Confidence |",
        "|---|---|---|---|---:|",
    ]
    representatives = (
        errors.sort_values(["local_confidence", "case_id"], ascending=[False, True])
        .groupby(["expected_sentiment", "predicted_sentiment"], sort=False)
        .head(1)
    )
    for row in representatives.itertuples(index=False):
        text = str(row.comentario).replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {row.case_id} | {text} | {row.expected_sentiment} | {row.predicted_sentiment} | {row.local_confidence:.4f} |"
        )
    lines += [
        "",
        "## Limitaciones",
        "",
        "- Las etiquetas son sintéticas y este conjunto no representa por sí solo producción.",
        "- La auditoría de negaciones es léxica; no garantiza que toda construcción negativa haya sido detectada.",
        "- Confidence es la probabilidad de la clase elegida por el modelo local, no una probabilidad calibrada de acierto.",
        "- Este resultado no autoriza modificar thresholds ni seleccionar un modelo sobre los mismos 104 casos.",
        "",
    ]
    return "\n".join(lines)


def run(source: Path = DEFAULT_SOURCE, output_dir: Path = OUTPUT_DIR) -> dict[str, Any]:
    frame = load_and_validate(source)

    # Deliberate separation: neither reference column can reach predict_batch().
    inputs = frame.loc[:, ["case_id", "comentario"]].copy()
    references = frame.loc[:, ["case_id", "expected_sentiment"]].copy()
    predictor = SentimentPredictor.load()
    predictions = predict_without_references(predictor, inputs)
    metrics, errors = evaluate_predictions(predictions, references, predictor.classes)

    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    metadata = {
        "source": str(source.relative_to(PROJECT_DIR)),
        "source_sha256": source_hash,
    }
    metrics["evaluation"] = {
        **metadata,
        "model_input_columns": ["comentario"],
        "reference_columns": ["expected_sentiment"],
        "excluded_columns": ["tema_esperado", "dataset_type"],
        "high_confidence_threshold_reporting_only": HIGH_CONFIDENCE_THRESHOLD,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(output_dir / "predictions.csv", index=False, encoding="utf-8-sig")
    error_columns = [
        "case_id",
        "comentario",
        "expected_sentiment",
        "predicted_sentiment",
        "local_confidence",
        "probability_negativo",
        "probability_neutro",
        "probability_positivo",
        "is_factual_neutral",
        "is_negation",
        "high_confidence_error",
    ]
    errors.loc[:, error_columns].to_csv(
        output_dir / "errors.csv", index=False, encoding="utf-8-sig"
    )
    (output_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "report.md").write_text(
        markdown_report(metrics, errors, metadata), encoding="utf-8"
    )
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    metrics = run(args.source.resolve(), args.output_dir.resolve())
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

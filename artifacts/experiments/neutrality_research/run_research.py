"""Reproducible, non-production audit of neutrality and frozen model behavior."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import train_test_split


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.model import SentimentPredictor  # noqa: E402


DEFAULT_HISTORICAL_ROOT = ROOT.parent / "_original_reference"
DEFAULT_CORPUS = DEFAULT_HISTORICAL_ROOT / "data/processed/dataset_unificado.csv"
DEFAULT_RAW_SYNTHETIC = DEFAULT_HISTORICAL_ROOT / "data/raw/DB_amazon_multilingual_v6.csv"
DIAGNOSTICS = {
    "manual_60": ROOT / "tests/fixtures/sentiment_benchmark.csv",
    "synthetic_demo_104": ROOT / "artifacts/experiments/sentiment_ai_demo_pareto_104.csv",
}
CLASSES = ("Negativo", "Neutro", "Positivo")
COMMERCIAL_TERMS = (
    "compra", "devolucion", "devolución", "entrega", "factura", "garantia",
    "garantía", "pedido", "problema", "producto", "reintegro", "soporte",
)
NEGATION = re.compile(r"\b(?:no|nunca|nadie|sin|tampoco|ni|jam[aá]s)\b", re.I)


def historical_clean(text: object) -> str:
    if not isinstance(text, str):
        return ""
    value = re.sub(r"[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s\.,!?]", "", text)
    return re.sub(r"\s+", " ", value).lower().strip()


def minimal_normalize(text: object) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(text))).strip()


TRANSFORMS = {
    "current_str_strip": lambda text: str(text).strip(),
    "historical_clean": historical_clean,
    "nfkc_whitespace": minimal_normalize,
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sentence_parts(text: str) -> set[str]:
    return {
        historical_clean(part)
        for part in re.split(r"[.!?]+", str(text))
        if len(historical_clean(part).split()) >= 4
    }


def corpus_audit(model, vectorizer, corpus_path: Path, raw_synthetic_path: Path) -> dict:
    corpus = pd.read_csv(corpus_path)
    raw = pd.read_csv(raw_synthetic_path, sep=";")
    normalized = corpus["texto"].map(historical_clean)
    conflicts = (
        corpus.assign(normalized=normalized)
        .groupby("normalized")["sentimiento"]
        .nunique()
    )
    train_idx, test_idx = train_test_split(
        np.arange(len(corpus)), test_size=0.2, random_state=42,
        stratify=corpus["sentimiento"],
    )
    train_parts: set[str] = set()
    for text in corpus.iloc[train_idx]["texto"]:
        train_parts.update(sentence_parts(text))
    test_shared = [bool(sentence_parts(text) & train_parts) for text in corpus.iloc[test_idx]["texto"]]

    features = np.asarray(vectorizer.get_feature_names_out())
    coefficient_rows = {}
    for class_index, label in enumerate(model.classes_):
        weights = model.coef_[class_index]
        top = np.argsort(weights)[-25:][::-1]
        bottom = np.argsort(weights)[:25]
        coefficient_rows[str(label)] = {
            "highest": [{"feature": str(features[i]), "weight": float(weights[i])} for i in top],
            "lowest": [{"feature": str(features[i]), "weight": float(weights[i])} for i in bottom],
        }
    vocabulary = vectorizer.vocabulary_
    commercial = {}
    for term in COMMERCIAL_TERMS:
        key = term.lower()
        index = vocabulary.get(key)
        commercial[term] = None if index is None else {
            str(label): float(model.coef_[class_index, index])
            for class_index, label in enumerate(model.classes_)
        }
    return {
        "sources": {
            "corpus": corpus_path.name,
            "corpus_sha256": sha(corpus_path),
            "raw_synthetic": raw_synthetic_path.name,
            "raw_synthetic_sha256": sha(raw_synthetic_path),
        },
        "rows": int(len(corpus)),
        "class_distribution": corpus["sentimiento"].value_counts().to_dict(),
        "source_distribution": corpus["origen_dato"].value_counts().to_dict(),
        "neutral_by_source": corpus.loc[corpus.sentimiento.eq("Neutro"), "origen_dato"].value_counts().to_dict(),
        "exact_duplicate_texts_processed": int(corpus["texto"].duplicated().sum()),
        "duplicates_after_historical_clean": int(normalized.duplicated().sum()),
        "conflicting_normalized_text_groups": int((conflicts > 1).sum()),
        "raw_synthetic_rows": int(len(raw)),
        "raw_synthetic_exact_duplicates": int(raw["comentario"].duplicated().sum()),
        "random_split_test_rows_sharing_sentence_with_train": int(sum(test_shared)),
        "random_split_test_share_percentage": float(np.mean(test_shared) * 100),
        "split_note": "Diagnostic reconstruction using random_state=42; shared generated segments are leakage risk, not proof of label leakage.",
        "model": {"classes": list(map(str, model.classes_)), "params": {k: str(v) for k, v in model.get_params().items()}, "features": int(len(features))},
        "vectorizer": {k: str(v) for k, v in vectorizer.get_params().items()},
        "top_coefficients": coefficient_rows,
        "commercial_term_coefficients": commercial,
        "coefficient_caution": "Coefficients are conditional associations in this fitted linear model; they do not establish causality.",
    }


def load_diagnostic(name: str, path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, encoding="utf-8-sig")
    if name == "manual_60":
        return frame.rename(columns={"text": "text"})[["text", "expected_sentiment"]].assign(subgroup=frame["category"])
    return frame.rename(columns={"comentario": "text"})[["text", "expected_sentiment"]].assign(
        subgroup=np.where(frame["expected_sentiment"].eq("Neutro"), "factual_neutral", "synthetic_opinion")
    )


def metrics(expected, predicted) -> dict:
    precision, recall, f1, support = precision_recall_fscore_support(expected, predicted, labels=CLASSES, zero_division=0)
    return {
        "accuracy": float(accuracy_score(expected, predicted)),
        "macro_f1": float(np.mean(f1)),
        "weighted_f1": float(np.average(f1, weights=support)),
        "per_class": {label: {"precision": float(precision[i]), "recall": float(recall[i]), "f1": float(f1[i]), "support": int(support[i])} for i, label in enumerate(CLASSES)},
        "confusion_matrix": {"labels": list(CLASSES), "values": confusion_matrix(expected, predicted, labels=CLASSES).tolist()},
    }


def evaluate_variants(predictor, vectorizer) -> tuple[dict, pd.DataFrame]:
    all_results = []
    summary = {}
    for dataset, path in DIAGNOSTICS.items():
        frame = load_diagnostic(dataset, path)
        summary[dataset] = {"source": str(path.relative_to(ROOT)), "sha256": sha(path), "selection_policy": "diagnostic_only"}
        baseline_predictions = None
        for variant, transform in TRANSFORMS.items():
            transformed = frame["text"].map(transform)
            prediction = predictor.predict_batch(transformed.tolist())
            if baseline_predictions is None:
                baseline_predictions = prediction["sentiment"].copy()
            matrix = vectorizer.transform(transformed)
            result = metrics(frame["expected_sentiment"], prediction["sentiment"])
            result["changed_vs_current"] = int((prediction["sentiment"] != baseline_predictions).sum())
            result["zero_feature_rows"] = int((matrix.getnnz(axis=1) == 0).sum())
            result["mean_nonzero_features"] = float(matrix.getnnz(axis=1).mean())
            result["subgroups"] = {}
            for subgroup, group in frame.assign(predicted=prediction["sentiment"].to_numpy()).groupby("subgroup"):
                result["subgroups"][str(subgroup)] = metrics(group.expected_sentiment, group.predicted)
            summary[dataset][variant] = result
            for i, row in frame.iterrows():
                all_results.append({
                    "dataset": dataset, "row_index": int(i), "variant": variant,
                    "text": row.text, "expected_sentiment": row.expected_sentiment,
                    "predicted_sentiment": prediction.loc[i, "sentiment"],
                    "confidence": float(prediction.loc[i, "confidence"]),
                    "subgroup": row.subgroup,
                    "is_negation": bool(NEGATION.search(str(row.text))),
                })
        baseline = pd.DataFrame([row for row in all_results if row["dataset"] == dataset and row["variant"] == "current_str_strip"])
        summary[dataset]["abstention_sensitivity"] = []
        for threshold in (0.50, 0.60, 0.70, 0.80):
            covered = baseline.confidence.ge(threshold)
            covered_frame = baseline.loc[covered]
            summary[dataset]["abstention_sensitivity"].append({
                "threshold": threshold,
                "coverage": float(covered.mean()),
                "covered_cases": int(covered.sum()),
                "selective_accuracy": float((covered_frame.expected_sentiment == covered_frame.predicted_sentiment).mean()) if len(covered_frame) else None,
                "selective_macro_f1": metrics(covered_frame.expected_sentiment, covered_frame.predicted_sentiment)["macro_f1"] if len(covered_frame) else None,
                "abstention_rate_by_reference_class": {label: float((~covered[baseline.expected_sentiment.eq(label)]).mean()) for label in CLASSES},
                "high_confidence_errors_remaining": int(((baseline.expected_sentiment != baseline.predicted_sentiment) & covered).sum()),
                "caution": "Sensitivity analysis only; thresholds were not selected on this dataset and selective accuracy is not global accuracy.",
            })
    return summary, pd.DataFrame(all_results)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--raw-synthetic", type=Path, default=DEFAULT_RAW_SYNTHETIC)
    args = parser.parse_args()
    model = joblib.load(ROOT / "models/sentiment_model.joblib")
    vectorizer = joblib.load(ROOT / "models/tfidf_vectorizer.joblib")
    predictor = SentimentPredictor(model, vectorizer)
    audit = corpus_audit(model, vectorizer, args.corpus.resolve(), args.raw_synthetic.resolve())
    comparisons, rows = evaluate_variants(predictor, vectorizer)
    output = Path(__file__).resolve().parent
    (output / "corpus_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "experiment_metrics.json").write_text(json.dumps(comparisons, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows.to_csv(output / "experiment_predictions.csv", index=False, encoding="utf-8-sig")
    print(json.dumps({"corpus": {k: audit[k] for k in ("rows", "class_distribution", "source_distribution", "raw_synthetic_exact_duplicates", "random_split_test_share_percentage")}, "datasets": comparisons}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

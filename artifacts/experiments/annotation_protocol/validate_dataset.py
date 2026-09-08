"""Validate blind annotation packets or the human-annotation master CSV."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
from pathlib import Path
import re
import sys


HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE / "dataset_schema.json"
BLIND_COLUMNS = (
    "case_id", "texto_original_anonimizado", "source_id", "family_id",
    "source_type", "language", "sentiment_subgroup", "annotator_label",
    "uncertainty_reason", "annotator_notes", "taxonomy_version",
)
PII_PATTERNS = {
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    "url": re.compile(r"https?://\S+|www\.\S+", re.I),
    "phone": re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)"),
    "long_numeric_id": re.compile(r"\b\d{6,}\b"),
}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("CSV has no header.")
        return reader.fieldnames, list(reader)


def is_utc_timestamp(value: str) -> bool:
    if not value.endswith("Z"):
        return False
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return True


def validate_blind(path: Path, schema: dict) -> list[str]:
    header, rows = read_csv(path)
    errors: list[str] = []
    if tuple(header) != BLIND_COLUMNS:
        errors.append(f"header: expected blind columns {list(BLIND_COLUMNS)}")
        return errors
    prohibited = set(schema["prohibited_columns"])
    if prohibited.intersection(header):
        errors.append("header: model prediction/reference columns are forbidden")
    seen: set[str] = set()
    labels = set(schema["label_values"])
    subgroups = set(schema["sentiment_subgroup_values"])
    source_types = set(schema["source_type_values"])
    patterns = {name: re.compile(pattern) for name, pattern in schema["id_patterns"].items()}
    language_pattern = re.compile(schema["language_pattern"])
    for number, row in enumerate(rows, start=2):
        case_id = row["case_id"].strip()
        if not case_id or case_id in seen:
            errors.append(f"row {number}: case_id is blank or duplicated")
        seen.add(case_id)
        for field in ("case_id", "source_id", "family_id"):
            if not patterns[field].fullmatch(row[field].strip()):
                errors.append(f"row {number}: invalid {field}")
        text = row["texto_original_anonimizado"].strip()
        if len(text) < 2:
            errors.append(f"row {number}: anonymized text is blank or too short")
        for kind, pattern in PII_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"row {number}: possible unredacted {kind} in text")
        if row["source_type"] not in source_types:
            errors.append(f"row {number}: invalid source_type")
        if not language_pattern.fullmatch(row["language"]):
            errors.append(f"row {number}: invalid language")
        label = row["annotator_label"].strip()
        if label and label not in labels:
            errors.append(f"row {number}: invalid annotator_label {label!r}")
        if row["sentiment_subgroup"].strip() not in subgroups:
            errors.append(f"row {number}: invalid sentiment_subgroup")
        if row["taxonomy_version"].strip() != schema["taxonomy_version"]:
            errors.append(f"row {number}: taxonomy_version mismatch")
        if label in {"Ambiguo", "No evaluable"} and not row["uncertainty_reason"].strip():
            errors.append(f"row {number}: uncertainty_reason is required for {label}")
    return errors


def validate_master(path: Path, schema: dict) -> list[str]:
    header, rows = read_csv(path)
    expected_header = schema["csv_columns"]
    errors: list[str] = []
    if header != expected_header:
        extras = sorted(set(header) - set(expected_header))
        errors.append(f"header: expected exact schema order; extra={extras}")
        return errors
    if set(header).intersection(schema["prohibited_columns"]):
        errors.append("header: prediction/reference aliases are forbidden")

    ids: set[str] = set()
    family_splits: dict[str, set[str]] = {}
    labels = set(schema["label_values"])
    final_labels = set(schema["final_label_values"])
    source_types = set(schema["source_type_values"])
    statuses = set(schema["annotation_status_values"])
    splits = set(schema["split_values"])
    subgroups = set(schema["sentiment_subgroup_values"])
    patterns = {name: re.compile(pattern) for name, pattern in schema["id_patterns"].items()}
    language_pattern = re.compile(schema["language_pattern"])

    for number, row in enumerate(rows, start=2):
        prefix = f"row {number}"
        for field in ("case_id", "source_id", "family_id"):
            value = row[field].strip()
            if not patterns[field].fullmatch(value):
                errors.append(f"{prefix}: invalid {field}")
        case_id = row["case_id"].strip()
        if case_id in ids:
            errors.append(f"{prefix}: duplicated case_id {case_id!r}")
        ids.add(case_id)
        text = row["texto_original_anonimizado"].strip()
        if len(text) < 2:
            errors.append(f"{prefix}: anonymized text is blank or too short")
        for kind, pattern in PII_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{prefix}: possible unredacted {kind} in text")
        if row["source_type"] not in source_types:
            errors.append(f"{prefix}: invalid source_type")
        if not language_pattern.fullmatch(row["language"]):
            errors.append(f"{prefix}: invalid language")
        if row["sentiment_subgroup"] not in subgroups:
            errors.append(f"{prefix}: invalid sentiment_subgroup")
        if not is_utc_timestamp(row["created_at"]):
            errors.append(f"{prefix}: created_at must be ISO-8601 UTC ending in Z")
        if row["taxonomy_version"] != schema["taxonomy_version"]:
            errors.append(f"{prefix}: taxonomy_version mismatch")

        status = row["annotation_status"]
        split = row["split"]
        first = row["annotator_1_label"]
        second = row["annotator_2_label"]
        adjudicated = row["adjudicated_label"]
        if status not in statuses:
            errors.append(f"{prefix}: invalid annotation_status")
        if split not in splits:
            errors.append(f"{prefix}: invalid split")
        for field, value in (("annotator_1_label", first), ("annotator_2_label", second)):
            if value and value not in labels:
                errors.append(f"{prefix}: invalid {field}")
        if adjudicated and adjudicated not in final_labels:
            errors.append(f"{prefix}: adjudicated_label must be ternary or No evaluable")

        if status == "pending" and any((first, second, adjudicated)):
            errors.append(f"{prefix}: pending rows cannot contain labels")
        elif status == "annotated" and (
            not first or first != second or first not in final_labels or adjudicated
        ):
            errors.append(f"{prefix}: annotated requires two matching resolved labels and no adjudication")
        elif status == "disagreement":
            if not first or not second or (first == second and "Ambiguo" not in {first, second}):
                errors.append(f"{prefix}: disagreement requires two conflicting/ambiguous labels")
            if adjudicated:
                errors.append(f"{prefix}: disagreement cannot already contain adjudicated_label")
            if not row["disagreement_reason"].strip():
                errors.append(f"{prefix}: disagreement_reason is required")
        elif status == "adjudicated":
            if not first or not second or not adjudicated or not row["adjudication_notes"].strip():
                errors.append(f"{prefix}: adjudicated requires both labels, final label and notes")
        elif status == "excluded" and split != "excluded":
            errors.append(f"{prefix}: excluded status requires excluded split")

        if split == "final" and status not in {"annotated", "adjudicated"}:
            errors.append(f"{prefix}: final split requires a resolved annotation")
        resolved_label = adjudicated if status == "adjudicated" else first if status == "annotated" else ""
        if resolved_label == "No evaluable" and split != "excluded":
            errors.append(f"{prefix}: No evaluable cases must use excluded split")
        if row["source_type"] == "synthetic" and split in {"development", "final"}:
            errors.append(f"{prefix}: synthetic examples are training-only, not independent evaluation")
        if split in {"development", "final"}:
            family_splits.setdefault(row["family_id"], set()).add(split)

    for family, assigned in family_splits.items():
        if len(assigned) > 1:
            errors.append(f"family {family!r}: cannot span development and final")
    return errors


def validate(path: Path, mode: str) -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return validate_blind(path, schema) if mode == "blind" else validate_master(path, schema)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--mode", choices=("master", "blind"), default="master")
    args = parser.parse_args()
    errors = validate(args.csv, args.mode)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
    print(f"OK: {args.csv} satisfies the {args.mode} annotation contract.")


if __name__ == "__main__":
    main()

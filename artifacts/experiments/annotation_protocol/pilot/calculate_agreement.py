"""Calculate transparent agreement statistics from two blind annotation packets."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import sys


PILOT_DIR = Path(__file__).resolve().parent
PROTOCOL_DIR = PILOT_DIR.parent
if str(PROTOCOL_DIR) not in sys.path:
    sys.path.insert(0, str(PROTOCOL_DIR))

from validate_dataset import validate  # noqa: E402


LABELS = ("Negativo", "Neutro", "Positivo", "No evaluable", "Ambiguo")
SHARED_FIELDS = (
    "case_id",
    "texto_original_anonimizado",
    "source_id",
    "family_id",
    "source_type",
    "language",
    "sentiment_subgroup",
    "taxonomy_version",
)


def packet_rows(path: Path) -> dict[str, dict[str, str]]:
    errors = validate(path, "blind")
    if errors:
        raise ValueError("; ".join(errors))
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {row["case_id"]: row for row in rows}


def validate_packet_pair(
    first: dict[str, dict[str, str]], second: dict[str, dict[str, str]]
) -> None:
    first_ids = set(first)
    second_ids = set(second)
    missing_from_b = sorted(first_ids - second_ids)
    additional_in_b = sorted(second_ids - first_ids)
    errors = []
    if missing_from_b:
        errors.append(f"case_id missing from packet B: {missing_from_b}")
    if additional_in_b:
        errors.append(f"case_id additional in packet B: {additional_in_b}")
    for case_id in sorted(first_ids & second_ids):
        mismatched = [
            field for field in SHARED_FIELDS if first[case_id][field] != second[case_id][field]
        ]
        if mismatched:
            errors.append(f"case_id {case_id}: shared fields differ: {mismatched}")
    if errors:
        raise ValueError("; ".join(errors))


def completed_labels(rows: dict[str, dict[str, str]]) -> dict[str, str]:
    return {
        row["case_id"]: row["annotator_label"]
        for row in rows.values()
        if row["annotator_label"]
    }


def agreement(first_path: Path, second_path: Path) -> dict[str, object]:
    first_rows = packet_rows(first_path)
    second_rows = packet_rows(second_path)
    validate_packet_pair(first_rows, second_rows)
    first = completed_labels(first_rows)
    second = completed_labels(second_rows)
    common = sorted(set(first) & set(second))
    if not common:
        return {
            "completed_overlap": 0,
            "raw_agreement": None,
            "cohen_kappa": None,
            "status": "No overlapping completed human annotations.",
            "prevalence": {"annotator_A": {}, "annotator_B": {}},
            "confusion_matrix": {"labels": list(LABELS), "values": [[0] * len(LABELS) for _ in LABELS]},
            "disagreements": [],
        }
    pairs = [(first[case_id], second[case_id]) for case_id in common]
    matrix = [[sum(a == row and b == column for a, b in pairs) for column in LABELS] for row in LABELS]
    observed = sum(a == b for a, b in pairs) / len(pairs)
    counts_a = Counter(a for a, _ in pairs)
    counts_b = Counter(b for _, b in pairs)
    expected = sum(counts_a[label] * counts_b[label] for label in LABELS) / len(pairs) ** 2
    kappa = (observed - expected) / (1 - expected) if expected < 1 else (1.0 if observed == 1 else None)
    return {
        "completed_overlap": len(common),
        "raw_agreement": observed,
        "cohen_kappa": kappa,
        "status": "Calculated from independent labels; interpret with prevalence and matrix.",
        "prevalence": {
            "annotator_A": {label: counts_a[label] for label in LABELS},
            "annotator_B": {label: counts_b[label] for label in LABELS},
        },
        "confusion_matrix": {"labels": list(LABELS), "values": matrix},
        "disagreements": [
            {"case_id": case_id, "annotator_A": first[case_id], "annotator_B": second[case_id]}
            for case_id in common if first[case_id] != second[case_id]
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet_a", type=Path)
    parser.add_argument("packet_b", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = agreement(args.packet_a, args.packet_b)
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()

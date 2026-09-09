from __future__ import annotations

import csv
from pathlib import Path

import pytest

from calculate_agreement import LABELS, agreement


COLUMNS = (
    "case_id", "texto_original_anonimizado", "source_id", "family_id",
    "source_type", "language", "sentiment_subgroup", "annotator_label",
    "uncertainty_reason", "annotator_notes", "taxonomy_version",
)


def packet(
    path: Path,
    labels: list[str],
    *,
    case_ids: list[str] | None = None,
    reverse: bool = False,
    overrides: dict[str, dict[str, str]] | None = None,
) -> None:
    case_ids = case_ids or [f"CASE-{index:03}" for index in range(1, len(labels) + 1)]
    rows = []
    for index, (case_id, label) in enumerate(zip(case_ids, labels, strict=True), start=1):
        row = {
            "case_id": case_id,
            "texto_original_anonimizado": f"Comentario de prueba {index}",
            "source_id": "SOURCE-001", "family_id": f"FAMILY-{index:03}",
            "source_type": "synthetic", "language": "es",
            "sentiment_subgroup": "other", "annotator_label": label,
            "uncertainty_reason": "Lecturas múltiples" if label == "Ambiguo" else "",
            "annotator_notes": "", "taxonomy_version": "sentiment-v1.0.0",
        }
        row.update((overrides or {}).get(case_id, {}))
        rows.append(row)
    if reverse:
        rows.reverse()
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_empty_packets_report_no_human_agreement(tmp_path):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    packet(a, []); packet(b, [])
    result = agreement(a, b)
    assert result["completed_overlap"] == 0
    assert result["cohen_kappa"] is None


def test_perfect_agreement(tmp_path):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    labels = ["Negativo", "Neutro", "Positivo"]
    packet(a, labels); packet(b, labels)
    result = agreement(a, b)
    assert result["raw_agreement"] == 1
    assert result["cohen_kappa"] == 1


def test_different_row_order_is_accepted(tmp_path):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    labels = ["Negativo", "Neutro", "Positivo"]
    packet(a, labels)
    packet(b, labels, reverse=True)
    assert agreement(a, b)["raw_agreement"] == 1


def test_disagreement_matrix_and_kappa(tmp_path):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    packet(a, ["Negativo", "Neutro", "Positivo"])
    packet(b, ["Negativo", "Positivo", "Positivo"])
    result = agreement(a, b)
    assert result["raw_agreement"] == pytest.approx(2 / 3)
    assert result["cohen_kappa"] == pytest.approx(0.5)
    assert result["confusion_matrix"]["values"][LABELS.index("Neutro")][LABELS.index("Positivo")] == 1
    assert result["disagreements"] == [{"case_id": "CASE-002", "annotator_A": "Neutro", "annotator_B": "Positivo"}]


@pytest.mark.parametrize(
    ("ids_a", "ids_b", "message"),
    [
        (["CASE-001", "CASE-002"], ["CASE-001"], "missing from packet B"),
        (["CASE-001"], ["CASE-001", "CASE-002"], "additional in packet B"),
    ],
)
def test_missing_or_additional_ids_block_agreement(tmp_path, ids_a, ids_b, message):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    packet(a, ["Neutro"] * len(ids_a), case_ids=ids_a)
    packet(b, ["Neutro"] * len(ids_b), case_ids=ids_b)
    with pytest.raises(ValueError, match=message):
        agreement(a, b)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("texto_original_anonimizado", "Texto diferente"),
        ("family_id", "FAMILY-999"),
    ],
)
def test_text_or_metadata_difference_blocks_agreement(tmp_path, field, value):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    packet(a, ["Neutro"])
    packet(b, ["Positivo"], overrides={"CASE-001": {field: value}})
    with pytest.raises(ValueError, match="shared fields differ"):
        agreement(a, b)


def test_duplicate_case_id_blocks_agreement(tmp_path):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    packet(a, ["Neutro", "Positivo"], case_ids=["CASE-001", "CASE-001"])
    packet(b, ["Neutro", "Positivo"])
    with pytest.raises(ValueError, match="duplicated"):
        agreement(a, b)


def test_different_labels_are_valid_structural_input(tmp_path):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    packet(a, ["Negativo"])
    packet(b, ["Positivo"])
    result = agreement(a, b)
    assert result["completed_overlap"] == 1
    assert result["raw_agreement"] == 0
    assert result["disagreements"] == [
        {"case_id": "CASE-001", "annotator_A": "Negativo", "annotator_B": "Positivo"}
    ]

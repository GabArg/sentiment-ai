from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from validate_dataset import BLIND_COLUMNS, SCHEMA_PATH, validate


SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def write_csv(path: Path, columns: list[str] | tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def master_row(**overrides: str) -> dict[str, str]:
    row = {column: "" for column in SCHEMA["csv_columns"]}
    row.update(
        case_id="CASE-001",
        texto_original_anonimizado="La operación quedó registrada correctamente.",
        source_id="SOURCE-001",
        family_id="FAMILY-001",
        source_type="authorized_feedback",
        language="es",
        annotation_status="annotated",
        annotator_1_label="Neutro",
        annotator_2_label="Neutro",
        sentiment_subgroup="factual",
        created_at="2026-09-08T12:00:00Z",
        taxonomy_version="sentiment-v1.0.0",
        split="development",
    )
    row.update(overrides)
    return row


def test_valid_resolved_master_contract(tmp_path):
    path = tmp_path / "master.csv"
    write_csv(path, SCHEMA["csv_columns"], [master_row()])
    assert validate(path, "master") == []


def test_model_outputs_are_rejected_from_master(tmp_path):
    path = tmp_path / "leaky.csv"
    columns = [*SCHEMA["csv_columns"], "local_confidence"]
    write_csv(path, columns, [{**master_row(), "local_confidence": "0.9"}])
    assert any("header" in error for error in validate(path, "master"))


def test_family_cannot_cross_development_and_final(tmp_path):
    path = tmp_path / "leak.csv"
    rows = [
        master_row(),
        master_row(case_id="CASE-002", split="final"),
    ]
    write_csv(path, SCHEMA["csv_columns"], rows)
    assert any("cannot span" in error for error in validate(path, "master"))


def test_adjudication_requires_final_label_and_notes(tmp_path):
    path = tmp_path / "adjudication.csv"
    row = master_row(
        annotation_status="adjudicated",
        annotator_1_label="Negativo",
        annotator_2_label="Neutro",
        disagreement_reason="Hecho con consecuencia discutida",
    )
    write_csv(path, SCHEMA["csv_columns"], [row])
    errors = validate(path, "master")
    assert any("final label and notes" in error for error in errors)


def test_synthetic_cannot_be_claimed_as_final_evaluation(tmp_path):
    path = tmp_path / "synthetic.csv"
    write_csv(path, SCHEMA["csv_columns"], [master_row(source_type="synthetic", split="final")])
    assert any("training-only" in error for error in validate(path, "master"))


def test_ambiguous_agreement_still_requires_adjudication(tmp_path):
    path = tmp_path / "ambiguous.csv"
    row = master_row(annotator_1_label="Ambiguo", annotator_2_label="Ambiguo")
    write_csv(path, SCHEMA["csv_columns"], [row])
    assert any("matching resolved labels" in error for error in validate(path, "master"))


def test_not_evaluable_case_must_be_excluded(tmp_path):
    path = tmp_path / "not_evaluable.csv"
    row = master_row(annotator_1_label="No evaluable", annotator_2_label="No evaluable")
    write_csv(path, SCHEMA["csv_columns"], [row])
    assert any("must use excluded split" in error for error in validate(path, "master"))


def test_possible_pii_is_rejected(tmp_path):
    path = tmp_path / "pii.csv"
    write_csv(path, SCHEMA["csv_columns"], [master_row(texto_original_anonimizado="Escribí a cliente@example.com")])
    assert any("unredacted email" in error for error in validate(path, "master"))


def test_blind_packet_has_one_label_and_no_model_fields(tmp_path):
    path = tmp_path / "blind.csv"
    row = {column: "" for column in BLIND_COLUMNS}
    row.update(
        case_id="CASE-001", texto_original_anonimizado="Estado registrado",
        source_id="SOURCE-001", family_id="FAMILY-001",
        source_type="authorized_feedback", language="es",
        sentiment_subgroup="factual", annotator_label="Ambiguo",
        uncertainty_reason="Dos lecturas plausibles",
        taxonomy_version="sentiment-v1.0.0",
    )
    write_csv(path, BLIND_COLUMNS, [row])
    assert validate(path, "blind") == []


@pytest.mark.parametrize("template,mode", [("annotation_template.csv", "blind"), ("adjudication_template.csv", "master")])
def test_empty_templates_have_valid_headers(template, mode):
    assert validate(SCHEMA_PATH.parent / template, mode) == []

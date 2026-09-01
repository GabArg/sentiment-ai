from __future__ import annotations

import pandas as pd
import pytest

from src.preprocessing import (
    CSVValidationError,
    MAX_ROWS,
    MAX_UPLOAD_BYTES,
    anonymize_text,
    prepare_text_column,
    read_csv_upload,
)


def test_empty_csv_is_rejected():
    with pytest.raises(CSVValidationError, match="empty"):
        read_csv_upload(b"")


def test_csv_columns_and_delimiter_are_detected():
    frame = read_csv_upload("id;opinion\n1;Muy bueno\n2;Muy malo\n".encode())
    assert list(frame.columns) == ["id", "opinion"]
    assert len(frame) == 2


SINGLE_COLUMN_COMMENTS = [
    "Excelente atención y entrega rápida.",
    "El producto llegó roto.",
    "El pedido llegó el martes por la tarde.",
    "Muy buena calidad, estoy conforme.",
    "No respondieron mi reclamo.",
    "La compra fue realizada el lunes.",
]


@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig"])
def test_single_column_csv_preserves_header_and_rows(encoding):
    raw = ("comentario\n" + "\n".join(SINGLE_COLUMN_COMMENTS) + "\n").encode(encoding)
    frame = read_csv_upload(raw)

    assert list(frame.columns) == ["comentario"]
    assert frame["comentario"].tolist() == SINGLE_COLUMN_COMMENTS


@pytest.mark.parametrize("delimiter", [",", ";", "\t"])
def test_supported_delimiters_are_detected(delimiter):
    raw = f"id{delimiter}opinion\n1{delimiter}Muy bueno\n2{delimiter}Muy malo\n".encode()
    frame = read_csv_upload(raw)
    assert list(frame.columns) == ["id", "opinion"]
    assert len(frame) == 2


def test_malformed_csv_is_rejected():
    raw = b'column_a,column_b\n"unterminated,value\n'
    with pytest.raises(CSVValidationError, match="encoding or delimiter"):
        read_csv_upload(raw)


def test_upload_size_limit_is_enforced_before_parsing():
    with pytest.raises(CSVValidationError, match="10 MB"):
        read_csv_upload(b"x" * (MAX_UPLOAD_BYTES + 1))


def test_row_limit_is_enforced():
    rows = "comment\n" + "\n".join(f"valid text {index}" for index in range(MAX_ROWS + 1))
    with pytest.raises(CSVValidationError, match="10,001 rows"):
        read_csv_upload(rows.encode())


def test_invalid_text_column_is_rejected():
    with pytest.raises(CSVValidationError, match="does not exist"):
        prepare_text_column(pd.DataFrame({"comment": ["ok"]}), "missing")


def test_null_and_blank_texts_are_removed():
    prepared, dropped = prepare_text_column(
        pd.DataFrame({"feedback": ["Excelente", None, " ", "x", "Terrible"]}),
        "feedback",
    )
    assert prepared["text"].tolist() == ["Excelente", "Terrible"]
    assert dropped == 3


def test_anonymization_removes_common_pii():
    source = "Ana: ana@example.com, +54 11 5555-1234, https://example.com, cliente 12345678"
    result = anonymize_text(source)
    assert "ana@example.com" not in result
    assert "5555" not in result
    assert "https://" not in result
    assert "12345678" not in result
    assert all(marker in result for marker in ("[EMAIL]", "[PHONE]", "[URL]", "[ID]"))


def test_anonymization_handles_international_phone_and_preserves_name_text():
    result = anonymize_text("Nombre: Ana Pérez; +1 (202) 555-0182; caso ABC-123456789")
    assert "Ana Pérez" in result
    assert "202" not in result
    assert "123456789" not in result
    assert result.count("[PHONE]") == 2


"""CSV validation, text normalization and privacy helpers."""

from __future__ import annotations

import csv
from io import BytesIO, StringIO
import re
from typing import BinaryIO

import pandas as pd


MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_ROWS = 10_000
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")
URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
LONG_ID_PATTERN = re.compile(r"\b\d{6,}\b")


class CSVValidationError(ValueError):
    """Raised when an uploaded CSV cannot be processed safely."""


def _is_coherent_single_column(text: str) -> bool:
    if "\x00" in text or any(ord(character) < 32 and character not in "\r\n\t" for character in text):
        return False
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        return False
    for delimiter in (",", ";", "\t"):
        try:
            header = next(csv.reader([lines[0]], delimiter=delimiter, strict=True))
            list(csv.reader(StringIO(text), delimiter=delimiter, strict=True))
        except csv.Error:
            return False
        if len(header) != 1:
            return False
    return True


def read_csv_upload(source: bytes | BinaryIO, max_bytes: int = MAX_UPLOAD_BYTES) -> pd.DataFrame:
    raw = source if isinstance(source, bytes) else source.read()
    if not raw:
        raise CSVValidationError("The CSV file is empty.")
    if len(raw) > max_bytes:
        raise CSVValidationError(f"The CSV exceeds the {max_bytes // (1024 * 1024)} MB limit.")

    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            frame = pd.read_csv(BytesIO(raw), sep=None, engine="python", encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
        except (pd.errors.ParserError, pd.errors.EmptyDataError):
            try:
                decoded = raw.decode(encoding)
            except UnicodeDecodeError:
                continue
            if not _is_coherent_single_column(decoded):
                continue
            try:
                frame = pd.read_csv(StringIO(decoded), sep="\x1f", engine="python")
                break
            except (pd.errors.ParserError, pd.errors.EmptyDataError):
                continue
    else:
        raise CSVValidationError("The CSV encoding or delimiter could not be detected.") from None

    if frame.empty or not len(frame.columns):
        raise CSVValidationError("The CSV contains no data rows.")
    if len(frame) > MAX_ROWS:
        raise CSVValidationError(f"The CSV contains {len(frame):,} rows; the limit is {MAX_ROWS:,}.")
    frame.columns = [str(column).strip() or f"column_{index + 1}" for index, column in enumerate(frame.columns)]
    return frame


def prepare_text_column(frame: pd.DataFrame, column: str) -> tuple[pd.DataFrame, int]:
    if column not in frame.columns:
        raise CSVValidationError(f"Column '{column}' does not exist.")
    values = frame[column]
    clean = values.fillna("").astype(str).str.strip()
    valid_mask = clean.str.len() >= 2
    dropped = int((~valid_mask).sum())
    prepared = pd.DataFrame({"text": clean[valid_mask]}).reset_index(drop=True)
    if prepared.empty:
        raise CSVValidationError("The selected column has no valid text values.")
    return prepared, dropped


def anonymize_text(text: str, max_chars: int = 240) -> str:
    value = EMAIL_PATTERN.sub("[EMAIL]", str(text))
    value = PHONE_PATTERN.sub("[PHONE]", value)
    value = URL_PATTERN.sub("[URL]", value)
    value = LONG_ID_PATTERN.sub("[ID]", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:max_chars]

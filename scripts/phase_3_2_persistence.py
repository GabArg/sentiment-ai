"""Append-only persistence primitives for the Phase 3.2 experiment."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


RESULT_FIELDS = (
    "case_id", "language", "expected_sentiment", "original_text", "anonymized_original",
    "translated_text", "local_original_prediction", "local_original_confidence",
    "local_translated_prediction", "local_translated_confidence", "review_original_requested",
    "review_original_result", "review_original_state", "review_original_error_code",
    "review_translated_requested", "review_translated_result", "review_translated_state",
    "review_translated_error_code", "translation_latency_ms", "review_original_latency_ms",
    "review_translated_latency_ms", "translation_input_tokens", "translation_output_tokens",
    "review_original_input_tokens", "review_original_output_tokens",
    "review_translated_input_tokens", "review_translated_output_tokens", "timestamps",
    "translation_raw_response", "review_original_raw_response", "review_translated_raw_response",
)
COST_FIELDS = (
    "case_id", "architecture", "call_type", "input_tokens", "output_tokens", "total_tokens",
    "cost_usd", "latency_ms", "state", "error_code", "started_at", "completed_at",
)


class ExperimentJournal:
    def __init__(self, result_path: Path, summary_path: Path, cost_path: Path) -> None:
        self.result_path = result_path
        self.summary_path = summary_path
        self.cost_path = cost_path
        for path in (result_path, summary_path, cost_path):
            path.parent.mkdir(parents=True, exist_ok=True)

    def append_result(self, event: str, record: dict[str, Any]) -> None:
        missing = set(RESULT_FIELDS) - set(record)
        if missing:
            raise ValueError(f"Result record missing fields: {sorted(missing)}")
        payload = {"event": event, **record}
        with self.result_path.open("a", encoding="utf-8", newline="") as stream:
            stream.write(json.dumps(payload, ensure_ascii=False) + "\n")
            stream.flush()

    def append_cost(self, row: dict[str, Any]) -> None:
        missing = set(COST_FIELDS) - set(row)
        if missing:
            raise ValueError(f"Cost row missing fields: {sorted(missing)}")
        exists = self.cost_path.exists() and self.cost_path.stat().st_size > 0
        with self.cost_path.open("a", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=COST_FIELDS)
            if not exists:
                writer.writeheader()
            writer.writerow({field: row.get(field) for field in COST_FIELDS})
            stream.flush()

    def write_summary(self, summary: dict[str, Any]) -> None:
        temporary = self.summary_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.summary_path)

    def latest_records(self) -> dict[tuple[str, str], dict[str, Any]]:
        latest = {}
        if not self.result_path.exists():
            return latest
        for line in self.result_path.read_text(encoding="utf-8").splitlines():
            payload = json.loads(line)
            latest[(payload["case_id"], payload["architecture"])] = payload
        return latest

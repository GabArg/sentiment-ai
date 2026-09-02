import csv
import json
from pathlib import Path

import pytest
import pandas as pd

from scripts.phase_3_2_persistence import COST_FIELDS, RESULT_FIELDS, ExperimentJournal


def _record():
    record = {field: None for field in RESULT_FIELDS}
    record.update({
        "case_id": "case-1", "architecture": "B", "language": "en",
        "expected_sentiment": "Neutro", "original_text": "Order received.",
        "anonymized_original": "Order received.", "timestamps": {},
    })
    return record


def test_journal_persists_each_result_and_cost_immediately(tmp_path):
    journal = ExperimentJournal(tmp_path / "results.jsonl", tmp_path / "summary.json", tmp_path / "costs.csv")
    journal.append_result("review_success", _record())
    cost = {field: None for field in COST_FIELDS}
    cost.update({"case_id": "case-1", "architecture": "B", "call_type": "review_original", "state": "success"})
    journal.append_cost(cost)

    payload = json.loads((tmp_path / "results.jsonl").read_text(encoding="utf-8"))
    rows = list(csv.DictReader((tmp_path / "costs.csv").open(encoding="utf-8")))
    assert payload["case_id"] == "case-1" and payload["event"] == "review_success"
    assert rows[0]["call_type"] == "review_original"


def test_journal_summary_is_atomic_and_latest_records_are_recoverable(tmp_path):
    journal = ExperimentJournal(tmp_path / "results.jsonl", tmp_path / "summary.json", tmp_path / "costs.csv")
    record = _record()
    journal.append_result("started", record)
    record["review_original_state"] = "success"
    journal.append_result("completed", record)
    journal.write_summary({"calls": 1})
    assert journal.latest_records()[("case-1", "B")]["review_original_state"] == "success"
    assert json.loads((tmp_path / "summary.json").read_text())["calls"] == 1


def test_journal_rejects_incomplete_records(tmp_path):
    journal = ExperimentJournal(tmp_path / "results.jsonl", tmp_path / "summary.json", tmp_path / "costs.csv")
    with pytest.raises(ValueError, match="missing fields"):
        journal.append_result("bad", {"case_id": "x"})


def test_versioned_experiment_artifacts_are_complete_and_secret_free():
    root = Path(__file__).parents[1]
    directory = root / "artifacts" / "experiments"
    results_path = directory / "multilingual_phase_3_2_results.jsonl"
    summary_path = directory / "multilingual_phase_3_2_summary.json"
    costs_path = directory / "multilingual_phase_3_2_costs.csv"
    results = [json.loads(line) for line in results_path.read_text(encoding="utf-8").splitlines()]
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    costs = pd.read_csv(costs_path)
    serialized = results_path.read_text(encoding="utf-8")
    assert len(costs) == summary["new_calls"] == 30
    assert len(results) == 39 and set(costs.architecture) == {"A", "B"}
    assert "CEREBRAS_API_KEY" not in serialized and "Bearer " not in serialized
    assert costs.state.value_counts().to_dict() == {"success": 29, "error": 1}

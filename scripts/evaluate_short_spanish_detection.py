"""Offline stability analysis for the eight short-Spanish risk cases."""

from __future__ import annotations

import json
from pathlib import Path
import re

import pandas as pd
from langdetect import detect_langs

from src.language_detection import LocalLanguageDetector


FIXTURE = Path("tests/fixtures/multilingual_risk_benchmark.csv")


def evaluate(repetitions: int = 10) -> dict[str, object]:
    data = pd.read_csv(FIXTURE)
    cases = data[data.group == "spanish_short"]
    detector = LocalLanguageDetector()
    rows = []
    for case in cases.itertuples(index=False):
        runs = [detector.detect(case.text).detected_language for _ in range(repetitions)]
        distribution = [
            {"language": item.lang, "score": item.prob}
            for item in detect_langs(case.text)
        ]
        rows.append(
            {
                "text": case.text,
                "words": len(re.findall(r"\b[\wáéíóúüñÁÉÍÓÚÜÑ]+\b", case.text)),
                "characters": len(case.text),
                "detected": runs[0],
                "correct": runs[0] == "es",
                "stable": len(set(runs)) == 1,
                "top_score": distribution[0]["score"],
                "top_gap": distribution[0]["score"] - distribution[1]["score"] if len(distribution) > 1 else None,
                "distribution": distribution,
            }
        )
    return {
        "cases": len(rows),
        "accuracy": sum(row["correct"] for row in rows) / len(rows),
        "stable_cases": sum(row["stable"] for row in rows),
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), ensure_ascii=False, indent=2))

"""Manual Cerebras smoke test for at most ten explicitly supplied comments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.sentiment_review import CerebrasSentimentReviewProvider


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", action="append", required=True, help="Repeat for 1-10 comments")
    parser.add_argument("--output", type=Path, help="Optional privacy-minimized JSON output")
    args = parser.parse_args()
    if not 1 <= len(args.text) <= 10:
        parser.error("Provide between 1 and 10 --text values.")

    provider = CerebrasSentimentReviewProvider()
    exported = []
    for index, text in enumerate(args.text, start=1):
        result = provider.review_sentiment(text)
        item = {
            "case": index,
            "sentiment": result.sentiment,
            "confidence": result.confidence,
            "provider": result.provider,
            "model": result.model,
            "success": result.success,
            "error_code": result.error_code,
            "usage": result.usage,
        }
        exported.append(item)
        print(json.dumps(item, ensure_ascii=False))
    if args.output:
        args.output.write_text(json.dumps(exported, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

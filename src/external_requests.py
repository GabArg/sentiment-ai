"""Shared pacing and budget for every Cerebras call in one operation."""

from __future__ import annotations

from collections import Counter

from src.rate_pacer import RatePacer


class ExternalRequestCoordinator:
    def __init__(self, max_calls: int, pacer: RatePacer, on_pacing=None) -> None:
        if max_calls < 1:
            raise ValueError("External request budget must be at least 1.")
        self.max_calls = max_calls
        self.pacer = pacer
        self.on_pacing = on_pacing
        self.calls = Counter()

    @property
    def used(self) -> int:
        return sum(self.calls.values())

    @property
    def remaining(self) -> int:
        return max(0, self.max_calls - self.used)

    def acquire(self, kind: str) -> bool:
        if kind not in {"translation", "sentiment_review"}:
            raise ValueError("Unsupported external request kind.")
        if self.used >= self.max_calls:
            return False
        self.pacer.wait_if_needed(self.on_pacing)
        self.calls[kind] += 1
        return True

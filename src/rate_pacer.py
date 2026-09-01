"""Injectable fixed-window pacing for sequential external reviews."""

from __future__ import annotations

from collections import deque
import time
from typing import Callable


class RatePacer:
    def __init__(
        self,
        max_requests: int = 5,
        window_seconds: float = 60.0,
        margin_seconds: float = 0.25,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        if max_requests < 1 or window_seconds <= 0 or margin_seconds < 0:
            raise ValueError("Invalid pacing configuration.")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.margin_seconds = margin_seconds
        self.clock = clock
        self.sleeper = sleeper
        self._timestamps: deque[float] = deque()

    def wait_if_needed(self, on_wait: Callable[[float], None] | None = None) -> float:
        now = self.clock()
        self._discard_expired(now)
        waited = 0.0
        if len(self._timestamps) >= self.max_requests:
            waited = max(0.0, self.window_seconds - (now - self._timestamps[0]) + self.margin_seconds)
            if waited:
                if on_wait is not None:
                    on_wait(waited)
                self.sleeper(waited)
                now = self.clock()
                self._discard_expired(now)
        self._timestamps.append(self.clock())
        return waited

    def _discard_expired(self, now: float) -> None:
        while self._timestamps and now - self._timestamps[0] >= self.window_seconds:
            self._timestamps.popleft()

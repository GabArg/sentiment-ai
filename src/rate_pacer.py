"""Atomic rolling-window pacing for sequential external requests."""

from __future__ import annotations

from collections import deque
import time
from threading import Lock
from typing import Callable


class RatePacer:
    def __init__(
        self,
        max_requests: int = 5,
        window_seconds: float = 60.0,
        margin_seconds: float = 2.0,
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
        self._lock = Lock()

    def wait_if_needed(self, on_wait: Callable[[float], None] | None = None) -> float:
        with self._lock:
            waited = 0.0
            effective_window = self.window_seconds + self.margin_seconds
            while True:
                now = self.clock()
                self._discard_expired(now, effective_window)
                if len(self._timestamps) < self.max_requests:
                    self._timestamps.append(now)  # reserve before releasing the lock
                    return waited
                delay = max(0.0, effective_window - (now - self._timestamps[0]))
                if delay <= 0:
                    continue
                if on_wait is not None:
                    on_wait(delay)
                self.sleeper(delay)
                waited += delay

    def _discard_expired(self, now: float, effective_window: float | None = None) -> None:
        expiry = self.window_seconds + self.margin_seconds if effective_window is None else effective_window
        while self._timestamps and now - self._timestamps[0] >= expiry:
            self._timestamps.popleft()

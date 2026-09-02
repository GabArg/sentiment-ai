from __future__ import annotations

import pytest

from src.rate_pacer import RatePacer


class FakeTime:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


def test_first_five_requests_pass_and_sixth_waits():
    fake = FakeTime()
    pacer = RatePacer(5, 60, 0.25, fake.clock, fake.sleep)
    assert [pacer.wait_if_needed() for _ in range(5)] == [0] * 5
    assert pacer.wait_if_needed() == pytest.approx(60.25)
    assert fake.sleeps == [pytest.approx(60.25)]


def test_expired_window_does_not_wait():
    fake = FakeTime()
    pacer = RatePacer(2, 10, 0, fake.clock, fake.sleep)
    pacer.wait_if_needed()
    pacer.wait_if_needed()
    fake.now = 10
    assert pacer.wait_if_needed() == 0
    assert fake.sleeps == []


def test_exact_window_boundary_keeps_safety_margin():
    fake = FakeTime()
    pacer = RatePacer(1, 60, 2, fake.clock, fake.sleep)
    pacer.wait_if_needed()
    fake.now = 60
    assert pacer.wait_if_needed() == pytest.approx(2)


def test_pacer_reevaluates_after_imprecise_sleep():
    fake = FakeTime()
    calls = []
    def imprecise(seconds):
        calls.append(seconds)
        fake.now += seconds / 2 if len(calls) == 1 else seconds
    pacer = RatePacer(1, 10, 2, fake.clock, imprecise)
    pacer.wait_if_needed()
    assert pacer.wait_if_needed() == pytest.approx(18)
    assert calls == [pytest.approx(12), pytest.approx(6)]


def test_old_timestamps_are_purged_after_effective_window():
    fake = FakeTime()
    pacer = RatePacer(2, 10, 2, fake.clock, fake.sleep)
    pacer.wait_if_needed()
    fake.now = 1
    pacer.wait_if_needed()
    fake.now = 12
    assert pacer.wait_if_needed() == 0
    assert len(pacer._timestamps) == 2


def test_consecutive_reservations_cannot_reuse_single_slot():
    fake = FakeTime()
    pacer = RatePacer(1, 10, 2, fake.clock, fake.sleep)
    assert pacer.wait_if_needed() == 0
    assert pacer.wait_if_needed() == pytest.approx(12)


def test_default_clock_is_monotonic():
    import time
    assert RatePacer().clock is time.monotonic

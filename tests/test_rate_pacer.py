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

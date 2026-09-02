import pytest

from src.external_requests import ExternalRequestCoordinator
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


def test_translation_and_review_share_one_pacing_window():
    fake = FakeTime()
    coordinator = ExternalRequestCoordinator(10, RatePacer(5, 60, 0.25, fake.clock, fake.sleep))
    for _ in range(3):
        assert coordinator.acquire("translation")
    for _ in range(2):
        assert coordinator.acquire("sentiment_review")
    assert fake.sleeps == []
    assert coordinator.acquire("translation")
    assert fake.sleeps == [pytest.approx(60.25)]
    assert coordinator.calls == {"translation": 4, "sentiment_review": 2}


def test_global_budget_never_allows_extra_request():
    coordinator = ExternalRequestCoordinator(2, RatePacer(5, 60))
    assert coordinator.acquire("translation")
    assert coordinator.acquire("sentiment_review")
    assert not coordinator.acquire("translation")
    assert coordinator.used == 2 and coordinator.remaining == 0


def test_coordinator_rejects_unknown_request_kind():
    coordinator = ExternalRequestCoordinator(2, RatePacer(5, 60))
    with pytest.raises(ValueError):
        coordinator.acquire("report")

from __future__ import annotations

import pytest

from src.model import SentimentPredictor


@pytest.fixture(scope="session")
def predictor() -> SentimentPredictor:
    return SentimentPredictor.load()


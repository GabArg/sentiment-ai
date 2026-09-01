from __future__ import annotations

import pytest

from src.hybrid_config import load_hybrid_config


def test_hybrid_feature_flag_is_off_by_default():
    config = load_hybrid_config(secrets={}, environ={})
    assert not config.enabled
    assert config.max_reviews_per_batch == 25


def test_hybrid_configuration_accepts_environment_and_secrets():
    config = load_hybrid_config(
        secrets={"ENABLE_HYBRID_SENTIMENT": True, "HYBRID_THRESHOLD_NEUTRAL": 0.62},
        environ={"HYBRID_THRESHOLD_POSITIVE": "0.58"},
    )
    assert config.enabled
    assert config.neutral_threshold == 0.62
    assert config.positive_threshold == 0.58
    assert config.router_config().threshold_for("Negativo") == 0.80


def test_invalid_feature_flag_is_rejected():
    with pytest.raises(ValueError, match="true or false"):
        load_hybrid_config(secrets={}, environ={"ENABLE_HYBRID_SENTIMENT": "sometimes"})


def test_invalid_pacing_window_is_rejected():
    with pytest.raises(ValueError, match="pacing window"):
        load_hybrid_config(secrets={}, environ={"HYBRID_WINDOW_SECONDS": "0"})

import pytest

from src.multilingual_config import load_multilingual_config


def test_multilingual_flag_is_off_by_default():
    config = load_multilingual_config(secrets={}, environ={})
    assert not config.enabled and config.max_external_calls_per_batch == 25


def test_multilingual_flag_reads_secrets_and_environment():
    assert load_multilingual_config(secrets={"ENABLE_MULTILINGUAL_SENTIMENT": True}, environ={}).enabled
    assert load_multilingual_config(secrets={}, environ={"ENABLE_MULTILINGUAL_SENTIMENT": "true"}).enabled


def test_global_budget_precedes_legacy_alias():
    config = load_multilingual_config(
        secrets={},
        environ={
            "ENABLE_MULTILINGUAL_SENTIMENT": "true",
            "HYBRID_MAX_EXTERNAL_CALLS_PER_BATCH": "9",
            "HYBRID_MAX_REVIEWS_PER_BATCH": "4",
        },
    )
    assert config.max_external_calls_per_batch == 9


def test_legacy_review_budget_is_alias_only_when_multilingual_on():
    enabled = load_multilingual_config(
        secrets={}, environ={"ENABLE_MULTILINGUAL_SENTIMENT": "true", "HYBRID_MAX_REVIEWS_PER_BATCH": "7"}
    )
    disabled = load_multilingual_config(
        secrets={}, environ={"ENABLE_MULTILINGUAL_SENTIMENT": "false", "HYBRID_MAX_REVIEWS_PER_BATCH": "7"}
    )
    assert enabled.max_external_calls_per_batch == 7
    assert disabled.max_external_calls_per_batch == 25


def test_invalid_multilingual_config_is_rejected():
    with pytest.raises(ValueError):
        load_multilingual_config(secrets={}, environ={"ENABLE_MULTILINGUAL_SENTIMENT": "maybe"})
    with pytest.raises(ValueError):
        load_multilingual_config(
            secrets={}, environ={"ENABLE_MULTILINGUAL_SENTIMENT": "true", "HYBRID_MAX_EXTERNAL_CALLS_PER_BATCH": "0"}
        )

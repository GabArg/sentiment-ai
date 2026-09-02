"""Opt-in configuration for multilingual sentiment preparation."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any, Mapping


def _value(name: str, secrets: Mapping[str, Any] | None, environ: Mapping[str, str]) -> Any:
    if secrets is not None:
        try:
            value = secrets.get(name)
        except Exception:
            value = None
        if value is not None:
            return value
    return environ.get(name)


def _boolean(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().casefold()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off", ""}:
        return False
    raise ValueError("ENABLE_MULTILINGUAL_SENTIMENT must be true or false.")


@dataclass(frozen=True)
class MultilingualConfig:
    enabled: bool = False
    max_external_calls_per_batch: int = 25

    def __post_init__(self) -> None:
        if self.max_external_calls_per_batch < 1:
            raise ValueError("HYBRID_MAX_EXTERNAL_CALLS_PER_BATCH must be at least 1.")


def load_multilingual_config(
    secrets: Mapping[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
) -> MultilingualConfig:
    values = os.environ if environ is None else environ
    enabled = _boolean(_value("ENABLE_MULTILINGUAL_SENTIMENT", secrets, values))
    global_limit = _value("HYBRID_MAX_EXTERNAL_CALLS_PER_BATCH", secrets, values)
    if global_limit is None and enabled:
        global_limit = _value("HYBRID_MAX_REVIEWS_PER_BATCH", secrets, values)
    limit = 25 if global_limit is None else int(global_limit)
    return MultilingualConfig(enabled=enabled, max_external_calls_per_batch=limit)

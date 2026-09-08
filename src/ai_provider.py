"""Optional Cerebras executive-report provider with safe fallback."""

from __future__ import annotations

import logging
import os
from typing import Any, Callable
from uuid import uuid4

from src.report_contract import (
    ASSISTED_READING_SCHEMA_VERSION,
    AssistedReading,
    ReportContractError,
    ReportFacts,
    parse_assisted_reading,
)
from src.reporting import build_ai_prompt


DEFAULT_CEREBRAS_MODEL = "gpt-oss-120b"
LOGGER = logging.getLogger(__name__)


class AIProviderError(RuntimeError):
    """Normalized error that is safe to display without leaking credentials."""

    def __init__(
        self,
        message: str,
        *,
        stage: str,
        code: str,
        exception_type: str | None = None,
        http_status: int | None = None,
    ) -> None:
        super().__init__(message)
        self.stage = stage
        self.code = code
        self.exception_type = exception_type
        self.http_status = http_status


def _http_status(exc: Exception) -> int | None:
    status = getattr(exc, "status_code", None)
    if status is None:
        status = getattr(getattr(exc, "response", None), "status_code", None)
    return status if isinstance(status, int) else None


def _normalized_error(stage: str, code: str, exc: Exception) -> AIProviderError:
    return AIProviderError(
        "Cerebras could not generate a valid report.",
        stage=stage,
        code=code,
        exception_type=type(exc).__name__,
        http_status=_http_status(exc),
    )


def resolve_api_key(explicit_key: str | None = None) -> str | None:
    return explicit_key or os.getenv("CEREBRAS_API_KEY") or None


def generate_cerebras_report(
    context: dict[str, object],
    facts: ReportFacts,
    api_key: str | None = None,
    model: str = DEFAULT_CEREBRAS_MODEL,
    client_factory: Callable[..., Any] | None = None,
) -> AssistedReading:
    key = resolve_api_key(api_key)
    if not key:
        raise AIProviderError(
            "CEREBRAS_API_KEY is not configured.",
            stage="configuration",
            code="missing_api_key",
        )
    try:
        if client_factory is None:
            from cerebras.cloud.sdk import Cerebras

            client_factory = Cerebras
        client = client_factory(api_key=key, timeout=30.0)
    except Exception as exc:
        raise _normalized_error("client_initialization", "client_initialization_failed", exc) from exc
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": build_ai_prompt(context)}],
            temperature=0.2,
            max_completion_tokens=1_200,
        )
    except Exception as exc:
        raise _normalized_error("provider_request", "provider_request_failed", exc) from exc
    try:
        content = response.choices[0].message.content
    except Exception as exc:
        raise _normalized_error("provider_response", "invalid_response_shape", exc) from exc
    if not isinstance(content, str) or not content.strip():
        exc = TypeError("Provider content is missing or empty.")
        raise _normalized_error("provider_response", "missing_response_content", exc)
    try:
        return parse_assisted_reading(content, facts)
    except ReportContractError as exc:
        raise _normalized_error("contract_validation", exc.code, exc) from exc
    except Exception as exc:
        raise _normalized_error("contract_validation", "contract_validation_failed", exc) from exc


def generate_report_with_fallback(
    context: dict[str, object],
    facts: ReportFacts,
    **provider_kwargs: Any,
) -> tuple[AssistedReading | None, bool, str | None]:
    try:
        return generate_cerebras_report(context, facts, **provider_kwargs), True, None
    except AIProviderError as exc:
        error_id = uuid4().hex[:12]
        LOGGER.warning(
            "assisted_report_fallback error_id=%s stage=%s code=%s exception_type=%s "
            "http_status=%s contract_version=%s",
            error_id,
            exc.stage,
            exc.code,
            exc.exception_type or "none",
            exc.http_status if exc.http_status is not None else "none",
            ASSISTED_READING_SCHEMA_VERSION,
        )
        return None, False, str(exc)


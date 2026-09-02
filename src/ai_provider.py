"""Optional Cerebras executive-report provider with safe fallback."""

from __future__ import annotations

import os
from typing import Any, Callable

from src.reporting import build_ai_prompt


DEFAULT_CEREBRAS_MODEL = "gpt-oss-120b"


class AIProviderError(RuntimeError):
    """Normalized error that is safe to display without leaking credentials."""


def resolve_api_key(explicit_key: str | None = None) -> str | None:
    return explicit_key or os.getenv("CEREBRAS_API_KEY") or None


def generate_cerebras_report(
    context: dict[str, object],
    api_key: str | None = None,
    model: str = DEFAULT_CEREBRAS_MODEL,
    client_factory: Callable[..., Any] | None = None,
) -> str:
    key = resolve_api_key(api_key)
    if not key:
        raise AIProviderError("CEREBRAS_API_KEY is not configured.")
    try:
        if client_factory is None:
            from cerebras.cloud.sdk import Cerebras

            client_factory = Cerebras
        client = client_factory(api_key=key, timeout=30.0)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": build_ai_prompt(context)}],
            temperature=0.2,
            max_completion_tokens=1_200,
        )
        content = response.choices[0].message.content
        if not isinstance(content, str) or len(content.strip()) < 80:
            raise ValueError("The provider returned an invalid report.")
        return content.strip()
    except AIProviderError:
        raise
    except Exception as exc:
        raise AIProviderError("Cerebras could not generate a valid report.") from exc


def generate_report_with_fallback(
    deterministic_report: str,
    context: dict[str, object],
    **provider_kwargs: Any,
) -> tuple[str, bool, str | None]:
    try:
        return generate_cerebras_report(context, **provider_kwargs), True, None
    except AIProviderError as exc:
        return deterministic_report, False, str(exc)


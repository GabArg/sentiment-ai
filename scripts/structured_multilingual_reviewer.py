"""Strict, experiment-only multilingual sentiment reviewer."""

from __future__ import annotations

from dataclasses import dataclass
import json
from time import perf_counter
from typing import Any

from src.ai_provider import DEFAULT_CEREBRAS_MODEL, resolve_api_key
from src.preprocessing import anonymize_text

SENTIMENTS = ("Negativo", "Neutro", "Positivo")
VARIANT_TOKENS = {"sentiment_rationale": 192, "sentiment_only": 128}


def response_schema(variant: str) -> dict[str, Any]:
    properties: dict[str, Any] = {"sentiment": {"type": "string", "enum": list(SENTIMENTS)}}
    required = ["sentiment"]
    if variant == "sentiment_rationale":
        properties["rationale"] = {"type": "string", "maxLength": 120}
        required.append("rationale")
    elif variant != "sentiment_only":
        raise ValueError(f"Unknown contract variant: {variant}")
    return {"type": "object", "additionalProperties": False, "properties": properties, "required": required}


def build_prompt(text: str, variant: str) -> str:
    fields = (
        'Devuelva solo {"sentiment":"...","rationale":"..."}. La explicación debe tener como máximo '
        "120 caracteres, señalar brevemente la evidencia principal y no repetir el comentario."
        if variant == "sentiment_rationale"
        else 'Devuelva solo {"sentiment":"..."}.'
    )
    return (
        "Clasifique el sentimiento del comentario, que puede estar en español, inglés, portugués o italiano. "
        "Use exactamente Negativo, Neutro o Positivo. Descripciones puramente factuales son Neutro. "
        f"{fields}\nComentario anonimizado:\n{text}"
    )


@dataclass(frozen=True)
class StructuredReviewResult:
    success: bool
    sentiment: str | None = None
    rationale: str | None = None
    error_code: str | None = None
    raw_response: str | None = None
    finish_reason: str | None = None
    usage: dict[str, int] | None = None
    latency_ms: float = 0.0
    parse_status: str = "not_parsed"
    schema_valid: bool = False


class StructuredMultilingualSentimentReviewer:
    def __init__(self, timeout: float = 30.0, max_retries: int = 0, client: Any = None) -> None:
        self.api_key = resolve_api_key()
        self.model = DEFAULT_CEREBRAS_MODEL
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = client

    def review(self, text: str, variant: str, max_completion_tokens: int | None = None) -> StructuredReviewResult:
        started = perf_counter()
        if not self.api_key and self._client is None:
            return StructuredReviewResult(False, error_code="unavailable", latency_ms=(perf_counter() - started) * 1000)
        safe_text = anonymize_text(text)
        try:
            if self._client is None:
                from cerebras.cloud.sdk import Cerebras
                self._client = Cerebras(api_key=self.api_key, timeout=self.timeout, max_retries=self.max_retries)
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": build_prompt(safe_text, variant)}],
                temperature=0,
                max_completion_tokens=max_completion_tokens or VARIANT_TOKENS[variant],
                response_format={"type": "json_schema", "json_schema": {
                    "name": f"multilingual_sentiment_{variant}", "strict": True,
                    "schema": response_schema(variant),
                }},
            )
            choice = response.choices[0]
            raw = choice.message.content
            finish_reason = getattr(choice, "finish_reason", None)
            usage = _usage(response)
            latency = (perf_counter() - started) * 1000
            if not isinstance(raw, str) or not raw.strip():
                return StructuredReviewResult(False, error_code="empty_response", raw_response=raw, finish_reason=finish_reason, usage=usage, latency_ms=latency, parse_status="empty")
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                return StructuredReviewResult(False, error_code="invalid_json", raw_response=raw, finish_reason=finish_reason, usage=usage, latency_ms=latency, parse_status="invalid_json")
            error = _validate(payload, variant)
            if error:
                return StructuredReviewResult(False, error_code=error, raw_response=raw, finish_reason=finish_reason, usage=usage, latency_ms=latency, parse_status="schema_violation")
            return StructuredReviewResult(True, payload["sentiment"], payload.get("rationale"), raw_response=raw, finish_reason=finish_reason, usage=usage, latency_ms=latency, parse_status="valid", schema_valid=True)
        except Exception as exc:
            status = getattr(exc, "status_code", None)
            code = "rate_limited" if status == 429 else "timeout" if type(exc).__name__ in {"APITimeoutError", "TimeoutError"} else "provider_error"
            return StructuredReviewResult(False, error_code=code, latency_ms=(perf_counter() - started) * 1000)


def _validate(payload: Any, variant: str) -> str | None:
    expected = {"sentiment", "rationale"} if variant == "sentiment_rationale" else {"sentiment"}
    if not isinstance(payload, dict) or set(payload) != expected:
        return "invalid_schema"
    if payload.get("sentiment") not in SENTIMENTS:
        return "invalid_sentiment"
    if variant == "sentiment_rationale" and (not isinstance(payload["rationale"], str) or len(payload["rationale"]) > 120):
        return "invalid_rationale"
    return None


def _usage(response: Any) -> dict[str, int] | None:
    usage = getattr(response, "usage", None)
    values = {}
    for name in ("prompt_tokens", "completion_tokens", "total_tokens"):
        value = getattr(usage, name, None) if usage is not None else None
        if isinstance(value, int) and not isinstance(value, bool):
            values[name] = value
    return values or None

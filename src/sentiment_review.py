"""Structured provider contract for experimental sentiment second checks."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Callable, Protocol

from src.ai_provider import DEFAULT_CEREBRAS_MODEL, resolve_api_key
from src.preprocessing import anonymize_text


ALLOWED_SENTIMENTS = frozenset({"Negativo", "Neutro", "Positivo"})
REVIEW_PROMPT_VERSION = "sentiment-review-v1"
REVIEW_PROMPT = """Sos un clasificador de sentimiento. Clasificá exclusivamente el comentario incluido en COMENTARIO como Negativo, Neutro o Positivo.

Definiciones:
- Negativo: expresa queja, rechazo, frustración, daño o valoración desfavorable.
- Neutro: información factual, descripción sin opinión, estado objetivo o comentario sin valoración claramente positiva o negativa.
- Positivo: expresa satisfacción, aprobación, recomendación o valoración favorable.

Ejemplos:
- "El producto llegó roto." -> Negativo
- "El pedido llegó el martes." -> Neutro
- "La atención fue excelente." -> Positivo

Respondé únicamente JSON válido con este esquema exacto:
{{"sentiment":"Negativo|Neutro|Positivo","confidence":0.0,"rationale":"explicación breve"}}
No agregues categorías, planes de acción ni análisis de negocio.

COMENTARIO:
{text}
"""


@dataclass(frozen=True)
class ReviewResult:
    sentiment: str | None
    confidence: float | None
    rationale: str | None
    provider: str
    model: str
    success: bool
    error_code: str | None = None
    usage: dict[str, int] | None = None

    def __post_init__(self) -> None:
        if self.success:
            if self.sentiment not in ALLOWED_SENTIMENTS:
                raise ValueError("Successful review must contain an allowed sentiment.")
            if self.error_code is not None:
                raise ValueError("Successful review cannot contain an error code.")
        elif self.sentiment is not None:
            raise ValueError("Failed review cannot contain a sentiment.")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("Review confidence must be between 0 and 1.")
        if self.rationale is not None and len(self.rationale) > 240:
            raise ValueError("Review rationale must not exceed 240 characters.")


class SentimentReviewProvider(Protocol):
    def review_sentiment(self, text: str) -> ReviewResult: ...


def build_review_prompt(text: str) -> str:
    return REVIEW_PROMPT.format(text=anonymize_text(text))


def _failure(model: str, error_code: str) -> ReviewResult:
    return ReviewResult(
        sentiment=None,
        confidence=None,
        rationale=None,
        provider="cerebras",
        model=model,
        success=False,
        error_code=error_code,
    )


def _usage_from_response(response: Any) -> dict[str, int] | None:
    usage = getattr(response, "usage", None)
    if usage is None:
        return None
    values = {}
    for name in ("prompt_tokens", "completion_tokens", "total_tokens"):
        value = getattr(usage, name, None)
        if isinstance(value, int):
            values[name] = value
    return values or None


class CerebrasSentimentReviewProvider:
    """Cerebras adapter isolated from executive-report generation."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_CEREBRAS_MODEL,
        client_factory: Callable[..., Any] | None = None,
        timeout: float = 30.0,
        max_retries: int = 2,
    ) -> None:
        self.api_key = resolve_api_key(api_key)
        self.model = model
        self.client_factory = client_factory
        self.timeout = timeout
        self.max_retries = max_retries

    def review_sentiment(self, text: str) -> ReviewResult:
        if not self.api_key:
            return _failure(self.model, "unavailable")
        try:
            factory = self.client_factory
            if factory is None:
                from cerebras.cloud.sdk import Cerebras

                factory = Cerebras
            client = factory(
                api_key=self.api_key,
                timeout=self.timeout,
                max_retries=self.max_retries,
            )
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": build_review_prompt(text)}],
                temperature=0,
                max_completion_tokens=160,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            if not isinstance(content, str) or not content.strip():
                return _failure(self.model, "empty_response")
            try:
                payload = json.loads(content)
            except json.JSONDecodeError:
                return _failure(self.model, "invalid_json")
            allowed_keys = {"sentiment", "confidence", "rationale"}
            if (
                not isinstance(payload, dict)
                or set(payload) - allowed_keys
                or payload.get("sentiment") not in ALLOWED_SENTIMENTS
            ):
                return _failure(self.model, "invalid_sentiment")
            confidence = payload.get("confidence")
            if confidence is not None and (
                isinstance(confidence, bool)
                or not isinstance(confidence, (int, float))
                or not 0 <= float(confidence) <= 1
            ):
                return _failure(self.model, "invalid_confidence")
            rationale = payload.get("rationale")
            if rationale is not None and not isinstance(rationale, str):
                return _failure(self.model, "invalid_rationale")
            rationale = rationale.strip()[:240] if rationale else None
            return ReviewResult(
                sentiment=payload["sentiment"],
                confidence=float(confidence) if confidence is not None else None,
                rationale=rationale,
                provider="cerebras",
                model=self.model,
                success=True,
                usage=_usage_from_response(response),
            )
        except TimeoutError:
            return _failure(self.model, "timeout")
        except Exception as exc:
            status_code = getattr(exc, "status_code", None)
            if status_code == 429:
                error_code = "rate_limited"
            elif type(exc).__name__ == "APITimeoutError":
                error_code = "timeout"
            else:
                error_code = "provider_error"
            return _failure(self.model, error_code)

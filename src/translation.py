"""Strict Cerebras translation adapter, separate from sentiment review."""

from __future__ import annotations

import json
import time
from typing import Any, Callable

from src.ai_provider import DEFAULT_CEREBRAS_MODEL, resolve_api_key
from src.multilingual_contracts import TranslationResult
from src.preprocessing import anonymize_text


TRANSLATION_PROMPT_VERSION = "translation-es-v1"
TRANSLATION_PROMPT = """Traducí el texto de {source_language} a español.
Preservá exactamente la semántica, el tono, las negaciones, la intensidad, los números y los nombres de productos.
No resumas, no infieras sentimiento, no agregues contexto y no suavices el contenido.
Respondé únicamente JSON válido con este esquema exacto:
{{"source_language":"{source_language}","translated_text":"..."}}

TEXTO:
{text}
"""


def build_translation_prompt(text: str, source_language: str, target_language: str = "es") -> str:
    if target_language != "es":
        raise ValueError("The initial translation target must be Spanish.")
    return TRANSLATION_PROMPT.format(
        text=anonymize_text(text),
        source_language=source_language,
    )


def _usage_from_response(response: Any) -> dict[str, int] | None:
    usage = getattr(response, "usage", None)
    if usage is None:
        return None
    values = {}
    for name in ("prompt_tokens", "completion_tokens", "total_tokens"):
        value = getattr(usage, name, None)
        if isinstance(value, int) and not isinstance(value, bool):
            values[name] = value
    return values or None


class CerebrasTranslationProvider:
    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_CEREBRAS_MODEL,
        client_factory: Callable[..., Any] | None = None,
        timeout: float = 30.0,
        max_retries: int = 0,
    ) -> None:
        self.api_key = resolve_api_key(api_key)
        self.model = model
        self.client_factory = client_factory
        self.timeout = timeout
        self.max_retries = max_retries

    def translate(self, text: str, source_language: str, target_language: str = "es") -> TranslationResult:
        started = time.perf_counter()
        if not self.api_key:
            return self._failure(text, source_language, target_language, "unavailable", started)
        try:
            factory = self.client_factory
            if factory is None:
                from cerebras.cloud.sdk import Cerebras

                factory = Cerebras
            client = factory(api_key=self.api_key, timeout=self.timeout, max_retries=self.max_retries)
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": build_translation_prompt(text, source_language, target_language)}],
                temperature=0,
                max_completion_tokens=240,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            if not isinstance(content, str) or not content.strip():
                return self._failure(text, source_language, target_language, "empty_response", started)
            try:
                payload = json.loads(content)
            except json.JSONDecodeError:
                return self._failure(text, source_language, target_language, "invalid_json", started)
            if not isinstance(payload, dict) or set(payload) != {"source_language", "translated_text"}:
                return self._failure(text, source_language, target_language, "invalid_schema", started)
            if payload["source_language"] != source_language:
                return self._failure(text, source_language, target_language, "source_mismatch", started)
            translated = payload["translated_text"]
            if not isinstance(translated, str) or not translated.strip():
                return self._failure(text, source_language, target_language, "empty_translation", started)
            return TranslationResult(
                source_language=source_language,
                target_language=target_language,
                original_text=anonymize_text(text),
                translated_text=translated.strip(),
                provider="cerebras",
                model=self.model,
                success=True,
                latency_ms=(time.perf_counter() - started) * 1000,
                usage=_usage_from_response(response),
            )
        except TimeoutError:
            return self._failure(text, source_language, target_language, "timeout", started)
        except Exception as exc:
            status_code = getattr(exc, "status_code", None)
            if status_code == 429:
                error_code = "rate_limited"
            elif type(exc).__name__ == "APITimeoutError":
                error_code = "timeout"
            else:
                error_code = "provider_error"
            return self._failure(text, source_language, target_language, error_code, started)

    def _failure(self, text: str, source: str, target: str, code: str, started: float) -> TranslationResult:
        return TranslationResult(
            source_language=source,
            target_language=target,
            original_text=anonymize_text(text),
            translated_text=None,
            provider="cerebras",
            model=self.model,
            success=False,
            latency_ms=(time.perf_counter() - started) * 1000,
            error_code=code,
        )

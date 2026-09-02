"""Experiment-only Cerebras caller that preserves raw responses for audit."""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

from src.ai_provider import DEFAULT_CEREBRAS_MODEL, resolve_api_key
from src.sentiment_review import ALLOWED_SENTIMENTS, build_review_prompt
from src.translation import build_translation_prompt


class ExperimentalCerebrasCaller:
    def __init__(self, timeout: float = 30.0, max_retries: int = 0) -> None:
        self.api_key = resolve_api_key()
        self.model = DEFAULT_CEREBRAS_MODEL
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = None

    def review(self, text: str):
        return self._call("review", text=text)

    def translate(self, text: str, source_language: str):
        return self._call("translation", text=text, source_language=source_language)

    def _call(self, kind: str, text: str, source_language: str | None = None):
        if not self.api_key:
            return _result(False, "unavailable")
        try:
            if self._client is None:
                from cerebras.cloud.sdk import Cerebras

                self._client = Cerebras(api_key=self.api_key, timeout=self.timeout, max_retries=self.max_retries)
            prompt = build_review_prompt(text) if kind == "review" else build_translation_prompt(text, source_language or "")
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_completion_tokens=240 if kind == "translation" else 160,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content
            usage = _usage(response)
            if not isinstance(raw, str) or not raw.strip():
                return _result(False, "empty_response", raw=raw, usage=usage)
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                return _result(False, "invalid_json", raw=raw, usage=usage)
            if kind == "review":
                if not isinstance(payload, dict) or set(payload) - {"sentiment", "confidence", "rationale"}:
                    return _result(False, "invalid_schema", raw=raw, usage=usage)
                if payload.get("sentiment") not in ALLOWED_SENTIMENTS:
                    return _result(False, "invalid_sentiment", raw=raw, usage=usage)
                return _result(True, raw=raw, usage=usage, sentiment=payload["sentiment"])
            if not isinstance(payload, dict) or set(payload) != {"source_language", "translated_text"}:
                return _result(False, "invalid_schema", raw=raw, usage=usage)
            if payload.get("source_language") != source_language:
                return _result(False, "source_mismatch", raw=raw, usage=usage)
            translated = payload.get("translated_text")
            if not isinstance(translated, str) or not translated.strip():
                return _result(False, "empty_translation", raw=raw, usage=usage)
            return _result(True, raw=raw, usage=usage, translated_text=translated.strip())
        except Exception as exc:
            status = getattr(exc, "status_code", None)
            error = "rate_limited" if status == 429 else "timeout" if type(exc).__name__ in {"APITimeoutError", "TimeoutError"} else "provider_error"
            return _result(False, error)


def _usage(response: Any) -> dict[str, int] | None:
    usage = getattr(response, "usage", None)
    if usage is None:
        return None
    values = {}
    for name in ("prompt_tokens", "completion_tokens", "total_tokens"):
        value = getattr(usage, name, None)
        if isinstance(value, int) and not isinstance(value, bool):
            values[name] = value
    return values or None


def _result(success, error_code=None, raw=None, usage=None, sentiment=None, translated_text=None):
    return SimpleNamespace(
        success=success, error_code=error_code, raw_response=raw, usage=usage,
        sentiment=sentiment, translated_text=translated_text,
    )

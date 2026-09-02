"""Pure contracts for the proposed multilingual pipeline (Phase 3.0A).

This module intentionally contains no detector or external translation adapter.
Runtime integration belongs to Phase 3.0B after the design is reviewed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


SUPPORTED_LANGUAGES = {
    "es": "Español",
    "en": "Inglés",
    "pt": "Portugués",
    "it": "Italiano",
}
LANGUAGE_STATUSES = frozenset({"detected", "unsupported", "unknown", "error"})
TRANSLATION_STATES = frozenset(
    {
        "not_needed",
        "translated",
        "fallback_original",
        "unsupported_language",
        "detection_error",
    }
)


@dataclass(frozen=True)
class LanguageDetectionResult:
    detected_language: str | None
    language_name: str | None
    supported: bool
    confidence: float | None
    provider: str
    success: bool
    status: str
    error_code: str | None = None

    def __post_init__(self) -> None:
        if self.status not in LANGUAGE_STATUSES:
            raise ValueError("Unsupported language detection status.")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("Language confidence must be between 0 and 1.")
        if self.success != (self.status in {"detected", "unsupported"}):
            raise ValueError("Detection success and status are inconsistent.")
        if self.status == "detected":
            expected_name = SUPPORTED_LANGUAGES.get(self.detected_language or "")
            if not self.supported or expected_name != self.language_name:
                raise ValueError("Detected status requires a supported language.")
        elif self.supported:
            raise ValueError("Only detected languages can be marked supported.")
        if self.success and self.error_code is not None:
            raise ValueError("Successful detection cannot contain an error code.")
        if not self.success and not self.error_code:
            raise ValueError("Failed detection requires an error code.")


class LanguageDetector(Protocol):
    def detect(self, text: str) -> LanguageDetectionResult: ...


@dataclass(frozen=True)
class TranslationResult:
    source_language: str
    target_language: str
    original_text: str
    translated_text: str | None
    provider: str
    model: str
    success: bool
    latency_ms: float | None = None
    error_code: str | None = None
    usage: dict[str, int] | None = None

    def __post_init__(self) -> None:
        if self.source_language == self.target_language:
            raise ValueError("Translation source and target must differ.")
        if self.latency_ms is not None and self.latency_ms < 0:
            raise ValueError("Translation latency cannot be negative.")
        if self.success:
            if not self.translated_text or not self.translated_text.strip():
                raise ValueError("Successful translation requires translated text.")
            if self.error_code is not None:
                raise ValueError("Successful translation cannot contain an error code.")
        else:
            if self.translated_text is not None:
                raise ValueError("Failed translation cannot contain translated text.")
            if not self.error_code:
                raise ValueError("Failed translation requires an error code.")
        if self.usage is not None:
            if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in self.usage.values()):
                raise ValueError("Translation usage values must be non-negative integers.")


class TranslationProvider(Protocol):
    def translate(
        self,
        text: str,
        source_language: str,
        target_language: str = "es",
    ) -> TranslationResult: ...


@dataclass(frozen=True)
class MultilingualPreparationResult:
    """Auditable output of language preparation before sentiment inference."""

    original_text: str
    detected_language: str | None
    language_name: str | None
    language_supported: bool
    translation_requested: bool
    translation_state: str
    translated_text: str | None
    translation_provider: str | None
    translation_model: str | None
    translation_latency_ms: float | None
    translation_error_code: str | None
    analysis_text: str
    translation_usage: dict[str, int] | None = None

    def __post_init__(self) -> None:
        if self.translation_state not in TRANSLATION_STATES:
            raise ValueError("Unsupported translation state.")
        if not self.analysis_text:
            raise ValueError("Analysis text cannot be empty.")
        if self.translation_state == "translated":
            if not self.translation_requested or not self.translated_text:
                raise ValueError("Translated state requires a requested translation.")
            if self.analysis_text != self.translated_text:
                raise ValueError("Successful translation must become analysis text.")
        elif self.translated_text is not None:
            raise ValueError("Only translated state may expose translated text.")
        if self.translation_state in {"fallback_original", "unsupported_language", "detection_error"}:
            if self.analysis_text != self.original_text:
                raise ValueError("Fallback states must preserve original analysis text.")


TranslationUsage = dict[str, int]
RawTranslationPayload = dict[str, Any]

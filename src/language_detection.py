"""Deterministic, local language detection for the controlled language scope."""

from __future__ import annotations

from langdetect import DetectorFactory, detect
from langdetect.lang_detect_exception import LangDetectException

from src.multilingual_contracts import LanguageDetectionResult, SUPPORTED_LANGUAGES


DetectorFactory.seed = 0


class LocalLanguageDetector:
    provider = "langdetect"

    def detect(self, text: str) -> LanguageDetectionResult:
        if not isinstance(text, str) or not text.strip():
            return self._failure("unknown", "empty_text")
        try:
            language = detect(text)
        except LangDetectException:
            return self._failure("unknown", "undetectable_text")
        except Exception:
            return self._failure("error", "detector_error")

        language_name = SUPPORTED_LANGUAGES.get(language)
        if language_name is None:
            return LanguageDetectionResult(
                detected_language=language,
                language_name=None,
                supported=False,
                confidence=None,
                provider=self.provider,
                success=True,
                status="unsupported",
            )
        return LanguageDetectionResult(
            detected_language=language,
            language_name=language_name,
            supported=True,
            confidence=None,
            provider=self.provider,
            success=True,
            status="detected",
        )

    def _failure(self, status: str, error_code: str) -> LanguageDetectionResult:
        return LanguageDetectionResult(
            detected_language=None,
            language_name=None,
            supported=False,
            confidence=None,
            provider=self.provider,
            success=False,
            status=status,
            error_code=error_code,
        )

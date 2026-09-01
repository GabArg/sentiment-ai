"""Sentiment model loading and vectorized inference."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import joblib
import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = PROJECT_DIR / "models" / "sentiment_model.joblib"
DEFAULT_VECTORIZER_PATH = PROJECT_DIR / "models" / "tfidf_vectorizer.joblib"


@dataclass(frozen=True)
class SentimentPrediction:
    label: str
    confidence: float
    probabilities: dict[str, float]


class SentimentPredictor:
    """Thin, reusable wrapper around the original V6 artifacts."""

    def __init__(self, model: Any, vectorizer: Any) -> None:
        if not hasattr(model, "classes_") or not hasattr(model, "predict_proba"):
            raise TypeError("The classifier must expose classes_ and predict_proba().")
        if not hasattr(vectorizer, "transform"):
            raise TypeError("The vectorizer must expose transform().")
        self.model = model
        self.vectorizer = vectorizer
        self.classes = tuple(str(item) for item in model.classes_)

    @classmethod
    def load(
        cls,
        model_path: Path = DEFAULT_MODEL_PATH,
        vectorizer_path: Path = DEFAULT_VECTORIZER_PATH,
    ) -> "SentimentPredictor":
        missing = [path.name for path in (model_path, vectorizer_path) if not path.is_file()]
        if missing:
            raise FileNotFoundError(f"Missing local artifacts: {', '.join(missing)}")
        return cls(joblib.load(model_path), joblib.load(vectorizer_path))

    def predict_one(self, text: str) -> SentimentPrediction:
        clean_text = str(text).strip()
        if len(clean_text) < 2:
            raise ValueError("Text must contain at least two characters.")
        result = self.predict_batch([clean_text]).iloc[0]
        probabilities = {
            class_name: float(result[f"probability_{class_name.casefold()}"])
            for class_name in self.classes
        }
        return SentimentPrediction(
            label=str(result["sentiment"]),
            confidence=float(result["confidence"]),
            probabilities=probabilities,
        )

    def predict_batch(self, texts: Iterable[str]) -> pd.DataFrame:
        values = [str(text).strip() for text in texts]
        if not values:
            return self._empty_result()
        if any(len(text) < 2 for text in values):
            raise ValueError("Every text must contain at least two characters.")

        features = self.vectorizer.transform(values)
        labels = self.model.predict(features)
        probabilities = np.asarray(self.model.predict_proba(features), dtype=float)
        if probabilities.shape != (len(values), len(self.classes)):
            raise ValueError("The classifier returned an unexpected probability matrix.")

        class_indices = {name: index for index, name in enumerate(self.classes)}
        confidences = [probabilities[row, class_indices[str(label)]] for row, label in enumerate(labels)]
        result = pd.DataFrame(
            {
                "text": values,
                "sentiment": [str(label) for label in labels],
                "confidence": confidences,
            }
        )
        for index, class_name in enumerate(self.classes):
            result[f"probability_{class_name.casefold()}"] = probabilities[:, index]
        return result

    def _empty_result(self) -> pd.DataFrame:
        columns = ["text", "sentiment", "confidence"] + [
            f"probability_{class_name.casefold()}" for class_name in self.classes
        ]
        return pd.DataFrame(columns=columns)


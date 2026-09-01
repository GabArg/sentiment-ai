"""Efficient batch sentiment analysis."""

from __future__ import annotations

import pandas as pd

from src.model import SentimentPredictor
from src.preprocessing import prepare_text_column


def analyze_dataframe(
    frame: pd.DataFrame,
    text_column: str,
    predictor: SentimentPredictor,
) -> tuple[pd.DataFrame, int]:
    prepared, dropped = prepare_text_column(frame, text_column)
    predictions = predictor.predict_batch(prepared["text"].tolist())
    return predictions, dropped


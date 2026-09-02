"""Transparent negative-feedback topic extraction and Pareto analysis."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer


MULTILINGUAL_STOPWORDS = frozenset(
    """
    a al algo algunas algunos ante antes as at aunque be been being but by cada como con contra cual
    cuando da das de del desde do dos e el ela elas ele eles em en entre era es esa ese eso esta estaba
    este eu foi for from fue ha hay i in is it la las le les lo los mais mas me mi muy na nao no nos nossa
    o of on or os ou para pero por porque que se sem ser si sin sobre su sus the to tu um uma un una unos
    y ya yo you your muito producto product servico servicio service compra pedido order
    """.split()
)


def extract_negative_topics(
    texts: Iterable[str],
    max_topics: int = 15,
    min_document_frequency: int = 1,
) -> pd.DataFrame:
    documents = [str(text).strip().casefold() for text in texts if len(str(text).strip()) >= 2]
    if not documents:
        return pd.DataFrame(columns=["topic", "frequency"])

    vectorizer = CountVectorizer(
        lowercase=True,
        strip_accents="unicode",
        stop_words=list(MULTILINGUAL_STOPWORDS),
        ngram_range=(1, 2),
        min_df=min_document_frequency,
        binary=True,
        token_pattern=r"(?u)\b[^\W\d_]\w+\b",
    )
    try:
        matrix = vectorizer.fit_transform(documents)
    except ValueError:
        return pd.DataFrame(columns=["topic", "frequency"])
    frequencies = matrix.sum(axis=0).A1
    candidates = sorted(
        zip(vectorizer.get_feature_names_out(), frequencies, strict=True),
        key=lambda item: (-int(item[1]), -len(item[0].split()), item[0]),
    )

    # Prefer informative bigrams and avoid showing their redundant unigram parts.
    selected: list[tuple[str, int]] = []
    covered_unigrams: set[str] = set()
    for topic, frequency in candidates:
        words = topic.split()
        if len(words) == 1 and topic in covered_unigrams:
            continue
        selected.append((topic, int(frequency)))
        if len(words) == 2:
            covered_unigrams.update(words)
        if len(selected) >= max_topics:
            break
    return pd.DataFrame(selected, columns=["topic", "frequency"])


def calculate_pareto(topics: pd.DataFrame, threshold: float = 0.80) -> pd.DataFrame:
    if not 0 < threshold <= 1:
        raise ValueError("Pareto threshold must be between 0 and 1.")
    if topics.empty:
        return pd.DataFrame(
            columns=["topic", "frequency", "percentage", "cumulative_percentage", "within_80_percent"]
        )
    if not {"topic", "frequency"}.issubset(topics.columns):
        raise ValueError("Topics must include topic and frequency columns.")

    result = topics[["topic", "frequency"]].copy()
    result["frequency"] = pd.to_numeric(result["frequency"], errors="raise")
    result = result[result["frequency"] > 0].sort_values(
        ["frequency", "topic"], ascending=[False, True]
    ).reset_index(drop=True)
    total = float(result["frequency"].sum())
    if not total:
        return calculate_pareto(pd.DataFrame())
    result["percentage"] = result["frequency"] / total * 100
    result["cumulative_percentage"] = result["percentage"].cumsum()
    previous = result["cumulative_percentage"].shift(fill_value=0)
    result["within_80_percent"] = (previous < threshold * 100)
    return result

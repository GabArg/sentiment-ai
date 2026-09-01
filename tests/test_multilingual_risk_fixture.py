from pathlib import Path

import pandas as pd

from scripts.run_negation_validation import ORIGINAL_REVIEW_TYPES


FIXTURE = Path(__file__).parent / "fixtures" / "multilingual_risk_benchmark.csv"


def test_risk_fixture_has_exact_manual_structure():
    data = pd.read_csv(FIXTURE)
    assert len(data) == 24 and data["text"].is_unique
    assert data["group"].value_counts().to_dict() == {
        "negation": 12,
        "spanish_short": 8,
        "control": 4,
    }
    negations = data[data.group == "negation"]
    assert negations["language"].value_counts().to_dict() == {"en": 4, "pt": 4, "it": 4}
    for language in ("en", "pt", "it"):
        assert set(negations.loc[negations.language == language, "negation_type"]) == {
            "contrast", "negative", "factual", "ambiguous"
        }


def test_spanish_short_cases_are_two_to_six_words_and_include_known_failures():
    data = pd.read_csv(FIXTURE)
    short = data[data.group == "spanish_short"]
    lengths = short["text"].str.findall(r"\b[\wáéíóúüñÁÉÍÓÚÜÑ]+\b").str.len()
    assert lengths.between(2, 6).all()
    assert {"No resolvieron mi reclamo.", "Pésimo soporte; no vuelvo."}.issubset(set(short.text))


def test_expected_values_are_limited_to_contract():
    data = pd.read_csv(FIXTURE)
    assert set(data.expected_sentiment) == {"Negativo", "Neutro", "Positivo"}
    assert set(data.language) == {"es", "en", "pt", "it"}


def test_real_review_comparison_is_capped_at_six_cases():
    data = pd.read_csv(FIXTURE)
    selected = data[(data.group == "negation") & data.negation_type.isin(ORIGINAL_REVIEW_TYPES)]
    assert len(selected) == 6

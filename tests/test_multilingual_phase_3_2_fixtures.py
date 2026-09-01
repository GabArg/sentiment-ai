from pathlib import Path
import re

import pandas as pd


FIXTURES = Path(__file__).parent / "fixtures"


def test_comparison_fixture_is_balanced_and_call_cap_is_30():
    data = pd.read_csv(FIXTURES / "multilingual_phase_3_2_benchmark.csv")
    assert len(data) == 12 and data.case_id.is_unique and data.text.is_unique
    assert data.language.value_counts().to_dict() == {"en": 4, "pt": 4, "it": 4}
    assert data.groupby(["language", "case_type"]).size().eq(1).all()
    paired = data[data.paired_a]
    assert len(paired) == 9
    assert set(paired.case_type) == {"negative_clear", "neutral_factual", "negation_contrast"}
    assert len(data) + 2 * len(paired) == 30


def test_short_fixture_has_requested_languages_and_at_most_four_tokens():
    data = pd.read_csv(FIXTURES / "multilingual_short_texts.csv")
    assert data.language.value_counts().to_dict() == {"es": 8, "en": 4, "pt": 4, "it": 4}
    lengths = data.text.map(lambda text: len(re.findall(r"\b[\wáéíóúüñÁÉÍÓÚÜÑ]+\b", text)))
    assert len(data) == 20 and lengths.le(4).all()
    assert data.case_id.is_unique
    assert (data.text == "Nada mal.").sum() == 2  # Intentionally ambiguous across ES/PT.

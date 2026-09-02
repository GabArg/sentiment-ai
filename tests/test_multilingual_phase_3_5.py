import hashlib,json
from pathlib import Path
import pandas as pd
from scripts.run_multilingual_phase_3_5 import EXPECTED_HASH,validate_fixture
ROOT=Path(__file__).parents[1]
def test_frozen_fixture_hash_and_distribution():
 frame,digest=validate_fixture();assert digest==EXPECTED_HASH and len(frame)==48
 assert frame[~frame.short_text].expected_language.value_counts().to_dict()=={'en':12,'pt':12,'it':12}
 assert frame[frame.short_text].expected_language.value_counts().to_dict()=={'es':3,'en':3,'pt':3,'it':3}
 assert frame.expected_sentiment.value_counts().to_dict()=={'Positivo':16,'Negativo':16,'Neutro':16}
def test_short_texts_are_at_most_four_tokens():
 frame,_=validate_fixture();assert all(len(text.split())<=4 for text in frame[frame.short_text].text)
def test_results_are_immediate_unique_and_secret_free_when_present():
 path=ROOT/'artifacts/experiments/multilingual_phase_3_5_results.jsonl'
 if not path.exists():return
 rows=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
 assert 1<=len(rows)<=48 and len({r['case_id'] for r in rows})==len(rows)
 assert all('finish_reason' in r and 'pacing_wait_ms' in r and 'timestamp' in r for r in rows)
 text=path.read_text(encoding='utf-8');assert 'CEREBRAS_API_KEY' not in text and 'Bearer ' not in text

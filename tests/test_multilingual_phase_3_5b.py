import json
from pathlib import Path
from scripts.run_multilingual_phase_3_5b import TEXTS
def test_operational_fixture_is_exactly_fifteen_non_short_requests():
 assert len(TEXTS)==15 and len(set(TEXTS))==15 and all(len(text.split())>4 for text in TEXTS)
def test_operational_artifacts_are_complete_and_secret_free_when_present():
 path=Path(__file__).parents[1]/'artifacts/experiments/multilingual_phase_3_5b_results.jsonl'
 if not path.exists():return
 rows=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
 assert len(rows)==15 and [r['position'] for r in rows]==list(range(1,16))
 assert all(r['safety_margin_seconds']==2 and 'recent_requests_before' in r for r in rows)
 text=path.read_text(encoding='utf-8');assert 'CEREBRAS_API_KEY' not in text and 'authorization' not in text.casefold()

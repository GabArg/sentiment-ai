from datetime import datetime,timezone
import json
from scripts.run_multilingual_phase_3_3b import TOKEN_LIMIT,clean_window_wait,failed_cases
from scripts.structured_multilingual_reviewer import StructuredMultilingualSentimentReviewer,response_schema
from tests.test_multilingual_phase_3_3 import client

def test_selects_exactly_five_failed_cases_without_successes():
 cases=failed_cases()
 assert [c['case_id'] for c in cases]==['en-neg-r','en-neg-s','en-neu-s','pt-neg-s','it-neu-s']
 assert all(not c['success'] for c in cases)
def test_contract_is_minimal_strict_and_token_limit_is_256():
 schema=response_schema('sentiment_only')
 assert TOKEN_LIMIT==256 and schema['required']==['sentiment'] and set(schema['properties'])=={'sentiment'} and schema['additionalProperties'] is False
 reviewer=StructuredMultilingualSentimentReviewer(client=client('{"sentiment":"Negativo"}'))
 assert reviewer.review('Terrible','sentiment_only',TOKEN_LIMIT).success
 assert reviewer._client.chat.completions.kwargs['max_completion_tokens']==256
def test_clean_window_wait_is_injectable_and_only_waits_remaining_time():
 now=datetime.now(timezone.utc).timestamp(); slept=[]
 cases=[{'completed_at':datetime.fromtimestamp(now-30,timezone.utc).isoformat()}]
 assert 30.9<clean_window_wait(cases,lambda:now,slept.append)<31.1 and len(slept)==1
def test_artifacts_are_complete_when_present():
 from scripts.run_multilingual_phase_3_3b import RESULTS
 if not RESULTS.exists(): return
 rows=[json.loads(line) for line in RESULTS.read_text(encoding='utf-8').splitlines()]
 assert 1<=len(rows)<=5 and len({r['case_id'] for r in rows})==len(rows)
 assert all(r['max_completion_tokens']==256 and 'finish_reason' in r for r in rows)
 assert 'CEREBRAS_API_KEY' not in RESULTS.read_text(encoding='utf-8')

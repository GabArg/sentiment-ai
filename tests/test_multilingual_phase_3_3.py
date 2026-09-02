import json
from pathlib import Path
from types import SimpleNamespace
import pandas as pd
from scripts.structured_multilingual_reviewer import StructuredMultilingualSentimentReviewer,response_schema
from src.external_requests import ExternalRequestCoordinator
from src.rate_pacer import RatePacer

ROOT=Path(__file__).parents[1]
class Completions:
 def __init__(self,raw): self.raw=raw; self.kwargs=None
 def create(self,**kwargs):
  self.kwargs=kwargs
  return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self.raw),finish_reason='stop')],usage=SimpleNamespace(prompt_tokens=10,completion_tokens=8,total_tokens=18))
def client(raw):
 c=SimpleNamespace(); c.chat=SimpleNamespace(); c.chat.completions=Completions(raw); return c

def test_fixture_is_balanced_and_bounded():
 df=pd.read_csv(ROOT/'tests/fixtures/multilingual_phase_3_3_benchmark.csv')
 assert len(df)==18
 assert df.language.value_counts().to_dict()=={'en':6,'pt':6,'it':6}
 assert df.expected_sentiment.value_counts().to_dict()=={'Positivo':6,'Negativo':6,'Neutro':6}
 assert df.contract_variant.value_counts().to_dict()=={'sentiment_rationale':9,'sentiment_only':9}
 assert all(len(str(x).split())<=4 for x in df[df.is_short].text)

def test_schemas_are_strict_and_confidence_free():
 for variant in ('sentiment_rationale','sentiment_only'):
  schema=response_schema(variant)
  assert schema['additionalProperties'] is False and 'confidence' not in schema['properties']
 assert response_schema('sentiment_rationale')['properties']['rationale']['maxLength']==120

def test_reviewer_uses_strict_schema_and_anonymizes():
 c=client('{"sentiment":"Neutro","rationale":"Descripción factual."}')
 result=StructuredMultilingualSentimentReviewer(client=c).review('Write me at a@b.com order 123456789','sentiment_rationale')
 assert result.success and result.finish_reason=='stop' and result.schema_valid
 kwargs=c.chat.completions.kwargs
 assert kwargs['response_format']['json_schema']['strict'] is True and kwargs['max_completion_tokens']==192
 prompt=kwargs['messages'][0]['content']; assert 'a@b.com' not in prompt and '123456789' not in prompt

def test_reviewer_accepts_experimental_token_override():
 c=client('{"sentiment":"Neutro"}')
 assert StructuredMultilingualSentimentReviewer(client=c).review('Fact','sentiment_only',256).success
 assert c.chat.completions.kwargs['max_completion_tokens']==256

def test_reviewer_rejects_extra_field_and_invalid_json():
 assert StructuredMultilingualSentimentReviewer(client=client('{"sentiment":"Neutro","extra":1}')).review('Fact','sentiment_only').error_code=='invalid_schema'
 assert StructuredMultilingualSentimentReviewer(client=client('{"sentiment":')).review('Fact','sentiment_only').error_code=='invalid_json'

def test_experiment_uses_supported_shared_coordinator_kind():
 coordinator=ExternalRequestCoordinator(1,RatePacer(5,60,sleeper=lambda _:None,clock=lambda:0))
 assert coordinator.acquire('sentiment_review') and coordinator.calls['sentiment_review']==1

def test_versioned_results_when_present_are_secret_free():
 path=ROOT/'artifacts/experiments/multilingual_phase_3_3_results.jsonl'
 if not path.exists(): return
 rows=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
 assert 1<=len(rows)<=18 and len({row['case_id'] for row in rows})==len(rows)
 assert all('finish_reason' in row for row in rows)
 text=path.read_text(encoding='utf-8'); assert 'CEREBRAS_API_KEY' not in text and 'Bearer ' not in text

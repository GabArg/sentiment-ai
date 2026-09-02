from types import SimpleNamespace
import pytest
from src.structured_sentiment_review import SCHEMA,StructuredSentimentReviewProvider
class Factory:
 def __init__(self,content='{"sentiment":"Neutro"}',finish='stop',error=None):self.content=content;self.finish=finish;self.error=error;self.kwargs=None
 def __call__(self,**_):return self
 @property
 def chat(self):return SimpleNamespace(completions=self)
 def create(self,**kwargs):
  self.kwargs=kwargs
  if self.error:raise self.error
  return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self.content),finish_reason=self.finish)],usage=SimpleNamespace(prompt_tokens=10,completion_tokens=20,total_tokens=30))
def test_provider_contract_token_limit_usage_and_privacy():
 f=Factory();r=StructuredSentimentReviewProvider('x',client_factory=f).review_sentiment('mail a@b.com id 123456789')
 assert r.success and r.sentiment=='Neutro' and r.usage['total_tokens']==30
 assert f.kwargs['max_completion_tokens']==256 and f.kwargs['response_format']['json_schema']['strict'] is True
 assert SCHEMA['additionalProperties'] is False and 'a@b.com' not in f.kwargs['messages'][0]['content'] and '123456789' not in f.kwargs['messages'][0]['content']
@pytest.mark.parametrize(('content','finish','error'), [('{}','stop','invalid_schema'),('{"sentiment":"Otro"}','stop','invalid_sentiment'),('{','stop','invalid_json'),('', 'length','completion_truncated')])
def test_provider_structured_failures(content,finish,error):
 assert StructuredSentimentReviewProvider('x',client_factory=Factory(content,finish)).review_sentiment('text').error_code==error
def test_provider_no_key_timeout_and_429(monkeypatch):
 monkeypatch.delenv('CEREBRAS_API_KEY',raising=False)
 assert StructuredSentimentReviewProvider().review_sentiment('x').error_code=='unavailable'
 assert StructuredSentimentReviewProvider('x',client_factory=Factory(error=TimeoutError())).review_sentiment('x').error_code=='timeout'
 exc=RuntimeError();exc.status_code=429
 assert StructuredSentimentReviewProvider('x',client_factory=Factory(error=exc)).review_sentiment('x').error_code=='rate_limited'

def test_429_exposes_only_safe_observability_headers():
 exc=RuntimeError();exc.status_code=429
 exc.response=SimpleNamespace(headers={'Retry-After':'12','X-Request-Id':'req-1','Authorization':'secret'})
 result=StructuredSentimentReviewProvider('x',client_factory=Factory(error=exc)).review_sentiment('x')
 assert result.retry_after=='12' and result.request_id=='req-1'
 assert 'authorization' not in result.rate_limit_headers

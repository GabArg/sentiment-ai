"""Production-shaped strict provider for opt-in direct multilingual review."""
from __future__ import annotations
from dataclasses import dataclass
import json,time
from typing import Any,Callable
from src.ai_provider import DEFAULT_CEREBRAS_MODEL,resolve_api_key
from src.preprocessing import anonymize_text

SENTIMENTS=('Negativo','Neutro','Positivo')
SCHEMA={'type':'object','additionalProperties':False,'properties':{'sentiment':{'type':'string','enum':list(SENTIMENTS)}},'required':['sentiment']}
PROMPT='''Clasifique el sentimiento del comentario, que puede estar en español, inglés, portugués o italiano. Use exactamente Negativo, Neutro o Positivo. Una descripción puramente factual es Neutro. Devuelva solamente el objeto JSON solicitado.\n\nCOMENTARIO ANONIMIZADO:\n{text}'''
@dataclass(frozen=True)
class StructuredReviewResult:
 sentiment:str|None; provider:str; model:str; success:bool; error_code:str|None=None
 finish_reason:str|None=None; latency_ms:float|None=None; usage:dict[str,int]|None=None
 retry_after:str|None=None; request_id:str|None=None; rate_limit_headers:dict[str,str]|None=None
class StructuredSentimentReviewProvider:
 def __init__(self,api_key=None,model=DEFAULT_CEREBRAS_MODEL,client_factory:Callable[...,Any]|None=None,timeout=30.0,max_retries=0):
  self.api_key=resolve_api_key(api_key);self.model=model;self.client_factory=client_factory;self.timeout=timeout;self.max_retries=max_retries
 def review_sentiment(self,text):
  started=time.perf_counter()
  if not self.api_key:return self._failure('unavailable',started)
  try:
   factory=self.client_factory
   if factory is None:
    from cerebras.cloud.sdk import Cerebras
    factory=Cerebras
   client=factory(api_key=self.api_key,timeout=self.timeout,max_retries=self.max_retries)
   response=client.chat.completions.create(model=self.model,messages=[{'role':'user','content':PROMPT.format(text=anonymize_text(text))}],temperature=0,max_completion_tokens=256,response_format={'type':'json_schema','json_schema':{'name':'direct_multilingual_sentiment','strict':True,'schema':SCHEMA}})
   choice=response.choices[0];finish=getattr(choice,'finish_reason',None)
   if finish=='length':return self._failure('completion_truncated',started,finish,_usage(response))
   raw=choice.message.content
   try: payload=json.loads(raw)
   except (json.JSONDecodeError,TypeError):return self._failure('invalid_json',started,finish,_usage(response))
   if not isinstance(payload,dict) or set(payload)!={'sentiment'}:return self._failure('invalid_schema',started,finish,_usage(response))
   if payload['sentiment'] not in SENTIMENTS:return self._failure('invalid_sentiment',started,finish,_usage(response))
   return StructuredReviewResult(payload['sentiment'],'cerebras',self.model,True,finish_reason=finish,latency_ms=(time.perf_counter()-started)*1000,usage=_usage(response))
  except TimeoutError:return self._failure('timeout',started)
  except Exception as exc:
   code='rate_limited' if getattr(exc,'status_code',None)==429 else 'timeout' if type(exc).__name__=='APITimeoutError' else 'provider_error'
   headers=getattr(getattr(exc,'response',None),'headers',{}) or {}
   safe={str(k).lower():str(v) for k,v in headers.items() if str(k).lower() in {'retry-after','x-request-id','x-ratelimit-remaining-tokens-minute','x-ratelimit-reset-tokens-minute','x-ratelimit-remaining-requests-day','x-ratelimit-reset-requests-day'}}
   failed=self._failure(code,started)
   return StructuredReviewResult(failed.sentiment,failed.provider,failed.model,failed.success,failed.error_code,failed.finish_reason,failed.latency_ms,failed.usage,safe.get('retry-after'),safe.get('x-request-id'),safe or None)
 def _failure(self,code,started,finish=None,usage=None):return StructuredReviewResult(None,'cerebras',self.model,False,code,finish,(time.perf_counter()-started)*1000,usage)
def _usage(response):
 usage=getattr(response,'usage',None); values={}
 for name in ('prompt_tokens','completion_tokens','total_tokens'):
  value=getattr(usage,name,None) if usage is not None else None
  if isinstance(value,int) and not isinstance(value,bool):values[name]=value
 return values or None

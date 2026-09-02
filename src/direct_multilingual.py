"""Routing and consolidation for one-call direct multilingual reviews."""
from __future__ import annotations
from dataclasses import dataclass
from src.external_requests import ExternalRequestCoordinator
from src.hybrid import HybridPrediction,evaluate_hybrid_observation,fallback_for_budget
from src.hybrid_config import HybridRoutingConfig
from src.model import SentimentPredictor
from src.multilingual_contracts import LanguageDetector
from src.review_router import ReviewDecision,route_prediction

@dataclass(frozen=True)
class DirectMultilingualResult:
 final_prediction:str; local_prediction:str; local_confidence:float; detected_language:str|None; language_name:str|None
 language_state:str; direct_review_requested:bool; direct_review_state:str; direct_review_provider:str|None=None
 direct_review_model:str|None=None; direct_review_latency_ms:float|None=None; direct_review_finish_reason:str|None=None
 direct_review_error_code:str|None=None; direct_review_usage:dict[str,int]|None=None; hybrid:HybridPrediction|None=None
 retry_after:str|None=None; request_id:str|None=None; rate_limit_headers:dict[str,str]|None=None
def token_count(text):return len(text.split())
def evaluate_direct_multilingual(text,predictor:SentimentPredictor,detector:LanguageDetector,provider,coordinator:ExternalRequestCoordinator|None=None,hybrid_config:HybridRoutingConfig|None=None,hybrid_provider=None):
 observation=predictor.observe_one(text); short=token_count(text)<=4
 detection=None if short else detector.detect(text)
 language_state='short_text_uncertain' if short else detection.status
 direct=short or bool(detection and detection.success and detection.supported and detection.detected_language in {'en','pt','it'})
 if not direct:
  config=hybrid_config or HybridRoutingConfig(enabled=False)
  decision=route_prediction(observation,config.router_config()) if config.enabled else ReviewDecision(False,(),observation.local_confidence,observation.prediction_margin,observation.local_prediction,observation.second_best_class)
  if decision.should_review and coordinator is not None and not coordinator.acquire('sentiment_review'): hybrid=fallback_for_budget(observation.local_prediction,observation.local_confidence,observation.prediction_margin,decision)
  else: hybrid=evaluate_hybrid_observation(text,observation,decision,hybrid_provider)
  return DirectMultilingualResult(hybrid.final_prediction,observation.local_prediction,observation.local_confidence,getattr(detection,'detected_language',None),getattr(detection,'language_name',None),language_state,False,'local_only',hybrid=hybrid)
 if provider is None or not bool(getattr(provider,'api_key',True)):
  return _fallback(observation,detection,language_state,'unavailable')
 if coordinator is not None and not coordinator.acquire('sentiment_review'):
  return _fallback(observation,detection,language_state,'external_budget_exceeded')
 result=provider.review_sentiment(text)
 if not result.success:return _fallback(observation,detection,language_state,result.error_code or 'provider_error',result)
 return DirectMultilingualResult(result.sentiment,observation.local_prediction,observation.local_confidence,getattr(detection,'detected_language',None),getattr(detection,'language_name',None),language_state,True,'direct_multilingual_review',result.provider,result.model,result.latency_ms,result.finish_reason,None,result.usage)
def _fallback(observation,detection,state,error,result=None):
 return DirectMultilingualResult(observation.local_prediction,observation.local_prediction,observation.local_confidence,getattr(detection,'detected_language',None),getattr(detection,'language_name',None),state,True,'direct_review_failed',getattr(result,'provider',None),getattr(result,'model',None),getattr(result,'latency_ms',None),getattr(result,'finish_reason',None),error,getattr(result,'usage',None),None,getattr(result,'retry_after',None),getattr(result,'request_id',None),getattr(result,'rate_limit_headers',None))

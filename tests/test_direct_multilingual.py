from types import SimpleNamespace
import pandas as pd
import pytest
from src.batch import analyze_dataframe_direct_multilingual
from src.direct_multilingual import evaluate_direct_multilingual
from src.direct_review_config import load_direct_review_config
from src.external_requests import ExternalRequestCoordinator
from src.language_detection import LocalLanguageDetector
from src.rate_pacer import RatePacer
from src.structured_sentiment_review import StructuredSentimentReviewProvider

class Provider:
 api_key='x'
 def __init__(self,success=True,error=None):self.received=[];self.success=success;self.error=error
 def review_sentiment(self,text):
  self.received.append(text);return SimpleNamespace(sentiment='Neutro' if self.success else None,provider='mock',model='v1',success=self.success,error_code=self.error,latency_ms=5,finish_reason='stop',usage={'total_tokens':10})
def coordinator(limit=25):return ExternalRequestCoordinator(limit,RatePacer(5,60,sleeper=lambda _:None))
def test_flag_default_off_and_independent():
 assert not load_direct_review_config({},{}).enabled
 assert load_direct_review_config({}, {'ENABLE_DIRECT_MULTILINGUAL_REVIEW':'true','ENABLE_MULTILINGUAL_SENTIMENT':'false','ENABLE_HYBRID_SENTIMENT':'false'}).enabled
@pytest.mark.parametrize('text', ['The order arrived on Tuesday afternoon.','O pedido chegou na terça-feira à tarde.','Il pacco è arrivato martedì pomeriggio.'])
def test_supported_non_spanish_long_routes_direct(text,predictor):
 p=Provider();r=evaluate_direct_multilingual(text,predictor,LocalLanguageDetector(),p,coordinator())
 assert r.direct_review_state=='direct_multilingual_review' and r.final_prediction=='Neutro' and p.received==[text]
def test_spanish_long_remains_local(predictor):
 p=Provider();r=evaluate_direct_multilingual('La compra fue realizada durante la mañana del lunes.',predictor,LocalLanguageDetector(),p,coordinator())
 assert not r.direct_review_requested and r.direct_review_state=='local_only' and not p.received
def test_short_text_skips_detector_and_routes_direct(predictor):
 class Exploding:
  def detect(self,_):raise AssertionError
 r=evaluate_direct_multilingual('Not bad.',predictor,Exploding(),Provider(),coordinator())
 assert r.language_state=='short_text_uncertain' and r.direct_review_requested
def test_unsupported_and_detection_error_stay_local(predictor):
 assert not evaluate_direct_multilingual('Die Lieferung kam am Dienstag an.',predictor,LocalLanguageDetector(),Provider(),coordinator()).direct_review_requested
 class Failed:
  def detect(self,_):return SimpleNamespace(success=False,supported=False,status='error',detected_language=None,language_name=None)
 assert not evaluate_direct_multilingual('long enough text for detection failure',predictor,Failed(),Provider(),coordinator()).direct_review_requested
def test_failure_and_budget_fallback_local(predictor):
 failed=evaluate_direct_multilingual('The order arrived on Tuesday afternoon.',predictor,LocalLanguageDetector(),Provider(False,'timeout'),coordinator())
 assert failed.direct_review_state=='direct_review_failed' and failed.direct_review_error_code=='timeout' and failed.final_prediction==failed.local_prediction
 exhausted=coordinator(1);exhausted.acquire('translation')
 budget=evaluate_direct_multilingual('The order arrived on Tuesday afternoon.',predictor,LocalLanguageDetector(),Provider(),exhausted)
 assert budget.direct_review_error_code=='external_budget_exceeded'
def test_batch_preserves_order_columns_and_shared_budget(predictor):
 frame=pd.DataFrame({'comment':['The order arrived on Tuesday afternoon.','Not bad.'],'region':['a','b']});p=Provider();c=coordinator(1)
 result,dropped,summary=analyze_dataframe_direct_multilingual(frame,'comment',predictor,LocalLanguageDetector(),p,c)
 assert dropped==0 and result.region.tolist()==['a','b'] and len(p.received)==1 and summary['external_calls_used']==1
 assert result.direct_review_state.tolist()==['direct_multilingual_review','direct_review_failed']
 assert 'anonymized_original' not in result and 'raw_response' not in result

def test_controlled_preview_fixture_has_exact_scope():
 from pathlib import Path
 frame=pd.read_csv(Path(__file__).parent/'fixtures/multilingual_phase_3_4_preview.csv')
 assert len(frame)==8 and frame.language.value_counts().to_dict()=={'en':3,'pt':2,'it':2,'es':1}
 assert frame.is_short.sum()==2 and set(frame.expected_sentiment)=={'Positivo','Negativo','Neutro'}

def test_controlled_preview_artifacts_are_complete_and_secret_free():
 import json
 from pathlib import Path
 path=Path(__file__).parents[1]/'artifacts/experiments/multilingual_phase_3_4_preview_results.jsonl'
 if not path.exists():return
 rows=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
 assert len(rows)==8 and all(r['direct_review_state']=='direct_multilingual_review' for r in rows)
 text=path.read_text(encoding='utf-8');assert 'CEREBRAS_API_KEY' not in text and 'Bearer ' not in text

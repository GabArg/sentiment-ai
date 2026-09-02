"""Eight-call controlled real QA for the opt-in direct runtime route."""
from __future__ import annotations
import csv,json,statistics,time
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import pandas as pd
from src.direct_multilingual import evaluate_direct_multilingual
from src.external_requests import ExternalRequestCoordinator
from src.language_detection import LocalLanguageDetector
from src.model import SentimentPredictor
from src.rate_pacer import RatePacer
from src.structured_sentiment_review import StructuredSentimentReviewProvider
ROOT=Path(__file__).resolve().parents[1];FIXTURE=ROOT/'tests/fixtures/multilingual_phase_3_4_preview.csv';ART=ROOT/'artifacts/experiments'
RESULTS=ART/'multilingual_phase_3_4_preview_results.jsonl';SUMMARY=ART/'multilingual_phase_3_4_preview_summary.json';COSTS=ART/'multilingual_phase_3_4_preview_costs.csv'
INPUT=.00000035;OUTPUT=.00000075;FIELDS=('case_id','input_tokens','output_tokens','total_tokens','cost_usd','latency_ms','pacing_wait_seconds','success','error_code','finish_reason','started_at','completed_at')
def now():return datetime.now(timezone.utc).isoformat()
def run():
 if RESULTS.exists() or COSTS.exists():raise RuntimeError('Preview artifacts exist; refusing repeat.')
 cases=pd.read_csv(FIXTURE);predictor=SentimentPredictor.load();provider=StructuredSentimentReviewProvider(max_retries=0);waits=[];coordinator=ExternalRequestCoordinator(8,RatePacer(5,60,.25),waits.append);records=[];wall=time.perf_counter()
 for case in cases.itertuples(index=False):
  before=sum(waits);started=now();result=evaluate_direct_multilingual(case.text,predictor,LocalLanguageDetector(),provider,coordinator);completed=now();wait=sum(waits)-before
  usage=result.direct_review_usage or {};inp=usage.get('prompt_tokens');out=usage.get('completion_tokens');total=usage.get('total_tokens');cost=(inp or 0)*INPUT+(out or 0)*OUTPUT if inp is not None or out is not None else None
  row={'case_id':case.case_id,'language':case.language,'expected_sentiment':case.expected_sentiment,'original_text':case.text,'is_short':bool(case.is_short),'detected_language':result.detected_language,'language_state':result.language_state,'sentiment':result.final_prediction,'direct_review_state':result.direct_review_state,'provider':result.direct_review_provider,'model':result.direct_review_model,'finish_reason':result.direct_review_finish_reason,'error_code':result.direct_review_error_code,'input_tokens':inp,'output_tokens':out,'total_tokens':total,'cost_usd':cost,'latency_ms':result.direct_review_latency_ms,'pacing_wait_seconds':wait,'started_at':started,'completed_at':completed}
  with RESULTS.open('a',encoding='utf-8') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n');f.flush()
  exists=COSTS.exists() and COSTS.stat().st_size
  with COSTS.open('a',encoding='utf-8',newline='') as f:
   w=csv.DictWriter(f,fieldnames=FIELDS)
   if not exists:w.writeheader()
   w.writerow({k:row.get(k) for k in FIELDS});f.flush()
  records.append(row)
  if result.direct_review_state!='direct_multilingual_review':break
 summary=build(records,time.perf_counter()-wall);SUMMARY.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:summary[k] for k in ('requests','valid','accuracy','truncations','errors')}));return summary
def build(rows,elapsed):
 accuracy=lambda items:sum(r['sentiment']==r['expected_sentiment'] for r in items)/len(items)
 group=lambda key:{str(v):accuracy([r for r in rows if r[key]==v]) for v in sorted({r[key] for r in rows})};lat=[r['latency_ms'] for r in rows if r['latency_ms'] is not None];cost=sum(r['cost_usd'] or 0 for r in rows)
 return {'requests':len(rows),'valid':sum(r['direct_review_state']=='direct_multilingual_review' for r in rows),'accuracy':accuracy(rows),'accuracy_by_language':group('language'),'accuracy_by_class':group('expected_sentiment'),'short_text_accuracy':accuracy([r for r in rows if r['is_short']]),'finish_reason':dict(Counter(r['finish_reason'] or 'none' for r in rows)),'truncations':sum(r['finish_reason']=='length' for r in rows),'errors':dict(Counter(r['error_code'] for r in rows if r['error_code'])),'calls_per_comment':len(rows)/len(rows),'tokens':{'input':sum(r['input_tokens'] or 0 for r in rows),'output':sum(r['output_tokens'] or 0 for r in rows),'total':sum(r['total_tokens'] or 0 for r in rows)},'cost_usd':cost,'cost_per_comment_usd':cost/len(rows),'latency_ms':{'min':min(lat),'median':statistics.median(lat),'max':max(lat)},'pacing_wait_seconds':sum(r['pacing_wait_seconds'] for r in rows),'elapsed_seconds':elapsed,'fallbacks':sum(r['direct_review_state']!='direct_multilingual_review' for r in rows)}
if __name__=='__main__':run()

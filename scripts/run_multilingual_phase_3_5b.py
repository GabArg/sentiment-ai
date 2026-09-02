"""Fifteen-request operational validation of hardened rolling-window pacing."""
from __future__ import annotations
import csv,json,statistics,time
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from src.direct_multilingual import evaluate_direct_multilingual
from src.external_requests import ExternalRequestCoordinator
from src.language_detection import LocalLanguageDetector
from src.model import SentimentPredictor
from src.rate_pacer import RatePacer
from src.structured_sentiment_review import StructuredSentimentReviewProvider
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'artifacts/experiments';RESULTS=ART/'multilingual_phase_3_5b_results.jsonl';SUMMARY=ART/'multilingual_phase_3_5b_summary.json';COSTS=ART/'multilingual_phase_3_5b_costs.csv'
TEXTS=[f'The order number {number} was registered at the warehouse this morning.' for number in range(1,16)]
FIELDS=('position','input_tokens','output_tokens','total_tokens','cost_usd','latency_ms','pacing_wait_seconds','state','error_code','finish_reason','timestamp');INPUT=.00000035;OUTPUT=.00000075
def run():
 if RESULTS.exists() or COSTS.exists():raise RuntimeError('Phase 3.5B artifacts exist; refusing repeat.')
 waits=[];pacer=RatePacer(5,60,2);coordinator=ExternalRequestCoordinator(15,pacer,waits.append);provider=StructuredSentimentReviewProvider(max_retries=0);predictor=SentimentPredictor.load();rows=[];wall=time.perf_counter()
 for position,text in enumerate(TEXTS,1):
  recent_before=len(pacer._timestamps);before=sum(waits);started=datetime.now(timezone.utc).isoformat();result=evaluate_direct_multilingual(text,predictor,LocalLanguageDetector(),provider,coordinator);wait=sum(waits)-before
  usage=result.direct_review_usage or {};inp=usage.get('prompt_tokens');out=usage.get('completion_tokens');total=usage.get('total_tokens');cost=(inp or 0)*INPUT+(out or 0)*OUTPUT if inp is not None or out is not None else None
  row={'position':position,'start_timestamp':started,'timestamp':datetime.now(timezone.utc).isoformat(),'pacing_wait_seconds':wait,'recent_requests_before':recent_before,'safety_margin_seconds':pacer.margin_seconds,'state':result.direct_review_state,'finish_reason':result.direct_review_finish_reason,'error_code':result.direct_review_error_code,'retry_after':result.retry_after,'request_id':result.request_id,'rate_limit_headers':result.rate_limit_headers,'latency_ms':result.direct_review_latency_ms,'input_tokens':inp,'output_tokens':out,'total_tokens':total,'cost_usd':cost}
  with RESULTS.open('a',encoding='utf-8') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n');f.flush()
  exists=COSTS.exists() and COSTS.stat().st_size
  with COSTS.open('a',encoding='utf-8',newline='') as f:
   w=csv.DictWriter(f,fieldnames=FIELDS)
   if not exists:w.writeheader()
   w.writerow({key:row.get(key) for key in FIELDS});f.flush()
  rows.append(row)
 summary=build(rows,time.perf_counter()-wall);SUMMARY.write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps({k:summary[k] for k in ('requests','provider_success','http_429','truncations','gate_pass')}));return summary
def build(rows,elapsed):
 success=sum(r['state']=='direct_multilingual_review' for r in rows);lat=[r['latency_ms'] for r in rows if r['latency_ms'] is not None];cost=sum(r['cost_usd'] or 0 for r in rows)
 return {'requests':len(rows),'provider_success':success,'http_429':sum(r['error_code']=='rate_limited' for r in rows),'truncations':sum(r['error_code']=='completion_truncated' for r in rows),'schema_errors':sum(r['error_code'] in {'invalid_json','invalid_schema','invalid_sentiment'} for r in rows),'finish_reason':dict(Counter(r['finish_reason'] or 'none' for r in rows)),'pacing_wait_seconds':sum(r['pacing_wait_seconds'] for r in rows),'wall_clock_seconds':elapsed,'latency_ms':{'min':min(lat),'median':statistics.median(lat),'max':max(lat)},'tokens':{'input':sum(r['input_tokens'] or 0 for r in rows),'output':sum(r['output_tokens'] or 0 for r in rows),'total':sum(r['total_tokens'] or 0 for r in rows)},'cost_usd':cost,'cost_per_comment_usd':cost/len(rows),'safety_margin_seconds':2.0,'max_requests':5,'effective_window_seconds':62.0,'concurrent':False,'gate_pass':len(rows)==15 and success==15 and all(not r['error_code'] for r in rows)}
if __name__=='__main__':run()

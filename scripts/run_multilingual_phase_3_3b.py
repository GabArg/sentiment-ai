"""Recover only the five failed Phase 3.3 cases with the minimal 256-token contract."""
from __future__ import annotations
import csv, json, statistics, time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from src.external_requests import ExternalRequestCoordinator
from src.rate_pacer import RatePacer
from scripts.structured_multilingual_reviewer import StructuredMultilingualSentimentReviewer

ROOT=Path(__file__).resolve().parents[1]; ART=ROOT/'artifacts/experiments'
PREVIOUS=ART/'multilingual_phase_3_3_results.jsonl'
RESULTS=ART/'multilingual_phase_3_3b_results.jsonl'; SUMMARY=ART/'multilingual_phase_3_3b_summary.json'; COSTS=ART/'multilingual_phase_3_3b_costs.csv'
MAX_CALLS=5; TOKEN_LIMIT=256; INPUT_COST=.00000035; OUTPUT_COST=.00000075
FIELDS=('case_id','input_tokens','output_tokens','total_tokens','cost_usd','latency_ms','pacing_wait_seconds','success','error_code','finish_reason','retry_after','started_at','completed_at')

def _now(): return datetime.now(timezone.utc).isoformat()
def _append_json(row):
 with RESULTS.open('a',encoding='utf-8',newline='') as f: f.write(json.dumps(row,ensure_ascii=False)+'\n'); f.flush()
def _append_cost(row):
 exists=COSTS.exists() and COSTS.stat().st_size
 with COSTS.open('a',encoding='utf-8',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=FIELDS)
  if not exists: writer.writeheader()
  writer.writerow({key:row.get(key) for key in FIELDS}); f.flush()
def failed_cases():
 rows=[json.loads(line) for line in PREVIOUS.read_text(encoding='utf-8').splitlines()]
 failed=[row for row in rows if not row['success']]
 if len(rows)!=18 or len(failed)!=5 or len({r['case_id'] for r in failed})!=5: raise RuntimeError('Unexpected Phase 3.3 source artifacts.')
 return failed
def clean_window_wait(cases,clock=time.time,sleeper=time.sleep):
 latest=max(datetime.fromisoformat(row['completed_at']).timestamp() for row in cases)
 wait=max(0.0,61.0-(clock()-latest))
 if wait: sleeper(wait)
 return wait
def run():
 if RESULTS.exists() or COSTS.exists(): raise RuntimeError('Phase 3.3B artifacts exist; refusing to repeat calls.')
 cases=failed_cases(); initial_wait=clean_window_wait(cases)
 waits=[]; coordinator=ExternalRequestCoordinator(MAX_CALLS,RatePacer(5,60,.25),waits.append)
 reviewer=StructuredMultilingualSentimentReviewer(max_retries=0); records=[]; wall=time.perf_counter()
 for position,case in enumerate(cases,1):
  before=sum(waits); coordinator.acquire('sentiment_review'); pacing=sum(waits)-before
  started=_now(); result=reviewer.review(case['original_text'],'sentiment_only',TOKEN_LIMIT); completed=_now()
  usage=result.usage or {}; inp=usage.get('prompt_tokens'); out=usage.get('completion_tokens'); total=usage.get('total_tokens')
  cost=(inp or 0)*INPUT_COST+(out or 0)*OUTPUT_COST if inp is not None or out is not None else None
  row={'case_id':case['case_id'],'position':position,'language':case['language'],'expected_sentiment':case['expected_sentiment'],
   'original_text':case['original_text'],'anonymized_original':case['anonymized_original'],'contract_variant':'sentiment_only',
   'max_completion_tokens':TOKEN_LIMIT,'sentiment':result.sentiment,'raw_response':result.raw_response,'parsed_result':result.sentiment,
   'success':result.success,'schema_valid':result.schema_valid,'parse_status':result.parse_status,'error_code':result.error_code,
   'finish_reason':result.finish_reason,'retry_after':result.retry_after,'input_tokens':inp,'output_tokens':out,'total_tokens':total,
   'cost_usd':cost,'latency_ms':result.latency_ms,'pacing_wait_seconds':pacing,'requests_in_window_before':position-1,
   'started_at':started,'completed_at':completed}
  _append_json(row); _append_cost(row); records.append(row)
  if not result.success: break
 summary=build_summary(records,initial_wait,time.perf_counter()-wall)
 SUMMARY.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:summary[k] for k in ('requests','valid_responses','truncations','errors','accuracy','promotion_gate')}))
 return summary
def build_summary(records,initial_wait,elapsed):
 valid=[r for r in records if r['success']]; latency=[r['latency_ms'] for r in records]; costs=sum(r['cost_usd'] or 0 for r in records)
 gate=len(records)==5 and all(r['success'] and r['sentiment']==r['expected_sentiment'] and r['finish_reason']!='length' for r in records)
 previous=[json.loads(line) for line in PREVIOUS.read_text(encoding='utf-8').splitlines()]
 return {'requests':len(records),'valid_responses':len(valid),'finish_reason':dict(Counter(r['finish_reason'] or 'none' for r in records)),
  'truncations':sum(r['finish_reason']=='length' for r in records),'invalid_json':sum(r['parse_status']=='invalid_json' for r in records),
  'schema_violations':sum(r['parse_status']=='schema_violation' for r in records),'errors':dict(Counter(r['error_code'] for r in records if r['error_code'])),
  'accuracy':sum(r['success'] and r['sentiment']==r['expected_sentiment'] for r in records)/len(records),
  'tokens':{'input':sum(r['input_tokens'] or 0 for r in records),'output':sum(r['output_tokens'] or 0 for r in records),'total':sum(r['total_tokens'] or 0 for r in records)},
  'cost_usd':costs,'cost_per_comment_usd':costs/len(records),'latency_ms':{'min':min(latency),'median':statistics.median(latency),'max':max(latency)},
  'initial_clean_window_wait_seconds':initial_wait,'pacing_wait_seconds':sum(r['pacing_wait_seconds'] for r in records),'elapsed_seconds':elapsed,
  'promotion_gate':gate,'combined':{'historical_valid_3_3':sum(r['success'] for r in previous),'recovered_3_3b':sum(r['success'] and r['sentiment']==r['expected_sentiment'] for r in records),'correct':13+sum(r['success'] and r['sentiment']==r['expected_sentiment'] for r in records),'total':18,'single_continuous_run':False},
  'privacy':{'anonymized_before_request':True,'expected_sent':False,'local_prediction_sent':False,'metadata_sent':False}}
if __name__=='__main__': run()

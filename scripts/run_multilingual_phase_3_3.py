"""Run and immediately persist the bounded Phase 3.3 experiment."""
from __future__ import annotations
import csv, json, statistics, time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
from src.external_requests import ExternalRequestCoordinator
from src.preprocessing import anonymize_text
from src.rate_pacer import RatePacer
from scripts.structured_multilingual_reviewer import StructuredMultilingualSentimentReviewer

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'tests/fixtures/multilingual_phase_3_3_benchmark.csv'
OUT=ROOT/'artifacts/experiments'
RESULTS=OUT/'multilingual_phase_3_3_results.jsonl'; SUMMARY=OUT/'multilingual_phase_3_3_summary.json'; COSTS=OUT/'multilingual_phase_3_3_costs.csv'
INPUT_COST=.00000035; OUTPUT_COST=.00000075; MAX_CALLS=18
COST_FIELDS=('case_id','language','contract_variant','input_tokens','output_tokens','total_tokens','cost_usd','latency_ms','pacing_wait_seconds','success','error_code','finish_reason','started_at','completed_at')

def now(): return datetime.now(timezone.utc).isoformat()
def percentile(values,p):
    ordered=sorted(values); pos=(len(ordered)-1)*p; lo=int(pos); hi=min(lo+1,len(ordered)-1)
    return ordered[lo]+(ordered[hi]-ordered[lo])*(pos-lo)
def append(path,payload):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a',encoding='utf-8',newline='') as f: f.write(json.dumps(payload,ensure_ascii=False)+'\n'); f.flush()
def append_cost(row):
    exists=COSTS.exists() and COSTS.stat().st_size
    with COSTS.open('a',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=COST_FIELDS)
        if not exists: w.writeheader()
        w.writerow(row); f.flush()

def run():
    cases=pd.read_csv(FIXTURE); reviewer=StructuredMultilingualSentimentReviewer(max_retries=0)
    records=[json.loads(line) for line in RESULTS.read_text(encoding='utf-8').splitlines()] if RESULTS.exists() else []
    completed={r['case_id'] for r in records}
    if len(records)>=MAX_CALLS: raise RuntimeError('Phase 3.3 call limit already reached.')
    waits=[]; coordinator=ExternalRequestCoordinator(MAX_CALLS-len(records),RatePacer(5,60,.25),waits.append)
    wall=time.perf_counter()
    for case in cases.itertuples(index=False):
        if case.case_id in completed: continue
        before=sum(waits); coordinator.acquire('sentiment_review'); wait=sum(waits)-before
        token_limit=256 if records else int(case.max_completion_tokens)
        started=now(); result=reviewer.review(case.text,case.contract_variant,token_limit); completed_at=now()
        usage=result.usage or {}; inp=usage.get('prompt_tokens'); out=usage.get('completion_tokens'); total=usage.get('total_tokens')
        cost=(inp or 0)*INPUT_COST+(out or 0)*OUTPUT_COST if inp is not None or out is not None else None
        record={'case_id':case.case_id,'language':case.language,'expected_sentiment':case.expected_sentiment,'original_text':case.text,
          'anonymized_original':anonymize_text(case.text),'case_type':case.case_type,'is_short':bool(case.is_short),
          'contract_variant':case.contract_variant,'max_completion_tokens':token_limit,'sentiment':result.sentiment,
          'rationale':result.rationale,'success':result.success,'error_code':result.error_code,'schema_valid':result.schema_valid,
          'parse_status':result.parse_status,'raw_response':result.raw_response,'finish_reason':result.finish_reason,
          'input_tokens':inp,'output_tokens':out,'total_tokens':total,'cost_usd':cost,'latency_ms':result.latency_ms,
          'pacing_wait_seconds':wait,'started_at':started,'completed_at':completed_at}
        append(RESULTS,record); append_cost({k:record.get(k) for k in COST_FIELDS}); records.append(record)
    summary=build_summary(records,time.perf_counter()-wall)
    SUMMARY.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:summary[k] for k in ('requests','valid_json','truncations','end_to_end_accuracy','total_cost_usd','elapsed_seconds')}))
    return summary

def build_summary(records,elapsed):
    valid=[r for r in records if r['success']]; lat=[r['latency_ms'] for r in records]; outs=[r['output_tokens'] for r in records if r['output_tokens'] is not None]
    accuracy=lambda rows: sum(r['success'] and r['sentiment']==r['expected_sentiment'] for r in rows)/len(rows)
    group=lambda key: {str(v):accuracy([r for r in records if r[key]==v]) for v in sorted({r[key] for r in records})}
    return {'requests':len(records),'valid_json':sum(r['parse_status']=='valid' for r in records),'invalid_json':sum(r['parse_status']=='invalid_json' for r in records),
      'schema_violations':sum(r['parse_status']=='schema_violation' for r in records),'truncations':sum(r['finish_reason']=='length' for r in records),
      'finish_reason':dict(Counter(r['finish_reason'] or 'none' for r in records)),'provider_errors':dict(Counter(r['error_code'] for r in records if r['error_code'])),
      'end_to_end_accuracy':accuracy(records),'valid_response_accuracy':sum(r['sentiment']==r['expected_sentiment'] for r in valid)/len(valid) if valid else None,
      'accuracy_by_language':group('language'),'accuracy_by_class':group('expected_sentiment'),
      'factual_neutral_accuracy':accuracy([r for r in records if 'factual_neutral' in r['case_type']]),'short_text_accuracy':accuracy([r for r in records if r['is_short']]),
      'tokens':{'input':sum(r['input_tokens'] or 0 for r in records),'output':sum(r['output_tokens'] or 0 for r in records),'total':sum(r['total_tokens'] or 0 for r in records),'mean_output':statistics.mean(outs),'max_output':max(outs)},
      'total_cost_usd':sum(r['cost_usd'] or 0 for r in records),'cost_per_comment_usd':sum(r['cost_usd'] or 0 for r in records)/len(records),'cost_per_100_usd':sum(r['cost_usd'] or 0 for r in records)/len(records)*100,
      'latency_ms':{'min':min(lat),'median':statistics.median(lat),'p95':percentile(lat,.95),'max':max(lat)},'pacing_wait_seconds':sum(r['pacing_wait_seconds'] for r in records),'elapsed_seconds':elapsed,
      'by_contract':{v:{'cases':len(g),'accuracy':accuracy(g),'mean_output_tokens':statistics.mean([r['output_tokens'] for r in g if r['output_tokens'] is not None]),'max_output_tokens':max(r['output_tokens'] for r in g if r['output_tokens'] is not None)} for v in sorted({r['contract_variant'] for r in records}) for g in [[r for r in records if r['contract_variant']==v]]},
      'privacy':{'anonymized_before_request':True,'expected_sent':False,'local_prediction_sent':False,'confidence_sent':False,'metadata_sent':False},
      'artifacts':{'results':str(RESULTS),'summary':str(SUMMARY),'costs':str(COSTS)}}
if __name__=='__main__': run()

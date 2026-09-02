"""Frozen 48-case validation gate exercising the Phase 3.4 production route."""
from __future__ import annotations
import csv,hashlib,json,statistics,time
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
ROOT=Path(__file__).resolve().parents[1];FIXTURE=ROOT/'tests/fixtures/multilingual_phase_3_5_validation.csv';ART=ROOT/'artifacts/experiments'
RESULTS=ART/'multilingual_phase_3_5_results.jsonl';SUMMARY=ART/'multilingual_phase_3_5_summary.json';COSTS=ART/'multilingual_phase_3_5_costs.csv';HASH=ART/'multilingual_phase_3_5_fixture.sha256'
EXPECTED_HASH='0310071e989f6f447ef697a77d2c9f9b1f7f9dc0ce95bdcc2d0e68e6fb01d417';INPUT=.00000035;OUTPUT=.00000075
COST_FIELDS=('case_id','input_tokens','output_tokens','total_tokens','cost_usd','latency_ms','pacing_wait_ms','state','error_code','finish_reason','timestamp')
def now():return datetime.now(timezone.utc).isoformat()
def validate_fixture():
 digest=hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
 if digest!=EXPECTED_HASH or not HASH.read_text().startswith(digest):raise RuntimeError('Frozen fixture hash mismatch.')
 frame=pd.read_csv(FIXTURE);long=frame[~frame.short_text];short=frame[frame.short_text]
 if len(frame)!=48 or long.expected_language.value_counts().to_dict()!={'en':12,'pt':12,'it':12} or short.expected_language.value_counts().to_dict()!={'es':3,'en':3,'pt':3,'it':3} or frame.expected_sentiment.value_counts().to_dict()!={'Positivo':16,'Negativo':16,'Neutro':16}:raise RuntimeError('Fixture distribution mismatch.')
 if any(len(text.split())>4 for text in short.text):raise RuntimeError('Short text exceeds four tokens.')
 return frame,digest
def append_result(row):
 with RESULTS.open('a',encoding='utf-8') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n');f.flush()
def append_cost(row):
 exists=COSTS.exists() and COSTS.stat().st_size
 with COSTS.open('a',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=COST_FIELDS)
  if not exists:w.writeheader()
  w.writerow({key:row.get(key) for key in COST_FIELDS});f.flush()
def resume_wait(records):
 if not records:return 0.0
 elapsed=time.time()-datetime.fromisoformat(records[-1]['timestamp']).timestamp();wait=max(0,61-elapsed)
 if wait:time.sleep(wait)
 return wait
def run():
 frame,digest=validate_fixture();records=[json.loads(line) for line in RESULTS.read_text(encoding='utf-8').splitlines()] if RESULTS.exists() else []
 done={r['case_id'] for r in records}
 if len(done)!=len(records) or len(records)>=48:raise RuntimeError('Results already complete or contain duplicate cases.')
 initial_wait=resume_wait(records);waits=[];coordinator=ExternalRequestCoordinator(48-len(records),RatePacer(5,60,.25),waits.append)
 predictor=SentimentPredictor.load();provider=StructuredSentimentReviewProvider(max_retries=0);started=time.perf_counter()
 for case in frame.itertuples(index=False):
  if case.case_id in done:continue
  before=sum(waits);result=evaluate_direct_multilingual(case.text,predictor,LocalLanguageDetector(),provider,coordinator);pacing=(sum(waits)-before)*1000
  usage=result.direct_review_usage or {};inp=usage.get('prompt_tokens');out=usage.get('completion_tokens');total=usage.get('total_tokens');cost=(inp or 0)*INPUT+(out or 0)*OUTPUT if inp is not None or out is not None else None
  row={'case_id':case.case_id,'expected_language':case.expected_language,'expected_sentiment':case.expected_sentiment,'text':case.text,'short_text':bool(case.short_text),'difficulty':case.difficulty,'detected_language':result.detected_language,'route':'direct_multilingual_review' if result.direct_review_requested else 'local','final_sentiment':result.final_prediction,'state':result.direct_review_state,'provider':result.direct_review_provider,'model':result.direct_review_model,'finish_reason':result.direct_review_finish_reason,'error_code':result.direct_review_error_code,'latency_ms':result.direct_review_latency_ms,'pacing_wait_ms':pacing,'input_tokens':inp,'output_tokens':out,'total_tokens':total,'cost_usd':cost,'timestamp':now(),'position':len(records)+1,'requests_in_window_before':(len(records))%5}
  append_result(row);append_cost(row);records.append(row)
 summary=build_summary(records,digest,initial_wait,time.perf_counter()-started);SUMMARY.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:summary[k] for k in ('requests','accuracy','provider_success','truncations','gate_pass')}));return summary
def pct(rows):return sum(r['final_sentiment']==r['expected_sentiment'] for r in rows)/len(rows) if rows else None
def build_summary(rows,digest,initial_wait,elapsed):
 by=lambda key:{str(value):pct([r for r in rows if r[key]==value]) for value in sorted({r[key] for r in rows})}
 short=[r for r in rows if r['short_text']];factual=[r for r in rows if r['difficulty']=='factual_neutral'];neg=[r for r in rows if r['difficulty']=='negation'];contrast=[r for r in rows if r['difficulty']=='contrast'];errors=[{k:r[k] for k in ('case_id','text','expected_language','expected_sentiment','final_sentiment','difficulty')} for r in rows if r['final_sentiment']!=r['expected_sentiment']]
 valid=sum(r['state']=='direct_multilingual_review' for r in rows);trunc=sum(r['error_code']=='completion_truncated' or r['finish_reason']=='length' for r in rows);schema=sum(r['error_code'] in {'invalid_json','invalid_schema','invalid_sentiment'} for r in rows);acc=pct(rows);long=[r for r in rows if not r['short_text']];languages={language:pct([r for r in long if r['expected_language']==language]) for language in ('en','pt','it')};neutral=pct([r for r in rows if r['expected_sentiment']=='Neutro']);success=valid/len(rows);gate=len(rows)==48 and acc>=.95 and all(languages.get(x,0)>=.90 for x in ('en','pt','it')) and pct(short)>=.85 and neutral>=.90 and trunc==0 and schema==0 and success>=.98
 lat=[r['latency_ms'] for r in rows if r['latency_ms'] is not None];ordered=sorted(lat);p95=ordered[int(.95*(len(ordered)-1))];cost=sum(r['cost_usd'] or 0 for r in rows)
 return {'fixture_sha256':digest,'requests':len(rows),'accuracy':acc,'accuracy_by_language':languages,'accuracy_by_class':by('expected_sentiment'),'neutral_accuracy':neutral,'factual_neutral_accuracy':pct(factual),'negation_accuracy':pct(neg),'contrast_accuracy':pct(contrast),'short_text_accuracy':pct(short),'classification_errors':errors,'valid_structured_outputs':valid,'provider_success':success,'fallbacks':len(rows)-valid,'truncations':trunc,'schema_errors':schema,'provider_errors':dict(Counter(r['error_code'] for r in rows if r['error_code'])),'finish_reason':dict(Counter(r['finish_reason'] or 'none' for r in rows)),'tokens':{'input':sum(r['input_tokens'] or 0 for r in rows),'output':sum(r['output_tokens'] or 0 for r in rows),'total':sum(r['total_tokens'] or 0 for r in rows),'average_total':sum(r['total_tokens'] or 0 for r in rows)/len(rows)},'cost_usd':cost,'cost_per_comment_usd':cost/len(rows),'cost_100_usd':cost/len(rows)*100,'cost_1000_usd':cost/len(rows)*1000,'latency_ms':{'min':min(lat),'median':statistics.median(lat),'p95':p95,'max':max(lat)},'initial_resume_wait_seconds':initial_wait,'pacing_wait_seconds':sum(r['pacing_wait_ms'] for r in rows)/1000,'elapsed_seconds_current_process':elapsed,'estimated_100_comments_at_5rpm_seconds':1200,'gate_pass':gate,'privacy':{'anonymized_in_productive_provider':True,'expected_sent':False,'local_prediction_sent':False,'metadata_sent':False}}
if __name__=='__main__':run()

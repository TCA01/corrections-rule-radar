"""Measured unattended sync entry point; no commit or deployment here."""
import argparse
import json
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.law_api import ApiError
from pipeline.operations import now
from pipeline.operations.metrics import Metrics
from pipeline.snapshot import write_json
from scripts.collect_core import run as collect_core
from scripts.discovery_scan import run as discover
from scripts.sync import sync,read,ROOT
from scripts.observe import public_fingerprint,semantic_hashes
from pipeline.law_api.comparisons import prepare

def run(*,discovery=False,full_audit=False):
    at=now(); start=time.monotonic(); metrics=Metrics(); previous=read('data/ops/health.json',{})
    before=public_fingerprint(ROOT); previous_state=read('data/registry/state.json',{}); previous_events=read('data/registry/events.json',[])
    write_json(ROOT/'data/reports/production_sync.json',{'result':'RUNNING','started_at':at,'last_good_dataset_version':previous.get('last_dataset_version')})
    collection=None; error=None
    try:
        collection=discover(metrics=metrics,full_audit=full_audit) if discovery or full_audit else None
        collection=collection or collect_core(metrics=metrics,quiet=True)
        prepare(collection,previous_state,read('data/registry/change_history.json',[]),metrics=metrics)
        result=sync(collection)
        if result['result']=='BLOCKED': error=result.get('reason','INCOMPLETE_COLLECTION')
    except Exception as exc:
        error=exc.code if isinstance(exc,ApiError) else 'SYNC_FAILED'
        result={'result':'BLOCKED','new_events':0,'public_rewritten':False,'dataset_version':previous.get('last_dataset_version')}
    ops=read('data/ops/health.json',previous)
    if error:
        ops.update({'last_successful_sync':previous.get('last_successful_sync'),'last_dataset_version':previous.get('last_dataset_version'),'publication_status':'BLOCKED','api_status':error})
    counts={'success_count':len(collection['registry']) if collection else 0,'review_count':sum(r['status']!='RESOLVED' for r in collection['resolution']) if collection else len(read('data/registry/rules.json',[]))}
    counts['failure_count']=counts['review_count']
    report={**result,'started_at':at,'finished_at':now(),'duration_seconds':round(time.monotonic()-start,6),**metrics.report(),**counts,'error_summary':{'code':error} if error else {},'mode':'WEEKLY_FULL_AUDIT' if full_audit else 'CORE_WITH_DAILY_DISCOVERY' if discovery else 'CORE_STABLE_IDS','last_good_dataset_version':ops.get('last_dataset_version')}
    report.update({'public_bytes_and_mtimes_identical':before==public_fingerprint(ROOT),'snapshot_hashes_identical':semantic_hashes(previous_state)==semantic_hashes(read('data/registry/state.json',{})),'event_ids_identical':[e['event_id'] for e in previous_events]==[e['event_id'] for e in read('data/registry/events.json',[])]})
    ops.update({'last_attempt':at,'duration_seconds':report['duration_seconds'],**metrics.report(),**counts})
    write_json(ROOT/'data/ops/health.json',ops); write_json(ROOT/'data/reports/production_sync.json',report)
    write_json(ROOT/'data/reports/production'/(at[:19].replace(':','').replace('-','')+'.json'),report)
    return report
def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--discovery',action='store_true'); parser.add_argument('--full-audit',action='store_true'); args=parser.parse_args()
    report=run(discovery=args.discovery,full_audit=args.full_audit); print(json.dumps(report,ensure_ascii=False)); return int(report['result']=='BLOCKED')
if __name__=='__main__': sys.exit(main())

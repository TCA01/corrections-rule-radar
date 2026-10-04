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
from pipeline.law_api.revalidation import revalidate

def run(*,discovery=False,full_audit=False,approved_expansion=False,approved_phase1g=False):
    at=now(); start=time.monotonic(); metrics=Metrics(); previous=read('data/ops/health.json',{})
    before=public_fingerprint(ROOT); previous_state=read('data/registry/state.json',{}); previous_events=read('data/registry/events.json',[])
    write_json(ROOT/'data/reports/production_sync.json',{'result':'RUNNING','started_at':at,'last_good_dataset_version':previous.get('last_dataset_version')})
    collection=None; error=None
    try:
        discovery_error=None
        if discovery or full_audit:
            print(f"[production_sync] running discovery (full_audit={full_audit})...", file=sys.stderr, flush=True)
            try: discover(metrics=metrics,full_audit=full_audit)
            except Exception as e:
                discovery_error='DISCOVERY_MONITOR_UNAVAILABLE'
                print(f"[production_sync] discovery monitor warning: {e}", file=sys.stderr, flush=True)
        if approved_phase1g:
            from scripts.prepare_phase1g import inputs
            state,rows=inputs()
            collection=collect_core(metrics=metrics,quiet=True,state=state,trusted=rows)
            collection['approved_expansion']='PHASE1G'
            collection['history_backfill']=read('data/staging/phase1g_backfill.json',{})
        elif approved_expansion:
            from scripts.prepare_expansion import inputs
            state,rows,approval=inputs()
            collection=collect_core(metrics=metrics,quiet=True,state=state,trusted=rows)
            collection['approved_expansion']='PHASE1F'
            collection['history_backfill']=read('data/staging/phase1f_backfill.json',{})
        else:
            print(f"[production_sync] collecting core regulations...", file=sys.stderr, flush=True)
            collection=collect_core(metrics=metrics,quiet=True)
            print(f"[production_sync] core regulations collected: {len(collection.get('registry', []))} rules", file=sys.stderr, flush=True)
        if full_audit:
            print(f"[production_sync] running full id revalidation...", file=sys.stderr, flush=True)
            checked=revalidate(collection,metrics=metrics)
            write_json(ROOT/'data/reports/full_id_revalidation.json',{'count':len(checked),'records':checked,'status':'PASS'})
        staged=collection.get('history_backfill')
        prepare(collection,previous_state,read('data/registry/change_history.json',[]),metrics=metrics)
        if staged: collection['history_backfill']=staged
        result=sync(collection)
        print(f"[production_sync] sync completed: {result.get('result')}", file=sys.stderr, flush=True)
        if result['result']=='BLOCKED': error=result.get('reason','INCOMPLETE_COLLECTION')
    except Exception as exc:
        print(f"[production_sync] sync error: {exc}", file=sys.stderr, flush=True)
        error=exc.code if isinstance(exc,ApiError) else 'SYNC_FAILED'
        result={'result':'BLOCKED','new_events':0,'public_rewritten':False,'dataset_version':previous.get('last_dataset_version')}
    ops=read('data/ops/health.json',previous)
    if error:
        ops.update({'last_successful_sync':previous.get('last_successful_sync'),'last_dataset_version':previous.get('last_dataset_version'),'publication_status':'BLOCKED','api_status':error})
    counts={'success_count':len(collection['registry']) if collection else 0,'review_count':sum(r['status']!='RESOLVED' for r in collection['resolution']) if collection else len(read('data/registry/rules.json',[]))}
    counts['failure_count']=counts['review_count']
    report={**result,'started_at':at,'finished_at':now(),'duration_seconds':round(time.monotonic()-start,6),**metrics.report(),**counts,'error_summary':{'code':error} if error else {},'mode':'WEEKLY_FULL_AUDIT' if full_audit else 'CORE_WITH_DAILY_DISCOVERY' if discovery else 'CORE_STABLE_IDS','last_good_dataset_version':ops.get('last_dataset_version')}
    report.update({'public_bytes_and_mtimes_identical':before==public_fingerprint(ROOT),'snapshot_hashes_identical':semantic_hashes(previous_state)==semantic_hashes(read('data/registry/state.json',{})),'event_ids_identical':[e['event_id'] for e in previous_events]==[e['event_id'] for e in read('data/registry/events.json',[])]})
    report['discovery_monitor_error']=locals().get('discovery_error')
    ops.update({'last_attempt':at,'duration_seconds':report['duration_seconds'],**metrics.report(),**counts})
    write_json(ROOT/'data/ops/health.json',ops); write_json(ROOT/'data/reports/production_sync.json',report)
    write_json(ROOT/'data/reports/production'/(at[:19].replace(':','').replace('-','')+'.json'),report)
    return report
def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--discovery',action='store_true'); parser.add_argument('--full-audit',action='store_true'); parser.add_argument('--approved-expansion',action='store_true'); parser.add_argument('--approved-phase1g',action='store_true'); args=parser.parse_args()
    report=run(discovery=args.discovery,full_audit=args.full_audit,approved_expansion=args.approved_expansion,approved_phase1g=args.approved_phase1g); print(json.dumps(report,ensure_ascii=False)); return int(report['result']=='BLOCKED')
if __name__=='__main__': sys.exit(main())

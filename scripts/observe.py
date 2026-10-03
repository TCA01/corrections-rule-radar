"""Normal LIVE collection/sync with private observation records; no deployment."""
import argparse
import json
import os
import sys
import time
import uuid
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.law_api import ApiError
from pipeline.operations import now
from pipeline.operations.metrics import Metrics
from pipeline.normalize import digest
from pipeline.snapshot import write_json
from scripts.collect import run as collect
from scripts.sync import sync,read,ROOT

def public_fingerprint(root):
    folder=Path(root)/'public/api/v1'
    return {str(p.relative_to(folder)).replace('\\','/'):{'hash':digest(p.read_text(encoding='utf-8')),'mtime_ns':p.stat().st_mtime_ns} for p in folder.rglob('*.json')}

def semantic_hashes(state):
    return {'current':{k:v['hashes'] for k,v in state.get('snapshots',{}).items()},'future':{k:[{'version_id':v['version_id'],'effective_date':v['metadata']['effective_date'],'hashes':v['hashes']} for v in vs] for k,vs in state.get('future',{}).items()}}

def observe_once():
    if not os.environ.get('LAW_API_OC','').strip(): raise ApiError('WAITING_FOR_LAW_API_OC')
    started=now(); clock=time.monotonic(); metrics=Metrics()
    run_id=started[:19].replace(':','').replace('-','')+'-'+uuid.uuid4().hex[:8]
    path=ROOT/'data/reports/observation'/(run_id+'.json')
    before=public_fingerprint(ROOT); state=read('data/registry/state.json',{}); events=read('data/registry/events.json',[])
    report={'run_id':run_id,'started_at':started,'finished_at':None,'duration_seconds':None,'observation_status':'RUNNING','source':'LIVE_NORMAL_SYNC'}
    write_json(path,report); errors=Counter(); collection=None
    try:
        collection=collect(metrics=metrics,quiet=True)
        result=sync(collection)
        errors.update(r['review_reason'] or 'UNRESOLVED' for r in collection['resolution'] if r['status']!='RESOLVED')
        if result['result']=='BLOCKED' and not errors: errors[result.get('reason','PUBLICATION_BLOCKED')]+=1
    except Exception as exc:
        code=exc.code if isinstance(exc,ApiError) else 'SYNC_FAILED'
        errors[code]+=1; result={'result':'BLOCKED','new_events':0,'dataset_version':None}
        ops=read('data/ops/health.json',{}); ops.update({'last_attempt':now(),'api_status':'OUTAGE_OR_SYNC_FAILURE','publication_status':'BLOCKED'})
        write_json(ROOT/'data/ops/health.json',ops)
    after=public_fingerprint(ROOT); next_events=read('data/registry/events.json',[]); ops=read('data/ops/health.json',{})
    resolution=collection['resolution'] if collection else []
    success=sum(r['status']=='RESOLVED' for r in resolution)
    changed_event_count=len(set(e['event_id'] for e in next_events)-set(e['event_id'] for e in events))
    report.update({'finished_at':now(),'duration_seconds':round(time.monotonic()-clock,6),'observation_status':'SUCCESS' if result['result'] in ('PUBLISHED','NO_CHANGE') else 'FAILED','success_count':success,'review_count':len(resolution)-success,'failure_count':len(resolution)-success if collection else len(state.get('snapshots',{})),'change_count':changed_event_count,'publication_status':result['result'],'last_good_dataset_version':ops.get('last_dataset_version'),'error_summary':dict(errors),'public_bytes_and_mtimes_identical':before==after,'event_ids_identical':[e['event_id'] for e in events]==[e['event_id'] for e in next_events],'snapshot_hashes_identical':semantic_hashes(state)==semantic_hashes(collection) if collection else None,**metrics.report()})
    write_json(path,report)
    return report

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--runs',type=int,default=1); args=parser.parse_args()
    if not 1<=args.runs<=10: parser.error('--runs must be 1..10; sequential only')
    failed=False
    for _ in range(args.runs):
        result=observe_once(); failed |= result['observation_status']=='FAILED'
        print(json.dumps(result,ensure_ascii=False),flush=True)
    return int(failed)

if __name__=='__main__':
    try: sys.exit(main())
    except ApiError as exc: print(exc.code); sys.exit(1)
    except Exception: print('OBSERVATION_FAILED'); sys.exit(1)

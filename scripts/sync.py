"""Run collection, then publish only complete validated state. No deployment."""
import argparse
import copy
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.law_api import ApiError
from pipeline.diff import compare,future_events,seed_events
from pipeline.operations import now,health
from pipeline.publication import build_contract,publish
from pipeline.snapshot import write_json
from pipeline.discovery import candidate
from pipeline.registry.domains import apply_domains

ROOT=Path(__file__).resolve().parents[1]
def read(path,default):
    p=ROOT/path
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default

def sync(collection):
    at=now(); previous=read('data/ops/health.json',{}); ops=health(collection,at,previous)
    if ops['publication_status']=='BLOCKED':
        write_json(ROOT/'data/ops/health.json',ops)
        return {'result':'BLOCKED','health':ops}
    state=read('data/registry/state.json',None); events=read('data/registry/events.json',[])
    if state:
        previous_ids=set(state['seed_ids']); actual_ids=set(collection['snapshots'])
        if previous_ids!=actual_ids:
            pending=seed_events(previous_ids,actual_ids,{**state['snapshots'],**collection['snapshots']},at)
            discoveries=[candidate(cid,collection['snapshots'][cid]['metadata']['name'],collection['snapshots'][cid]['official_source_url'],'CORRECTIONS_SEED') for cid in sorted(actual_ids-previous_ids)]
            write_json(ROOT/'data/reports/pending_seed_events.json',pending)
            write_json(ROOT/'data/reports/discovery_candidates.json',discoveries)
            ops.update({'publication_status':'BLOCKED','api_status':'SEED_MEMBERSHIP_REVIEW','review_count':len(previous_ids^actual_ids),'last_successful_sync':previous.get('last_successful_sync')})
            write_json(ROOT/'data/ops/health.json',ops)
            return {'result':'BLOCKED','reason':'SEED_MEMBERSHIP_REQUIRES_REVIEW','health':ops}
        prior_registry={r['canonical_id']:r for r in read('data/registry/rules.json',[])}
        collection=copy.deepcopy(collection)
        for row in collection['registry']:
            prior=prior_registry.get(row['canonical_id'])
            if prior:
                row['seed_names']=list(dict.fromkeys(prior['seed_names']+row['seed_names']))
                old_names=prior['historical_names']+row['historical_names']
                if prior['current_name']!=row['current_name']: old_names.append(prior['current_name'])
                row['historical_names']=list(dict.fromkeys(n for n in old_names if n!=row['current_name']))
    added=[]
    collection=apply_domains(collection,read('data/registry/business_domains.json',None))
    if state:
        for cid,new in collection['snapshots'].items():
            added+=compare(state['snapshots'].get(cid),new,at,repeal_evidence=new.get('repeal_evidence'))
            added+=future_events(state.get('future',{}).get(cid,[]),collection['future'].get(cid,[]),at)
        added+=seed_events(state['seed_ids'],list(collection['snapshots']),{**state['snapshots'],**collection['snapshots']},at)
    else:
        # First current dataset is a baseline, not a flood of fake amendments.
        for versions in collection['future'].values(): added+=future_events([],versions,at)
    known={e['event_id'] for e in events}; events+= [e for e in added if e['event_id'] not in known]; events.sort(key=lambda e:e['event_id'])
    # Existing version artifacts remain available after current/future placement
    # changes. Event references resolve from retained official evidence.
    history=[json.loads(p.read_text(encoding='utf-8')) for p in (ROOT/'data/snapshots').rglob('*.json')]
    history += [json.loads(p.read_text(encoding='utf-8'))['version'] for p in (ROOT/'public/api/v1/rules').glob('*/versions/*.json')]
    version,files=build_contract(collection,events,at,history=history)
    # Persist enriched comparison references so a future event keeps its original
    # baseline after becoming current; event IDs never depend on derived display.
    events=sorted(files['changes/latest.json'][1]['events']+files['changes/upcoming.json'][1]['events'],key=lambda e:e['event_id'])
    changed=version!=previous.get('last_dataset_version')
    if changed:
        try: publish(files,ROOT)
        except Exception:
            ops.update({'publication_status':'BLOCKED','last_successful_sync':previous.get('last_successful_sync')})
            write_json(ROOT/'data/ops/health.json',ops)
            raise ValueError('PUBLICATION_VALIDATION_OR_SWITCH_FAILED') from None
    ops.update({'last_dataset_version':version,'publication_status':'PUBLISHED' if changed else 'NO_CHANGE'})
    if changed:
        write_json(ROOT/'data/registry/rules.json',collection['registry'])
        write_json(ROOT/'data/registry/state.json',{'snapshots':collection['snapshots'],'future':collection['future'],'seed_ids':sorted(collection['snapshots'])})
    write_json(ROOT/'data/registry/events.json',events)
    write_json(ROOT/'data/ops/health.json',ops)
    report={'result':'PUBLISHED' if changed else 'NO_CHANGE','dataset_version':version,'new_events':len([e for e in added if e['event_id'] not in known]),'public_rewritten':changed}
    write_json(ROOT/'data/reports/last_sync.json',report)
    return report

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--from-collected',action='store_true'); args=parser.parse_args()
    if not args.from_collected:
        from scripts.collect import run
        try: run()
        except Exception:
            ops=read('data/ops/health.json',{})
            ops.update({'last_attempt':now(),'api_status':'OUTAGE_OR_SEED_FAILURE','publication_status':'BLOCKED'})
            write_json(ROOT/'data/ops/health.json',ops)
            raise
    collection=read('data/staging/collection.json',None)
    if not collection: raise ValueError('NO_COLLECTION')
    print(json.dumps(sync(collection),ensure_ascii=False))

if __name__=='__main__':
    try: main()
    except ApiError as e: print(e.code); sys.exit(1)
    except Exception: print('SYNC_FAILED_PUBLICATION_BLOCKED'); sys.exit(1)

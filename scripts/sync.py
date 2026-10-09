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
from pipeline.diff.history import make_event,merge,identity
from pipeline.publication.versions import url
from pipeline.registry.approval import verify_expansion
from pipeline.registry.provenance import apply_provenance
from pipeline.diff.effective_states import reconcile_upcoming,state_key

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
        expanded=previous_ids!=actual_ids and verify_expansion(ROOT,state,collection)
        if previous_ids!=actual_ids and not expanded:
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
    collection=apply_provenance(collection,read('data/registry/provenance.json',None))
    collection=apply_domains(collection,read('data/registry/business_domains.json',None))
    fallback=[{'canonical_id':r['canonical_id'],'current_name':r['current_name'],'primary_domain':'기타','reason':'APPROVED_MAPPING_CONTENT_CHANGED_OR_MISSING'} for r in collection['registry'] if r.get('domain_assignment_status')=='FALLBACK']
    write_json(ROOT/'data/reports/domain_fallback.json',{'records':fallback,'count':len(fallback)})
    if state:
        for cid,new in collection['snapshots'].items():
            # Inclusion in the approved scope establishes a current baseline;
            # it is not evidence that a legal amendment happened today.
            if cid in state['snapshots']: added+=compare(state['snapshots'][cid],new,at,repeal_evidence=new.get('repeal_evidence'))
            added+=future_events(state.get('future',{}).get(cid,[]),collection['future'].get(cid,[]),at)
        # Scope expansion is provenance, not a legal-change event.
    else:
        # First current dataset is a baseline, not a flood of fake amendments.
        for versions in collection['future'].values(): added+=future_events([],versions,at)
    known={e['event_id'] for e in events}; events+= [e for e in added if e['event_id'] not in known]; events.sort(key=lambda e:e['event_id'])
    # Existing version artifacts remain available after current/future placement
    # changes. Event references resolve from retained official evidence.
    history=[json.loads(p.read_text(encoding='utf-8')) for p in (ROOT/'data/snapshots').rglob('*.json')]
    history += [json.loads(p.read_text(encoding='utf-8'))['version'] for p in (ROOT/'public/api/v1/rules').glob('*/versions/*.json')]
    persistent=read('data/registry/change_history.json',[])
    previous_persistent_ids={e['event_id'] for e in persistent}
    candidates=[]; staged=collection.get('history_backfill',{})
    history+=staged.get('snapshots',[])
    for row in collection['registry']:
        prior_names=[s['metadata']['name'] for s in staged.get('snapshots',[]) if s['canonical_id']==row['canonical_id'] and s['metadata']['name']!=row['current_name']]
        row['historical_names']=list(dict.fromkeys(row['historical_names']+sorted(set(prior_names))))
    for pair in staged.get('pairs',[]):
        new=pair['after']
        original=[e['detected_at'] for e in events if e['canonical_id']==new['canonical_id'] and e['new_version']==new['version_id'] and e['effective_date']==new['metadata']['effective_date']]
        detected=min(original) if original else at
        candidates.append(make_event(pair['before'],new,detected,official_comparison=pair.get('official_comparison'),comparison_evidence=pair.get('comparison_evidence')))
    by_url={url(s):s for s in history+list(collection['snapshots'].values())+[v for vs in collection['future'].values() for v in vs]}
    upcoming_keys={state_key(v) for vs in collection['future'].values() for v in vs}
    # Migrate exact retained comparisons, preserving original detection time.
    for e in events:
        ref=e.get('old_reference') or e.get('articles_compared_to')
        old=by_url.get(ref['snapshot_url']) if ref else (state or {}).get('snapshots',{}).get(e['canonical_id'])
        new=next((v for v in by_url.values() if v['canonical_id']==e['canonical_id'] and v['version_id']==e['new_version'] and v['hashes']==e['new_hashes']),None)
        if not new: raise ValueError('HISTORY_EVENT_VERSION_MISSING')
        if state_key(new) in upcoming_keys: continue
        # Once a future version becomes current, its recorded comparison is
        # immutable. Official-state flags and placement cannot create a new event.
        if any(p['canonical_id']==new['canonical_id'] and p['after_version']['identifier']==new['version_id'] and p['after_version']['effective_date']==new['metadata']['effective_date'] and p['after_version']['body_hash']==new['hashes']['body_hash'] for p in persistent+candidates if p):
            if not old or old['version_id']!=new['version_id']: continue
        candidates.append(make_event(old,new,e['detected_at']))
    if state:
        for cid,new in collection['snapshots'].items():
            old=state['snapshots'].get(cid)
            if old and old['version_id']==new['version_id'] and old['hashes']!=new['hashes']:
                candidates.append(make_event(old,new,at))
    persistent=merge(persistent,candidates)
    persistent,replacements=reconcile_upcoming(persistent,collection,at)
    version,files=build_contract(collection,events,at,history=history,persistent=persistent)
    # Persist enriched comparison references so a future event keeps its original
    # baseline after becoming current; event IDs never depend on derived display.
    events=sorted(files['changes/latest.json'][1]['events']+files['changes/upcoming.json'][1]['events'],key=lambda e:e['event_id'])
    # Actions starts from a fresh checkout. Private attempt health is deliberately
    # not committed, so its version may predate the published legal dataset.
    # Compare against the validated publication, not that operational cache.
    changed=version!=read('public/api/v1/manifest.json',{}).get('dataset_version')
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
        write_json(ROOT/'data/registry/change_history.json',persistent)
        if replacements: write_json(ROOT/'data/reports/phase1h_history_migration.json',{'schema_version':'1.5','replacements':replacements,'past_events_preserved':True})
    write_json(ROOT/'data/registry/events.json',events)
    write_json(ROOT/'data/ops/health.json',ops)
    report={'result':'PUBLISHED' if changed else 'NO_CHANGE','dataset_version':version,'new_events':len([e for e in added if e['event_id'] not in known]),'persistent_new_events':len([e for e in persistent if e['event_id'] not in previous_persistent_ids]),'public_rewritten':changed}
    write_json(ROOT/'data/reports/last_sync.json',report)
    return report

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--from-collected',action='store_true'); args=parser.parse_args()
    if not args.from_collected:
        from scripts.collect_core import run
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

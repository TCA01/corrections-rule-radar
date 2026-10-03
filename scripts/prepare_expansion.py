"""Prepare the approved 38 with live API resolution; no production publication."""
import copy,json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.normalize import digest
from pipeline.registry.approval import approved_candidates
from pipeline.operations import now
from pipeline.operations.metrics import Metrics
from pipeline.snapshot import write_json
from scripts.collect_core import run as collect
from scripts.backfill_history import run as backfill

ROOT=Path(__file__).resolve().parents[1]
def load(path): return json.loads((ROOT/path).read_text(encoding='utf8'))

def inputs():
    audit=load('data/reports/phase1d_api_eligibility.json'); additions=approved_candidates(audit)
    state=load('data/registry/state.json'); rows=load('data/registry/rules.json')
    if len(rows)!=68 or set(state['seed_ids'])!={r['canonical_id'] for r in rows}: raise ValueError('PREVIOUS_68_SCOPE_DISCREPANCY_STOP')
    scope=load('data/reports/phase1c_scope_audit.json')
    by_id={r['canonical_id']:r for r in scope['current_records']+scope['discovery_candidates']}
    for entry in additions:
        s=entry['snapshot']; rows.append({'canonical_id':s['canonical_id'],'source_kind':s['source_kind'],'current_name':s['metadata']['name'],'seed_names':[],'historical_names':[],'corrections_category':s['metadata']['rule_type'],'business_domains':[],'classification_status':'REVIEWED','status':'CURRENT','version_id':s['version_id'],'current_effective_date':s['metadata']['effective_date'],'law_or_rule_identifier':s['stable_identifier'],'official_source':s['official_source_url']})
        state['snapshots'][s['canonical_id']]=s; state['future'][s['canonical_id']]=entry['future_effective_capability']['future_versions']
    state['seed_ids']=sorted(state['snapshots'])
    for row in rows:
        evidence=by_id[row['canonical_id']]; historical=row['status']=='REPEALED'
        scope_class='HISTORICAL_REPEALED' if historical else evidence.get('scope_class',evidence.get('scope_class_candidate'))
        row['provenance']={'scope_class':scope_class,'selection_basis':evidence.get('selection_basis',evidence.get('reason')),
            'applies_to':evidence['applies_to'],'official_seed_name':evidence.get('official_seed_name'),'official_seed_url':evidence.get('official_seed_url'),
            'canonical_source_url':row['official_source'],'discovery_source':['CORRECTIONS_PAGE'] if row['seed_names'] else ['LAW_API_MINISTRY','LAW_API_KEYWORD'],
            'scope_review_status':'APPROVED','api_tracking_class':'API_TRACKABLE',
            'structured_body_source':'LAWGO_JSON_XML','history_source':'LAWGO_STRUCTURED_HISTORY','appendix_metadata_source':'LAWGO_STRUCTURED_METADATA'}
        if not row['provenance']['selection_basis'] or scope_class not in ('OFFICIAL_CORRECTIONS_LIST','DIRECT_CORRECTIONS','CROSS_DOMAIN_CORRECTIONS','HISTORICAL_REPEALED'): raise ValueError('PROVENANCE_EVIDENCE_MISSING')
    approval={'release':'PHASE1F','status':'APPROVED','previous_ids':load('data/registry/state.json')['seed_ids'],'additions':sorted(r['canonical_id'] for r in additions),'evidence_hash':digest(audit),'authorization':'PRODUCT_OWNER_PHASE1F_EXPLICIT_38_APPROVAL'}
    return state,rows,approval

def run():
    state,rows,approval=inputs(); metrics=Metrics(); at=now(); start=time.monotonic()
    write_json(ROOT/'data/registry/scope_approval.json',approval)
    collection=collect(state=state,trusted=rows,metrics=metrics,output='data/staging/phase1f_collection.json')
    report={'started_at':at,'finished_at':now(),'duration_seconds':round(time.monotonic()-start,3),'metrics':metrics.report(),'resolution':collection['resolution']}
    write_json(ROOT/'data/reports/phase1f_live_resolution.json',report)
    if len(collection['snapshots'])!=106 or any(r['status']!='RESOLVED' for r in collection['resolution']): raise ValueError('LIVE_106_RESOLUTION_FAILED_LAST_GOOD_UNCHANGED')
    new_rows=[r for r in collection['registry'] if r['canonical_id'] in approval['additions']]
    live_state={'snapshots':collection['snapshots'],'future':collection['future'],'seed_ids':sorted(collection['snapshots'])}
    backfill(state=live_state,rows=new_rows,output=ROOT/'data/staging/phase1f_backfill.json',report='data/reports/phase1f_backfill.json',cache_name='phase1f')
    print('APPROVED_38_LIVE_RESOLVED_AND_HISTORY_PREPARED',flush=True)

if __name__=='__main__': run()

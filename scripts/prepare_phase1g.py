"""One explicitly approved law: live structured eligibility before admission."""
import argparse,copy,json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.law_api import LawClient
from pipeline.law_api.search import search
from pipeline.registry import identifiers,normalized_title
from pipeline.normalize import digest
from pipeline.diff.history import article_groups,make_event
from pipeline.operations import now
from pipeline.operations.metrics import Metrics
from pipeline.snapshot import write_json
from scripts.collect_core import run as collect
from scripts.backfill_history import run as backfill

ROOT=Path(__file__).resolve().parents[1]
TITLE='형사소송법'
def load(name): return json.loads((ROOT/name).read_text(encoding='utf8'))
def duplicates(rows,cid=None):
    return [r['canonical_id'] for r in rows if r['canonical_id']==cid or any(normalized_title(n)==TITLE for n in [r['current_name']]+r['seed_names']+r['historical_names'])]
def audit():
    rows=load('data/registry/rules.json'); state=load('data/registry/state.json')
    if len(rows)!=106 or len(state['seed_ids'])!=106 or duplicates(rows): raise ValueError('PHASE1G_DUPLICATE_OR_PREVIOUS_SCOPE_STOP')
    start=time.monotonic(); metrics=Metrics(); client=LawClient(metrics=metrics)
    items,proof=search(client,'eflaw',query=TITLE,nw='2,3')
    exact=[i for i in items if normalized_title(i.get('법령명한글',''))==TITLE]
    stable_ids={identifiers(i,'law')[0] for i in exact}
    current=[i for i in exact if i.get('현행연혁코드')=='현행']
    if len(stable_ids)!=1 or len(current)!=1: raise ValueError('EXACT_OFFICIAL_IDENTITY_AMBIGUOUS_STOP')
    stable,serial=identifiers(current[0],'law'); cid='law-'+stable
    if duplicates(rows,cid): raise ValueError('PHASE1G_DUPLICATE_STABLE_ID_STOP')
    # Bootstrap only the API-discovered stable identity. The collector independently
    # resolves list/detail serial, dates, body and future versions by this identity.
    row={'canonical_id':cid,'source_kind':'law','current_name':TITLE,'seed_names':[],'historical_names':[],
         'corrections_category':'법률','business_domains':[],'classification_status':'REVIEWED','status':'CURRENT',
         'version_id':serial,'law_or_rule_identifier':stable}
    collection=collect(state={'seed_ids':[cid],'snapshots':{cid:{'stable_identifier':stable}},'future':{}},trusted=[row],metrics=metrics,quiet=True,output='data/staging/phase1g_law.json')
    if len(collection['snapshots'])!=1 or collection['resolution'][0]['status']!='RESOLVED': raise ValueError('STRUCTURED_API_ELIGIBILITY_FAILED_STOP')
    sn=collection['snapshots'][cid]
    if sn['metadata']['name']!=TITLE or sn['metadata']['rule_type']!='법률' or sn['version_id']!=serial: raise ValueError('OFFICIAL_LIST_BODY_MISMATCH_STOP')
    groups=article_groups(sn['body'])
    if not groups or not sn['metadata']['issue_date'] or not sn['metadata']['issue_number']: raise ValueError('STRUCTURED_ELIGIBILITY_INCOMPLETE_STOP')
    history,history_proof=search(client,'eflaw',LID=stable,nw='1,2,3')
    history=[i for i in history if identifiers(i,'law')[0]==stable]
    if not history: raise ValueError('OFFICIAL_HISTORY_UNAVAILABLE_STOP')
    queue_hits=[]
    for path in ('data/reports/discovery_candidates_api.json','data/reports/discovery_candidates.json'):
        p=ROOT/path
        if p.exists():
            candidates=load(path)
            if isinstance(candidates,list): queue_hits.extend(r for r in candidates if r.get('canonical_id')==cid or normalized_title(r.get('candidate_name',r.get('name','')))==TITLE)
    report={'phase':'PHASE1G','status':'PASS','api_tracking_class':'API_TRACKABLE','canonical_id':cid,'stable_law_id':stable,
            'current_mst':serial,'official_title':sn['metadata']['name'],'metadata':sn['metadata'],
            'official_source_url':sn['official_source_url'],'hashes':sn['hashes'],'structured_article_count':len(groups),
            'list_evidence':proof,'history_evidence':history_proof,'history_version_count':len(history),
            'discovery_candidate_hits':queue_hits,'production_duplicate_hits':[],
            'snapshot_diff_capability':bool(make_event(sn,{**sn,'version_id':serial+'0'},now())),
            'metrics':metrics.report(),'duration_seconds':round(time.monotonic()-start,3),'verified_at':now()}
    write_json(ROOT/'data/reports/phase1g_api_eligibility.json',report)
    print(json.dumps({k:report[k] for k in ('status','canonical_id','official_title','metadata','history_version_count')},ensure_ascii=False),flush=True)
    return collection,report
def prepare():
    collection,evidence=audit(); cid=evidence['canonical_id']; sn=collection['snapshots'][cid]
    history=backfill(state={'seed_ids':[cid],'snapshots':collection['snapshots'],'future':collection['future']},rows=collection['registry'],output=ROOT/'data/staging/phase1g_backfill.json',report='data/reports/phase1g_backfill.json',cache_name='phase1g',max_history_pairs=32)
    if not history['pairs'] or history['records'][0]['status']=='REVIEW': raise ValueError('HISTORY_VERIFICATION_FAILED_STOP')
    provenance={'scope_class':'CROSS_DOMAIN_CORRECTIONS','selection_basis':'수용기록 업무에서 구속·영장·석방 등 형사절차 관련 사항 확인에 직접 활용되는 기본법',
        'applies_to':['수용기록 업무','구속·영장 관련 업무','석방 관련 업무'],'official_seed_name':None,'official_seed_url':None,
        'canonical_source_url':sn['official_source_url'],'discovery_source':['MANUAL_OFFICIAL_REVIEW','LAW_API_KEYWORD'],
        'scope_review_status':'APPROVED','api_tracking_class':'API_TRACKABLE','structured_body_source':'LAWGO_JSON_XML',
        'history_source':'LAWGO_STRUCTURED_HISTORY','appendix_metadata_source':'LAWGO_STRUCTURED_METADATA'}
    groups=article_groups(sn['body']); selected=[a for a in groups.values() if any(t in a['text'] for t in ('구속','영장','석방'))][:10]
    basis={'method':'OFFICIAL_METADATA_AND_SCOPE_REVIEW','reviewer':'CODEX_EVIDENCE_REVIEW','owner_decision':'PRODUCT_OWNER_PHASE1G_EXPLICIT_SCOPE_APPROVAL',
        'legal_interpretation':False,'title':sn['metadata']['name'],'official_department':sn['metadata']['department'],
        'official_source_url':sn['official_source_url'],'version_id':sn['version_id'],'body_hash':sn['hashes']['body_hash'],
        'metadata_hash':sn['hashes']['metadata_hash'],'official_text_excerpt':'\n'.join(a['text'] for a in selected)[:3500],
        'article_headings':[a['article_title'] for a in selected],'rationale':'제품 책임자가 승인한 수용기록·구속·영장·석방 관련 검색 맥락과 공식 본문을 기존 수용·보안 분야에 연결','confidence':'HIGH'}
    prov=load('data/registry/provenance.json'); prov['rules'][cid]=provenance
    domains=load('data/registry/business_domains.json'); domains['rules'].append({'canonical_id':cid,'current_name':sn['metadata']['name'],'primary_domain':'수용·보안','secondary_domains':[],'classification_basis':basis,'review_status':'REVIEWED'})
    approval={'release':'PHASE1G','status':'APPROVED','previous_ids':load('data/registry/state.json')['seed_ids'],'additions':[cid],
        'evidence_hash':digest(evidence),'authorization':'PRODUCT_OWNER_PHASE1G_EXPLICIT_CRIMINAL_PROCEDURE_ACT_ONLY'}
    collection['registry'][0]['provenance']=provenance
    write_json(ROOT/'data/staging/phase1g_law.json',collection)
    write_json(ROOT/'data/registry/provenance.json',prov)
    write_json(ROOT/'data/registry/business_domains.json',domains)
    write_json(ROOT/'data/registry/scope_approvals/phase1g.json',approval)
    print('ONE_APPROVED_LAW_READY_NO_PUBLICATION',flush=True)
def inputs():
    approval=load('data/registry/scope_approvals/phase1g.json'); staged=load('data/staging/phase1g_law.json')
    state=load('data/registry/state.json'); rows=load('data/registry/rules.json'); cid=approval['additions'][0]
    if len(rows)!=106 or cid in state['seed_ids']: raise ValueError('PHASE1G_APPROVAL_CANNOT_BE_REUSED')
    rows+=staged['registry']; state['snapshots'].update(staged['snapshots']); state['future'].update(staged['future']); state['seed_ids']=sorted(state['snapshots'])
    return state,rows
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--audit-only',action='store_true'); args=p.parse_args()
    audit() if args.audit_only else prepare()

"""Evidence-bound domain/provenance assignments for the approved release."""
import copy,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.snapshot import write_json
from pipeline.diff.history import article_groups
from scripts.prepare_expansion import inputs

ROOT=Path(__file__).resolve().parents[1]
def load(path): return json.loads((ROOT/path).read_text(encoding='utf8'))

# These are reviewed registry decisions, not legal interpretations or title-based
# tracking identities. Each decision is saved together with actual official text.
DECISIONS={
 '2036599':('인사·조직',[]),'2078078':('보고',['수용·보안']),
 '26402':('인사·조직',[]),'27435':('인사·조직',[]),'27439':('인사·조직',[]),
 '27525':('인사·조직',['급식·복지']),'27617':('인사·조직',[]),'29857':('인사·조직',['기타']),
 '32125':('기타',[]),'35611':('수용·보안',[]),'37000':('인사·조직',[]),'37001':('인사·조직',[]),
 '37470':('인권·청원',[]),'37556':('인사·조직',['교육·교화','작업·직업훈련']),
 '37578':('인사·조직',['민원']),'38684':('인사·조직',['인권·청원']),
 '38793':('인사·조직',[]),'54232':('인사·조직',[]),'64876':('인사·조직',[]),
 '66785':('인사·조직',[]),'68106':('인사·조직',[]),'69673':('인사·조직',[]),
 '74433':('인사·조직',[]),'74434':('인사·조직',[]),'75221':('인사·조직',[]),
 '77216':('인사·조직',[]),'78303':('교육·교화',['인사·조직']),
 '83074':('의료',[]),'84204':('인사·조직',[]),'84831':('인사·조직',[]),
 '86352':('인사·조직',[]),'86499':('수용·보안',[]),'87003':('수용·보안',['인사·조직']),
 '89409':('인사·조직',[]),'91035':('인사·조직',[]),'97044':('심리치료',['교육·교화']),
 '97483':('인사·조직',[]),'98096':('기타',[])}

def run():
    collection=load('data/staging/phase1f_collection.json'); _,approved_rows,approval=inputs()
    if len(collection['registry'])!=106 or any(r['status']!='RESOLVED' for r in collection['resolution']): raise ValueError('LIVE_106_REQUIRED')
    prov={r['canonical_id']:r['provenance'] for r in approved_rows}
    write_json(ROOT/'data/registry/provenance.json',{'release':'PHASE1F','rules':prov})
    previous=load('data/registry/business_domains.json')
    write_json(ROOT/'data/staging/phase1f_previous_domains.json',previous)
    mappings={r['canonical_id']:copy.deepcopy(r) for r in previous['rules']}; low=[]
    for row in collection['registry']:
        cid=row['canonical_id']; s=collection['snapshots'][cid]; old=mappings.get(cid)
        if cid in ('admrul-32484','admrul-51868'): primary='보고'; secondary=[]
        elif cid in approval['additions']: primary,secondary=DECISIONS[cid.split('-')[1]]
        else: primary=old['primary_domain']; secondary=old['secondary_domains']
        if not primary: raise ValueError('CONTROLLED_DOMAIN_MISSING')
        groups=article_groups(s['body']) or {}; texts=[a['text'] for a in groups.values()]
        # Non-article administrative guidance still has official structured text.
        raw=s['body']['articles']; excerpt='\n'.join(texts) if texts else json.dumps(raw,ensure_ascii=False)
        basis=copy.deepcopy(old['classification_basis']) if old else {}
        basis.update({'method':'OFFICIAL_METADATA_AND_SCOPE_REVIEW','reviewer':'CODEX_EVIDENCE_REVIEW','legal_interpretation':False,
            'title':s['metadata']['name'],'official_department':s['metadata']['department'],
            'official_source_url':s['official_source_url'],'version_id':s['version_id'],
            'body_hash':s['hashes']['body_hash'],'metadata_hash':s['hashes']['metadata_hash'],
            'purpose':next((a['text'] for a in groups.values() if '(목적)' in a['article_title']),None),
            'scope':next((a['text'] for a in groups.values() if '(적용범위)' in a['article_title']),None),
            'official_text_excerpt':excerpt[:2200],'article_headings':[a['article_title'] for a in groups.values()],
            'rationale':'공식 제목·소관부서·목적·적용범위 및 본문을 업무 검색 분야와 연결. 세부 업무 지시는 제공하지 않음.',
            'confidence':'LOW' if primary=='기타' else 'HIGH'})
        if cid in ('admrul-32484','admrul-51868'): basis['owner_decision']='PHASE1F_REPORT_DOMAIN_APPROVED_BY_PRODUCT_OWNER'
        if primary=='기타': low.append({'canonical_id':cid,'current_name':s['metadata']['name'],'reason':'공식 제목·본문의 업무 주제를 현재 통제 업무분야에 직접 연결하기 어려워 기타로 분류. 법적 적용 판단이 아님.','primary_domain':primary})
        mappings[cid]={'canonical_id':cid,'current_name':s['metadata']['name'],'primary_domain':primary,'secondary_domains':secondary,'classification_basis':basis,'review_status':'REVIEWED'}
    previous.update({'registry_version':'1.4','fallback_policy':'OTHER_WITH_INTERNAL_LOW_CONFIDENCE','review_policy':'Approved mappings use exact official evidence. Changed/unmapped approved rules safely use 기타 with an internal low-confidence report; no periodic manual update dependency.','rules':list(mappings.values())})
    write_json(ROOT/'data/registry/business_domains.json',previous)
    taxonomy=load('data/seed/business_domains.json')
    if '보고' not in taxonomy['domains']: taxonomy['domains'].insert(-1,'보고')
    taxonomy['policy']='Multi-domain metadata organization; evidence-reviewed mappings and approved 기타 fallback. No legal interpretation.'
    write_json(ROOT/'data/seed/business_domains.json',taxonomy)
    write_json(ROOT/'data/reports/phase1f_domain_review.json',{'classified':106,'low_confidence':low,'requested_id_title_notes':[
        {'canonical_id':cid,'official_current_name':collection['snapshots'][cid]['metadata']['name'],'decision':'보고 assignment follows the explicitly requested stable ID; no title-based re-keying'} for cid in ('admrul-32484','admrul-51868')]})
    print('PROVENANCE_106_DOMAINS_106_CONFIGURED')

if __name__=='__main__': run()

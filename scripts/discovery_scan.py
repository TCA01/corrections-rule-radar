"""Opaque page-change monitoring and API-only discovery; never changes scope.

The two Corrections pages are fingerprinted as bytes only, never parsed. They
are an independent discovery signal, not a source for production legal data.
"""
import hashlib,json,time,urllib.request
from pathlib import Path
from pipeline.law_api import LawClient,ApiError
from pipeline.law_api.search import search
from pipeline.operations import now
from pipeline.registry import identifiers
from pipeline.snapshot import write_json

ROOT=Path(__file__).resolve().parents[1]
URLS={'law':'https://www.corrections.go.kr/corrections/2534/subview.do','admrul':'https://www.corrections.go.kr/corrections/2535/subview.do'}

def public_page(url,metrics=None):
    if url not in URLS.values(): raise ValueError('UNTRUSTED_DISCOVERY_PAGE')
    start=time.monotonic(); error=None
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'CorrectionsRuleRadar/1.4'}),timeout=30) as response: return response.read()
    except Exception:
        error='DISCOVERY_PAGE_UNAVAILABLE'; raise ApiError(error) from None
    finally:
        if metrics: metrics.record('public_page',time.monotonic()-start,error)

def api_discovery(metrics=None):
    client=LawClient(metrics=metrics); items,evidence=search(client,'admrul',org='1270000',nw=1)
    known={r['canonical_id'] for r in json.loads((ROOT/'data/registry/rules.json').read_text(encoding='utf8'))}
    prior_path=ROOT/'data/reports/discovery_candidates_api.json'
    prior=json.loads(prior_path.read_text(encoding='utf8')) if prior_path.exists() else []
    queue={r['canonical_id']:r for r in prior}
    for item in items:
        stable,serial=identifiers(item,'admrul'); cid='admrul-'+stable
        if cid in known: continue
        queue.setdefault(cid,{'canonical_id':cid,'candidate_name':item['행정규칙명'],'discovery_source':'LAW_API_MINISTRY','lifecycle':'DISCOVERED','first_seen_at':now(),'requires':['API_ELIGIBILITY_AUDIT','SCOPE_REVIEW','HUMAN_APPROVAL'],'auto_production_entry':False})
    write_json(prior_path,sorted(queue.values(),key=lambda r:r['canonical_id']))
    return {'api_candidates_pending':len(queue),'list_evidence':evidence}
def run(*,metrics=None,full_audit=False):
    path=ROOT/'data/ops/discovery_pages.json'; previous=json.loads(path.read_text(encoding='utf8')) if path.exists() else {}
    fingerprints={kind:hashlib.sha256(public_page(url,metrics)).hexdigest() for kind,url in URLS.items()}
    changed=fingerprints!=previous.get('page_sha256')
    report={'last_attempt':now(),'table_changed':changed,'monitor_mode':'OPAQUE_BYTES_ONLY_NO_HTML_PARSING','full_identity_audit':bool(full_audit),'production_membership_changed':False}
    if changed: report.update(api_discovery(metrics))
    write_json(ROOT/'data/reports/discovery_scan.json',report)
    write_json(path,{'page_sha256':fingerprints})
    return None

"""Live sequential collection; unresolved items remain explicit REVIEW records."""
import json
import re
import sys
import time
import urllib.request
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse,unquote,quote,parse_qs
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bs4 import BeautifulSoup
from pipeline.law_api import LawClient,ApiError
from pipeline.corrections_seed import parse_seed,URLS
from pipeline.registry import as_list,unwrap,identifiers,normalized_title
from pipeline.normalize import snapshot
from pipeline.snapshot import write_json,save_snapshot
from pipeline.operations.calendar import seoul_date

def public_page(url,metrics=None):
    p=urlparse(url)
    if p.scheme!='https' or p.hostname not in ('www.law.go.kr','law.go.kr','www.corrections.go.kr'): raise ValueError('UNTRUSTED_URL')
    encoded=p._replace(path=quote(unquote(p.path),safe='/(),')).geturl()
    started=time.monotonic(); error=None
    try:
        with urllib.request.urlopen(urllib.request.Request(encoded,headers={'User-Agent':'CorrectionsRuleRadar/0.0.1'}),timeout=30) as r:
            return r.read().decode('utf-8')
    except Exception:
        error='OFFICIAL_PAGE_FAILED'
        raise ApiError(error) from None
    finally:
        if metrics: metrics.record('public_page',time.monotonic()-started,error)

def search(c,target,**params):
    items=[]; evidence=[]
    for page in range(1,101):
        obj,ev=c.fetch(target=target,display=100,page=page,**params); root=unwrap(obj)
        if 'totalCnt' not in root: raise ValueError('LIST_SCHEMA_CHANGED')
        batch=as_list(root.get('admrul' if target=='admrul' else 'law'))
        items+=batch; evidence.append(ev)
        if len(items)>=int(root['totalCnt']): return items,evidence
        if not batch: raise ValueError('PAGINATION_INCOMPLETE')
    raise ValueError('PAGINATION_LIMIT')

def run(*,metrics=None,quiet=False):
    c=LawClient(metrics=metrics); now=datetime.now(timezone.utc).isoformat(); seed=[]; counts={}
    for kind,url in URLS.items():
        html=public_page(url,metrics)
        Path('data/raw_cache').mkdir(parents=True,exist_ok=True)
        Path('data/raw_cache/seed_'+('admin' if kind=='admrul' else 'law')+'.html').write_text(html,encoding='utf-8')
        entries,category_counts=parse_seed(html,kind,now); seed+=entries; counts.update(category_counts)
    write_json('data/seed/corrections.json',{'entries':seed,'counts':counts,'expected_baseline':{'법률':6,'대통령령':7,'법무부령':6,'예규':36,'훈령':13},'baseline_difference':sum(counts.values())-68})
    results=[]; registry=[]; snapshots={}; future={}
    for index,e in enumerate(seed,1):
        kind=e['source_kind']; record={**e,'status':'REVIEW','review_reason':None,'confidence':0.0,'canonical_id':None,'current_name':None,'resolution_method':None}
        try:
            old=None
            if kind=='admrul':
                html=public_page(e['outgoing_url'],metrics); soup=BeautifulSoup(html,'html.parser')
                iframe=soup.find('iframe',src=True)
                seq=parse_qs(urlparse(iframe['src'] if iframe else '').query).get('admRulSeq',[None])[0]
                if not seq or not seq.isdigit(): raise ValueError('OUTGOING_IDENTIFIER_MISSING')
                try:
                    old_obj,old_ev=c.fetch('lawService.do',target=kind,ID=seq)
                    old=snapshot(old_obj,kind,seq,old_ev); save_snapshot(old)
                    stable=old['stable_identifier']
                    method='OFFICIAL_OUTGOING_SERIAL_THEN_STABLE_LID'
                except ValueError as err:
                    if str(err)!='EMPTY_API_RESULT': raise
                    # Retired historical serials may no longer be served. Exact
                    # current title is a documented lower-priority fallback.
                    candidates,_=search(c,'admrul',query=e['seed_name'],nw=1)
                    exact=[i for i in candidates if normalized_title(i.get('행정규칙명',''))==normalized_title(e['seed_name']) and i.get('소관부처명')=='법무부' and i.get('행정규칙종류')==e['category']]
                    if len(exact)!=1: raise ValueError('RETIRED_SERIAL_TITLE_REQUIRES_REVIEW')
                    stable,_=identifiers(exact[0],kind)
                    method='EXACT_UNIQUE_TITLE_MINISTRY_TYPE_FALLBACK'
                obj,ev=c.fetch('lawService.do',target=kind,LID=stable)
                repeal_evidence=None
                try: meta=unwrap(obj).get('행정규칙기본정보',{})
                except ValueError as err:
                    if str(err)!='EMPTY_API_RESULT' or old is None: raise
                    history,he=search(c,'admrul',query=old['metadata']['name'],nw=2)
                    history=[i for i in history if identifiers(i,kind)[0]==stable]
                    if not history: raise ValueError('MISSING_CURRENT_REQUIRES_REVIEW')
                    latest=sorted(history,key=lambda i:(i['발령일자'],i['행정규칙일련번호']),reverse=True)[0]
                    if latest.get('제개정구분명') not in ('폐지','타법폐지'): raise ValueError('NO_REPEAL_EVIDENCE_REVIEW')
                    _,repeal_serial=identifiers(latest,kind)
                    obj,ev=c.fetch('lawService.do',target=kind,ID=repeal_serial)
                    meta=unwrap(obj).get('행정규칙기본정보',{})
                    repeal_evidence={'canonical_id':kind+'-'+stable,'version_id':repeal_serial,'source':'OFFICIAL_HISTORY','history_evidence':he,'amendment_type':latest['제개정구분명']}
                serial=str(meta.get('행정규칙일련번호',''))
                current=snapshot(obj,kind,serial,ev)
                if current['stable_identifier']!=stable: raise ValueError('CANONICAL_ID_MISMATCH')
                if repeal_evidence:
                    if current['metadata']['amendment_type'] not in ('폐지','타법폐지'): raise ValueError('REPEAL_BODY_MISMATCH')
                    if current['metadata']['effective_date']>seoul_date().isoformat(): raise ValueError('FUTURE_REPEAL_REQUIRES_REVIEW')
                    current['repeal_evidence']=repeal_evidence
                    method='OFFICIAL_OUTGOING_ID_AND_EXPLICIT_REPEAL_HISTORY'
                elif current['metadata']['official_state']!='Y': raise ValueError('CURRENT_NOT_CONFIRMED')
                upcoming=[]
            else:
                title=unquote(urlparse(e['outgoing_url']).path).split('/')[2]
                html=public_page(e['outgoing_url'],metrics); soup=BeautifulSoup(html,'html.parser')
                iframe=soup.find('iframe',src=True)
                seq=parse_qs(urlparse(iframe['src'] if iframe else '').query).get('lsiSeq',[None])[0]
                if seq and seq.isdigit():
                    oo,oe=c.fetch('lawService.do',target='law',MST=seq)
                    old=snapshot(oo,kind,seq,oe); save_snapshot(old)
                    stable=old['stable_identifier']
                    items,evs=search(c,'eflaw',LID=stable,nw='2,3')
                    exact=[i for i in items if str(i.get('법령ID'))==stable]
                    method='OFFICIAL_OUTGOING_SERIAL_THEN_API_LID'
                else:
                    items,evs=search(c,'eflaw',query=title,nw='2,3')
                    exact=[i for i in items if normalized_title(i.get('법령명한글','')) in (normalized_title(title),normalized_title(e['seed_name']))]
                    method='OFFICIAL_OUTGOING_TITLE_EXACT_THEN_API_LID'
                ids={identifiers(i,kind)[0] for i in exact}
                if len(ids)!=1: raise ValueError('TITLE_IDENTITY_AMBIGUOUS')
                stable=next(iter(ids)); current_items=[i for i in exact if i.get('현행연혁코드')=='현행']
                if len(current_items)!=1: raise ValueError('CURRENT_VERSION_AMBIGUOUS')
                chosen=current_items[0]; _,serial=identifiers(chosen,kind)
                obj,ev=c.fetch('lawService.do',target='eflaw',MST=serial,efYd=chosen['시행일자'])
                current=snapshot(obj,kind,serial,ev)
                if current['stable_identifier']!=stable: raise ValueError('CANONICAL_ID_MISMATCH')
                upcoming=[]
                for i in exact:
                    if i.get('현행연혁코드')!='시행예정': continue
                    _,fs=identifiers(i,kind)
                    fo,fe=c.fetch('lawService.do',target='eflaw',MST=fs,efYd=i['시행일자'])
                    sn=snapshot(fo,kind,fs,fe); save_snapshot(sn); upcoming.append(sn)
            save_snapshot(current); cid=current['canonical_id']; snapshots[cid]=current; future[cid]=upcoming
            m=current['metadata']
            status='REPEALED' if 'repeal_evidence' in current else 'CURRENT'
            record.update({'status':'RESOLVED','current_name':m['name'],'canonical_id':cid,'resolution_method':method,'confidence':0.95 if 'FALLBACK' in method else 1.0,'rule_type':m['rule_type'],'current_status':status,'issue_or_promulgation_date':m['issue_date'],'effective_date':m['effective_date'],'ministry':m['ministry'],'department':m['department'] or e['department'],'official_detail_url':current['official_source_url'],'structured_body':bool(current['body']['articles']),'historical_name':old['metadata']['name'] if old else None})
            registry.append({'canonical_id':cid,'source_kind':kind,'seed_names':[e['seed_name']],'current_name':m['name'],'historical_names':list(dict.fromkeys([old['metadata']['name']] if old and old['metadata']['name']!=m['name'] else [])),'corrections_category':e['category'],'business_domains':[],'classification_status':'REVIEW','status':status,'law_or_rule_identifier':stable,'current_effective_date':m['effective_date'],'official_source':current['official_source_url'],'last_verified_at':now,'version_id':serial})
        except (ApiError,ValueError,KeyError,TypeError) as exc:
            record['review_reason']=exc.code if isinstance(exc,ApiError) else str(exc) if isinstance(exc,ValueError) else 'SCHEMA_MISMATCH'
        except Exception:
            record['review_reason']='INTERNAL_COLLECTION_ERROR'
        results.append(record)
        if not quiet: print(json.dumps({'progress':f'{index}/{len(seed)}','seed_name':e['seed_name'],'status':record['status'],'reason':record['review_reason']},ensure_ascii=False),flush=True)
        write_json('data/reports/resolution.json',{'collected_at':now,'counts':counts,'entries':results,'complete':index==len(seed)})
        write_json('data/staging/collection.json',{'collected_at':now,'registry':registry,'snapshots':snapshots,'future':future,'resolution':results,'complete':index==len(seed)})
    if not quiet: print('COLLECTION_COMPLETE',flush=True)
    return {'collected_at':now,'registry':registry,'snapshots':snapshots,'future':future,'resolution':results,'complete':True}

if __name__=='__main__':
    try: run()
    except ApiError as e: print(e.code); sys.exit(1)
    except Exception: print('COLLECTION_ABORTED'); sys.exit(1)

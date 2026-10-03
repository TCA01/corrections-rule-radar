"""Read-only structured Law API eligibility evidence. No HTML or file parsing."""
import json
import hashlib
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.law_api import LawClient,ApiError
from pipeline.registry import unwrap,as_list,identifiers,detail_url
from pipeline.normalize import snapshot,digest
from pipeline.snapshot import write_json
from pipeline.operations import now
from pipeline.operations.calendar import seoul_date
from pipeline.operations.metrics import Metrics

OUT=Path('data/reports/phase1d_evidence')

def fingerprint():
    result={}
    for name in ('data/registry','data/seed','data/snapshots','data/ops','public/api/v1','schemas','web/src','.github','firebase.json'):
        base=Path(name); paths=[base] if base.is_file() else base.rglob('*')
        for p in paths:
            if p.is_file(): result[str(p)]=[hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns]
    return result

class StatusOpener:
    def __init__(self,delegate): self.delegate=delegate; self.last_status=None
    def open(self,*args,**kwargs):
        response=self.delegate.open(*args,**kwargs)
        self.last_status=response.status
        return response

def request(c,endpoint='lawSearch.do',**params):
    payload,ev=c.fetch(endpoint,**params)
    ev={**ev,'endpoint':'https://www.law.go.kr/DRF/'+endpoint,'http_status':c.opener.last_status}
    return payload,ev

def search(c,target,**params):
    values=[]; evidence=[]
    for page in range(1,101):
        obj,ev=request(c,target=target,display=100,page=page,**params)
        root=unwrap(obj)
        if 'totalCnt' not in root: raise ValueError('LIST_SCHEMA_CHANGED')
        items=as_list(root.get('admrul' if target=='admrul' else 'law'))
        values+=items; evidence.append(ev)
        if len(values)>=int(root['totalCnt']): return values,evidence
        if not items: raise ValueError('PAGINATION_INCOMPLETE')
    raise ValueError('PAGINATION_LIMIT')

def one(c,row):
    cid=row['canonical_id']; kind=cid.split('-')[0]; stable=cid.split('-')[1]
    if kind=='law':
        items,ev=search(c,'eflaw',LID=stable,nw='2,3')
        exact=[i for i in items if identifiers(i,'law')[0]==stable]
        current=[i for i in exact if i.get('현행연혁코드')=='현행']
        if len(current)!=1: raise ValueError('CURRENT_VERSION_AMBIGUOUS')
        chosen=current[0]; _,serial=identifiers(chosen,'law')
        obj,evidence=request(c,'lawService.do',target='eflaw',MST=serial,efYd=chosen['시행일자'])
        future=[]
        for item in exact:
            if item.get('현행연혁코드')!='시행예정': continue
            _,version=identifiers(item,'law')
            payload,proof=request(c,'lawService.do',target='eflaw',MST=version,efYd=item['시행일자'])
            future.append(snapshot(payload,'law',version,proof))
        return {'payload':obj,'evidence':evidence,'serial':serial,'status':'CURRENT','resolution_method':'API_EFLAW_STABLE_LID_CURRENT_VERSION','resolution_evidence':ev,'future':future}
    payload,ev=request(c,'lawService.do',target='admrul',LID=stable)
    try:
        meta=unwrap(payload).get('행정규칙기본정보')
        if not isinstance(meta,dict): raise ValueError('METADATA_MISSING')
        if str(meta.get('행정규칙ID'))!=stable: raise ValueError('CANONICAL_ID_MISMATCH')
        if meta.get('현행여부')!='Y': raise ValueError('CURRENT_NOT_CONFIRMED')
        return {'payload':payload,'evidence':ev,'serial':str(meta['행정규칙일련번호']),'status':'FUTURE_EFFECTIVE' if meta['시행일자']>seoul_date().strftime('%Y%m%d') else 'CURRENT','resolution_method':'API_ADMRUL_STABLE_LID','resolution_evidence':[ev],'future':[]}
    except ValueError as exc:
        if str(exc)!='EMPTY_API_RESULT': raise
    history,he=search(c,'admrul',query=row.get('current_name') or row['name'],nw=2)
    matches=[i for i in history if identifiers(i,'admrul')[0]==stable]
    if not matches: raise ValueError('MISSING_CURRENT_AND_HISTORY')
    latest=max(matches,key=lambda i:(i['발령일자'],i['행정규칙일련번호']))
    if latest.get('제개정구분명') not in ('폐지','타법폐지'): raise ValueError('MISSING_CURRENT_WITHOUT_EXPLICIT_REPEAL')
    _,serial=identifiers(latest,'admrul')
    obj,evidence=request(c,'lawService.do',target='admrul',ID=serial)
    meta=unwrap(obj)['행정규칙기본정보']
    if str(meta['행정규칙ID'])!=stable or meta.get('제개정구분명') not in ('폐지','타법폐지'): raise ValueError('REPEAL_BODY_MISMATCH')
    if meta['시행일자']>seoul_date().strftime('%Y%m%d'): raise ValueError('FUTURE_REPEAL_REQUIRES_REVIEW')
    proof={'canonical_id':cid,'version_id':serial,'source':'OFFICIAL_HISTORY','amendment_type':latest['제개정구분명'],'history_evidence':he}
    return {'payload':obj,'evidence':evidence,'serial':serial,'status':'REPEALED','resolution_method':'API_EMPTY_CURRENT_THEN_EXPLICIT_REPEAL_HISTORY','resolution_evidence':[ev,*he],'repeal_evidence':proof,'history_items':matches,'future':[]}

def assess(first,second,kind,cid):
    root=unwrap(first['payload']); meta=root.get('행정규칙기본정보' if kind=='admrul' else '기본정보',{})
    body=root.get('조문내용' if kind=='admrul' else '조문')
    record={'canonical_id':cid,'current_metadata':meta,'current_status':first['status'],'effective_date':meta.get('시행일자'),'body_available':bool(body),'response_format_tested':list(dict.fromkeys([first['evidence']['request']['type'],second['evidence']['request']['type']])),'detail_query':first['evidence']['request'],'api_detail_endpoint':first['evidence']['endpoint'],'api_resolution_method':first['resolution_method'],'stable_api_identifier':cid.split('-')[1],'api_evidence':[first['evidence'],second['evidence']],'resolution_evidence':first['resolution_evidence'],'appendix_metadata_available':'별표' in root,'attachment_metadata_available':'첨부파일' in root,'appendix_policy':'본문·상태는 구조화 API, 첨부는 공식 메타데이터·링크만 비교; 파일 의미 분석 없음','future_effective_capability':{'type':'API_EFLAW_CURRENT_AND_FUTURE' if kind=='law' else 'ISSUE_EFFECTIVE_METADATA_ONLY','dedicated_future_version_enumeration':kind=='law','future_versions':first['future'],'admin_limitation':'별도 시행예정 목록 보장 없음. 안정 ID 현행 응답의 시행일을 비교할 수 있으나 현행 응답이 미래 버전만 반환하면 이전 현행은 history에서 검증하는 수집기 보완 필요.' if kind=='admrul' else None},'eligibility_result':'REVIEW','failure_reason':None,'snapshot_viable':False,'change_detection_viable':False,'repeat_deterministic':False,'production_eligible':False}
    try:
        baseline=snapshot(first['payload'],kind,first['serial'],first['evidence'])
        repeat=snapshot(second['payload'],kind,second['serial'],second['evidence'])
        if baseline['canonical_id']!=cid or repeat['canonical_id']!=cid: raise ValueError('CANONICAL_ID_MISMATCH')
        if first['status']!=second['status'] or baseline['version_id']!=repeat['version_id'] or baseline['hashes']!=repeat['hashes']: raise ValueError('REPEAT_RESPONSE_CHANGED_REVIEW')
        if not baseline['metadata']['issue_date']: raise ValueError('ISSUE_DATE_MISSING')
        if first['status']=='REPEALED':
            baseline['repeal_evidence']=first['repeal_evidence']; repeat['repeal_evidence']=second['repeal_evidence']
        record.update({'eligibility_result':'API_TRACKABLE','snapshot_viable':True,'change_detection_viable':True,'repeat_deterministic':True,'snapshot':baseline,'repeat_snapshot':repeat,'repeal_evidence':first.get('repeal_evidence'),'api_only_state_sustainable':True})
    except (ValueError,TypeError,KeyError) as exc:
        reason=str(exc) if isinstance(exc,ValueError) else 'NORMALIZER_SHAPE_REVIEW'
        record['failure_reason']=reason
        record['body_available']=bool(body) and reason!='STRUCTURED_BODY_MISSING'
        record['eligibility_result']='API_TRACKABLE_LIMITED' if reason in ('STRUCTURED_BODY_MISSING','METADATA_INCOMPLETE','ISSUE_DATE_MISSING') else 'REVIEW'
        record['repeat_deterministic']=digest(first['payload'])==digest(second['payload'])
    return record

def audit(c,row,group):
    cid=row['canonical_id']; kind=cid.split('-')[0]
    base={'canonical_id':cid,'candidate_name':row.get('current_name') or row['name'],'scope_class':row.get('scope_class') or row.get('scope_class_candidate'),'group':group,'scope_pass':row.get('scope_class',row.get('scope_class_candidate')) not in ('REVIEW','NOT_CORRECTIONS'),'production_eligible':False}
    try:
        first=one(c,row); second=one(c,row); result={**base,**assess(first,second,kind,cid)}
        if kind=='admrul':
            items,ev=search(c,'admrul',query=result['current_metadata'].get('행정규칙명',base['candidate_name']),nw=2)
            history=[i for i in items if identifiers(i,'admrul')[0]==cid.split('-')[1]]
            result['history_availability']={'available':bool(history),'version_count':len(history),'items':history,'evidence':ev}
        else: result['history_availability']={'available':None,'note':'이번 감사는 현행·시행예정 API와 정규화 스냅샷을 검증. 법령 과거 목록은 필수 자격 요건이 아니므로 재조회하지 않음.'}
        result['source_ministry']=result['current_metadata'].get('소관부처명',result['current_metadata'].get('소관부처'))
        result['rule_type']=result['current_metadata'].get('행정규칙종류',result['current_metadata'].get('법종구분'))
        if not base['scope_pass']: result['api_capability_class']=result['eligibility_result']; result['eligibility_result']='REVIEW'
        result['production_eligible']=base['scope_pass'] and result['eligibility_result']=='API_TRACKABLE'
        result['production_decision']='PRODUCTION_ELIGIBLE' if result['production_eligible'] else 'PRODUCTION_INELIGIBLE'
        return result
    except (ApiError,ValueError,TypeError,KeyError) as exc:
        reason=exc.code if isinstance(exc,ApiError) else str(exc) if isinstance(exc,ValueError) else 'SCHEMA_REVIEW'
        return {**base,'eligibility_result':'API_UNAVAILABLE' if reason in ('MISSING_CURRENT_AND_HISTORY','EMPTY_API_RESULT') else 'REVIEW','failure_reason':reason,'production_decision':'PRODUCTION_INELIGIBLE'}

def main():
    OUT.mkdir(parents=True,exist_ok=True); before=fingerprint(); write_json(OUT/'production_before.json',before)
    phase1c=json.loads(Path('data/reports/phase1c_scope_audit.json').read_text(encoding='utf-8'))
    additions=set(phase1c['recommended_production_core']['add_after_review'])
    groups=[('CURRENT_68',phase1c['current_records']),('NEW_39',[c for c in phase1c['discovery_candidates'] if c['canonical_id'] in additions]),('OTHER_DISCOVERY',[c for c in phase1c['discovery_candidates'] if c['canonical_id'] not in additions])]
    metrics=Metrics(); c=LawClient(cache='data/raw_cache/phase1d',metrics=metrics); c.opener=StatusOpener(c.opener)
    records=[]; start=time.monotonic(); at=now()
    for group,rows in groups:
        for index,row in enumerate(rows,1):
            result=audit(c,row,group); records.append(result)
            write_json(OUT/'records.json',records)
            print(group+' '+str(index)+'/'+str(len(rows))+' '+row['canonical_id']+' '+result['eligibility_result'],flush=True)
    queries={}
    for title in ('교정직제 영어 명칭','교정공무원 예절','교정공무원 행동','국가공무원 복무','국가공무원 복무·징계 관련 예규','국가공무원 인사운영처리지침','국가공무원 인사운영','공무원 인사운영처리지침'):
        for nw in (1,2):
            items,ev=search(c,'admrul',query=title,nw=nw)
            queries[title+'/'+str(nw)]={'items':items,'evidence':ev}
    write_json(OUT/'lineage_searches.json',queries)
    details={}
    # Recent and oldest versions establish official stable-ID continuity; no
    # inference from similar titles. Inspect successor and special-check text.
    special=[r for r in records if r['canonical_id'] in ('admrul-26424','admrul-26917','admrul-30248','admrul-84831')]
    for row in special:
        items=row.get('history_availability',{}).get('items',[])
        ordered=sorted(items,key=lambda i:(i['발령일자'],i['행정규칙일련번호']))
        for item in ordered[:1]+ordered[-2:]:
            stable,serial=identifiers(item,'admrul')
            if serial in details: continue
            payload,ev=request(c,'lawService.do',target='admrul',ID=serial)
            details[serial]={'canonical_id':'admrul-'+stable,'payload':payload,'evidence':ev}
    write_json(OUT/'lineage_details.json',details)
    after=fingerprint(); write_json(OUT/'integrity.json',{'started_at':at,'finished_at':now(),'duration_seconds':round(time.monotonic()-start,3),'metrics':metrics.report(),'production_unchanged':before==after,'changed_paths':sorted(p for p in set(before)|set(after) if before.get(p)!=after.get(p))})
    print('STRUCTURED_API_AUDIT_COMPLETE',flush=True)
    if before!=after: raise ValueError('PROTECTED_FILES_CHANGED')

def supplement_lineage():
    before=fingerprint(); metrics=Metrics(); c=LawClient(cache='data/raw_cache/phase1d',metrics=metrics); c.opener=StatusOpener(c.opener)
    result={'reason':'폐지 26424 상세 API의 폐지이유에서 명시적으로 언급된 정부조직 영어명칭 규칙을 확인; 유사 제목 임의 추정이 아님.','queries':[],'records':[]}
    title='정부조직 영어명칭에 관한 규칙'
    for nw in (1,2):
        items,ev=search(c,'admrul',query=title,nw=nw)
        result['queries'].append({'title':title,'nw':nw,'items':items,'evidence':ev})
    referenced_ids={str(item['행정규칙ID']) for q in result['queries'] if q['nw']==2 for item in q['items'] if item['행정규칙명'].replace(' ','')==title.replace(' ','') and item['발령번호']=='40'}
    for q in result['queries']:
        for item in q['items']:
            if str(item['행정규칙ID']) not in referenced_ids: continue
            if q['nw']==2 and item['발령번호']!='40': continue
            stable,serial=identifiers(item,'admrul')
            obj,proof=request(c,'lawService.do',target='admrul',ID=serial)
            result['records'].append({'canonical_id':'admrul-'+stable,'list_item':item,'payload':obj,'evidence':proof})
    result['production_unchanged']=before==fingerprint(); result['metrics']=metrics.report()
    write_json(OUT/'lineage_supplement.json',result)
    print('EXPLICIT_REPEAL_REFERENCE_CHECKED',flush=True)
    if before!=fingerprint(): raise ValueError('PROTECTED_FILES_CHANGED')

if __name__=='__main__':
    supplement_lineage() if '--lineage-supplement' in sys.argv else main()

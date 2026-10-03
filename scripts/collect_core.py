"""Sync trusted stable IDs. Discovery is separate; missing identity fails closed."""
import copy
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.law_api import LawClient,ApiError
from pipeline.registry import unwrap,identifiers
from pipeline.normalize import snapshot
from pipeline.snapshot import write_json,save_snapshot
from pipeline.operations import now
from pipeline.operations.calendar import seoul_date
from pipeline.law_api.search import search

ROOT=Path(__file__).resolve().parents[1]
def run(*,metrics=None,quiet=False,state=None,trusted=None,output='data/staging/collection.json'):
    state=state or json.loads((ROOT/'data/registry/state.json').read_text(encoding='utf-8'))
    trusted=trusted or json.loads((ROOT/'data/registry/rules.json').read_text(encoding='utf-8'))
    if set(state['seed_ids'])!=set(r['canonical_id'] for r in trusted): raise ValueError('TRUSTED_REGISTRY_INCOMPLETE')
    client=LawClient(metrics=metrics); at=now(); snapshots={}; future={}; rows=[]; resolution=[]
    for row in trusted:
        cid=row['canonical_id']; stable=state['snapshots'][cid]['stable_identifier']; kind=row['source_kind']
        record={'canonical_id':cid,'seed_name':row['seed_names'][0] if row['seed_names'] else None,'status':'REVIEW','review_reason':None,'resolution_method':'TRUSTED_STABLE_ID'}
        try:
            upcoming=[]; repeal=None
            if kind=='law':
                items,_=search(client,'eflaw',LID=stable,nw='2,3')
                exact=[i for i in items if identifiers(i,kind)[0]==stable]
                current=[i for i in exact if i.get('현행연혁코드')=='현행']
                if len(current)!=1: raise ValueError('CURRENT_VERSION_AMBIGUOUS')
                chosen=current[0]; _,serial=identifiers(chosen,kind)
                payload,ev=client.fetch('lawService.do',target='eflaw',MST=serial,efYd=chosen['시행일자'])
                value=snapshot(payload,kind,serial,ev)
                for item in exact:
                    if item.get('현행연혁코드')!='시행예정': continue
                    _,version=identifiers(item,kind)
                    body,evidence=client.fetch('lawService.do',target='eflaw',MST=version,efYd=item['시행일자'])
                    sn=snapshot(body,kind,version,evidence)
                    if sn['canonical_id']!=cid: raise ValueError('CANONICAL_ID_MISMATCH')
                    upcoming.append(sn); save_snapshot(sn)
            else:
                # Explicitly repealed identities remain checked against official
                # history. Never treat an empty LID response as proof of repeal.
                if row['status']=='REPEALED': payload=None
                else:
                    payload,ev=client.fetch('lawService.do',target='admrul',LID=stable)
                    try: unwrap(payload)
                    except ValueError as exc:
                        if str(exc)!='EMPTY_API_RESULT': raise
                        payload=None
                if payload is None:
                    history,he=search(client,'admrul',query=row['current_name'],nw=2)
                    exact=[i for i in history if identifiers(i,kind)[0]==stable]
                    if not exact: raise ValueError('MISSING_CURRENT_REQUIRES_REVIEW')
                    latest=max(exact,key=lambda i:(i['발령일자'],i['행정규칙일련번호']))
                    _,serial=identifiers(latest,kind)
                    payload,ev=client.fetch('lawService.do',target=kind,ID=serial)
                    if latest.get('제개정구분명') in ('폐지','타법폐지'):
                        repeal={'canonical_id':cid,'version_id':serial,'source':'OFFICIAL_HISTORY','history_evidence':he,'amendment_type':latest['제개정구분명']}
                else: serial=str(unwrap(payload).get('행정규칙기본정보',{}).get('행정규칙일련번호',''))
                value=snapshot(payload,kind,serial,ev)
                if repeal:
                    if value['metadata']['amendment_type'] not in ('폐지','타법폐지') or value['metadata']['effective_date']>seoul_date().isoformat(): raise ValueError('REPEAL_BODY_MISMATCH')
                    value['repeal_evidence']=repeal
                elif value['metadata']['official_state']!='Y': raise ValueError('CURRENT_NOT_CONFIRMED')
                if value['metadata']['effective_date']>seoul_date().isoformat():
                    # Some administrative LID responses expose the next version
                    # as Y. Establish today's operative predecessor by exact-ID
                    # history, never by a manually maintained effective date.
                    upcoming.append(value); save_snapshot(value)
                    items=[]
                    for title in dict.fromkeys([row['current_name'],value['metadata']['name']]):
                        found,_=search(client,'admrul',query=title,nw=2); items+=found
                    from pipeline.normalize import date
                    past=[i for i in items if identifiers(i,kind)[0]==stable and date(i.get('시행일자')) and date(i['시행일자'])<=seoul_date().isoformat()]
                    if not past: raise ValueError('ADMIN_FUTURE_PREDECESSOR_UNAVAILABLE')
                    chosen=max(past,key=lambda i:(date(i['시행일자']),i['발령일자'],i['행정규칙일련번호']))
                    _,serial=identifiers(chosen,kind)
                    payload,ev=client.fetch('lawService.do',target='admrul',ID=serial)
                    value=snapshot(payload,kind,serial,ev)
                    if value['metadata']['effective_date']!=date(chosen['시행일자']) or value['metadata']['amendment_type'] in ('폐지','타법폐지'): raise ValueError('ADMIN_FUTURE_PREDECESSOR_REQUIRES_REVIEW')
            if value['canonical_id']!=cid: raise ValueError('CANONICAL_ID_MISMATCH')
            if value['metadata']['effective_date']>seoul_date().isoformat(): raise ValueError('CURRENT_DATE_IN_FUTURE')
            save_snapshot(value); snapshots[cid]=value; future[cid]=upcoming
            updated=copy.deepcopy(row); updated.update({'current_name':value['metadata']['name'],'status':'REPEALED' if repeal else 'CURRENT','current_effective_date':value['metadata']['effective_date'],'version_id':value['version_id'],'last_verified_at':at,'official_source':value['official_source_url']})
            if row['current_name']!=value['metadata']['name'] and row['current_name'] not in updated['historical_names']: updated['historical_names'].append(row['current_name'])
            if 'provenance' in updated: updated['provenance']['canonical_source_url']=value['official_source_url']
            rows.append(updated)
            record.update({'status':'RESOLVED','current_name':value['metadata']['name']})
        except (ApiError,ValueError,KeyError,TypeError) as exc:
            record['review_reason']=exc.code if isinstance(exc,ApiError) else str(exc) if isinstance(exc,ValueError) else 'SCHEMA_MISMATCH'
            if isinstance(exc,ApiError) and exc.code in ('AUTHENTICATION_ERROR','WAITING_FOR_LAW_API_OC'): raise
        resolution.append(record)
    collection={'complete':True,'collected_at':at,'registry':rows,'snapshots':snapshots,'future':future,'resolution':resolution}
    write_json(ROOT/'data/reports/core_resolution.json',{'entries':resolution,'complete':True,'collected_at':at})
    write_json(ROOT/output,collection)
    return collection

"""Read-only live history preparation for the trusted production registry."""
import json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.law_api import LawClient,ApiError
from pipeline.law_api.search import search
from pipeline.registry import identifiers,unwrap
from pipeline.normalize import snapshot,date
from pipeline.operations import now
from pipeline.operations.calendar import seoul_date
from pipeline.operations.metrics import Metrics
from pipeline.snapshot import write_json
from datetime import timedelta

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/staging/phase1e_backfill.json'

def run(*,state=None,rows=None,output=OUT,report='data/reports/phase1e_backfill.json',cache_name='phase1e'):
    state=state or json.loads((ROOT/'data/registry/state.json').read_text(encoding='utf8'))
    rows=rows or json.loads((ROOT/'data/registry/rules.json').read_text(encoding='utf8'))
    if not {r['canonical_id'] for r in rows}<=set(state['seed_ids']): raise ValueError('CORE_SCOPE_MISMATCH')
    metrics=Metrics(); client=LawClient(cache=ROOT/'data/raw_cache'/cache_name,metrics=metrics)
    start=time.monotonic(); at=now(); cutoff=(seoul_date()-timedelta(days=89)).isoformat()
    frozen=list(state['snapshots'].values())+[s for vs in state['future'].values() for s in vs]
    frozen+=[json.loads(p.read_text(encoding='utf8')) for p in (ROOT/'data/snapshots').rglob('*.json')]
    cache={}
    for s in frozen: cache.setdefault((s['canonical_id'],s['version_id'],s['metadata']['effective_date']),s)
    result={'started_at':at,'cutoff':cutoff,'records':[],'snapshots':[],'pairs':[]}
    for row in rows:
        cid=row['canonical_id']; kind=row['source_kind']; stable=cid.split('-')[1]
        record={'canonical_id':cid,'status':'PASS','failures':[]}
        try:
            if kind=='law': items,ev=search(client,'eflaw',LID=stable,nw='1,2,3')
            else:
                items=[]; ev=[]
                for name in dict.fromkeys([row['current_name']]+row['historical_names']):
                    found,proof=search(client,'admrul',query=name,nw=2); items+=found; ev+=proof
            exact=[i for i in items if identifiers(i,kind)[0]==stable]
            record.update({'history_items':exact,'list_evidence':ev})
            versions={}
            for i in exact:
                _,serial=identifiers(i,kind); effective=date(i.get('시행일자'))
                if effective: versions[(serial,effective)]=i
            for s in [state['snapshots'][cid]]+state['future'].get(cid,[]):
                versions[(s['version_id'],s['metadata']['effective_date'])]=None
            ordered=sorted(versions,key=lambda k:(k[1],str((versions[k] or {}).get('공포일자',(versions[k] or {}).get('발령일자',''))),int(k[0])))
            selected=[i for i,k in enumerate(ordered) if k[1]>=cutoff]
            # Retain the most recent earlier change as well; never a retention cap.
            older=[i for i,k in enumerate(ordered) if k[1]<cutoff]
            if older: selected.append(older[-1])
            needed=set(selected)|{i-1 for i in selected if i>0}
            resolved={}
            for i in sorted(needed):
                serial,effective=ordered[i]; key=(cid,serial,effective)
                try:
                    if key in cache: sn=cache[key]
                    else:
                        params={'target':'eflaw','MST':serial,'efYd':effective.replace('-','')} if kind=='law' else {'target':'admrul','ID':serial}
                        payload,proof=client.fetch('lawService.do',**params); sn=snapshot(payload,kind,serial,proof)
                    if sn['canonical_id']!=cid or sn['metadata']['effective_date']!=effective: raise ValueError('HISTORY_VERSION_IDENTITY_MISMATCH')
                    resolved[i]=sn; result['snapshots'].append(sn)
                except (ApiError,ValueError,KeyError,TypeError) as exc:
                    record['failures'].append({'version_id':serial,'code':exc.code if isinstance(exc,ApiError) else 'HISTORY_BODY_UNAVAILABLE'})
            for i in sorted(set(selected)):
                if i not in resolved: continue
                new=resolved[i]; old=resolved.get(i-1); payload=None; proof=None; reason=None
                try:
                    params={'target':'oldAndNew','MST':new['version_id']} if kind=='law' else {'target':'admrulOldAndNew','ID':new['version_id']}
                    payload,proof=client.fetch('lawService.do',**params)
                except (ApiError,ValueError): reason='OFFICIAL_COMPARISON_UNAVAILABLE'
                result['pairs'].append({'before':old,'after':new,'official_comparison':payload,'comparison_evidence':proof,'comparison_failure':reason})
            if record['failures']: record['status']='PARTIAL'
        except (ApiError,ValueError,KeyError,TypeError) as exc:
            record['status']='REVIEW'; record['failures'].append({'code':exc.code if isinstance(exc,ApiError) else 'HISTORY_LIST_UNAVAILABLE'})
        result['records'].append(record)
        result.update({'finished_at':now(),'duration_seconds':round(time.monotonic()-start,3),'metrics':metrics.report()})
        write_json(output,result)
        print(cid+' '+record['status']+' pairs='+str(len(result['pairs'])),flush=True)
    write_json(ROOT/report,{k:v for k,v in result.items() if k not in ('snapshots','pairs')})
    return result

if __name__=='__main__': run()

"""Sunday independent list/detail identity cross-check for all approved IDs."""
from pipeline.law_api import LawClient
from pipeline.law_api.search import search
from pipeline.registry import identifiers
from pipeline.normalize import date

def revalidate(collection,*,metrics=None):
    client=LawClient(metrics=metrics); results=[]
    for row in collection['registry']:
        cid=row['canonical_id']; kind=row['source_kind']; sn=collection['snapshots'][cid]
        if kind=='law': items,ev=search(client,'eflaw',LID=sn['stable_identifier'],nw='1,2,3')
        else: items,ev=search(client,'admrul',query=sn['metadata']['name'],nw=2 if row['status']=='REPEALED' or sn['metadata']['official_state']!='Y' else 1)
        exact=[i for i in items if identifiers(i,kind)==(sn['stable_identifier'],sn['version_id']) and date(i.get('시행일자'))==sn['metadata']['effective_date']]
        if not exact: raise ValueError('FULL_ID_REVALIDATION_FAILED')
        results.append({'canonical_id':cid,'version_id':sn['version_id'],'status':'PASS','evidence':ev})
    return results

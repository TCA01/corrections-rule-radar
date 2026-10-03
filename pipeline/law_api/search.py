"""Paginated structured API lists; no document or HTML processing."""
from pipeline.registry import unwrap,as_list

def search(client,target,**params):
    values=[]; evidence=[]
    for page in range(1,101):
        payload,ev=client.fetch(target=target,display=100,page=page,**params)
        root=unwrap(payload)
        if 'totalCnt' not in root: raise ValueError('LIST_SCHEMA_CHANGED')
        items=as_list(root.get('admrul' if target=='admrul' else 'law'))
        values+=items; evidence.append(ev)
        if len(values)>=int(root['totalCnt']): return values,evidence
        if not items: raise ValueError('PAGINATION_INCOMPLETE')
    raise ValueError('PAGINATION_LIMIT')

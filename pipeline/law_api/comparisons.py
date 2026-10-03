"""Fetch comparisons once for newly observed version pairs only."""
from pipeline.law_api import LawClient,ApiError

def prepare(collection,state,persisted,*,metrics=None):
    if not state or not collection.get('complete') or len(collection['registry'])!=len(state['seed_ids']): return
    known={(e['canonical_id'],e['after_version']['identifier'],e['after_version']['effective_date'],e['after_version']['body_hash']) for e in persisted}
    pairs=[]; client=None
    for cid,current in collection['snapshots'].items():
        old=state['snapshots'].get(cid)
        for new in [current]+collection['future'].get(cid,[]):
            key=(cid,new['version_id'],new['metadata']['effective_date'],new['hashes']['body_hash'])
            if key in known or not old or old['version_id']==new['version_id']: continue
            client=client or LawClient(metrics=metrics)
            params={'target':'oldAndNew','MST':new['version_id']} if new['source_kind']=='law' else {'target':'admrulOldAndNew','ID':new['version_id']}
            try: payload,ev=client.fetch('lawService.do',**params)
            except (ApiError,ValueError): payload=None; ev=None
            pairs.append({'before':old,'after':new,'official_comparison':payload,'comparison_evidence':ev})
    if pairs: collection['history_backfill']={'snapshots':[],'pairs':pairs}

"""Fetch comparisons once for newly observed version pairs only."""
from pipeline.law_api import LawClient,ApiError
from pipeline.diff.effective_states import future_pairs

def prepare(collection,state,persisted,*,metrics=None):
    if not state or not collection.get('complete') or len(collection['registry'])!=len(state['seed_ids']): return
    def key(s): return (s['canonical_id'],s['version_id'],s['metadata']['effective_date'],s['hashes']['body_hash'])
    def refkey(cid,r): return (cid,r['identifier'],r['effective_date'],r['body_hash']) if r else None
    known={(refkey(e['canonical_id'],e['before_version']),refkey(e['canonical_id'],e['after_version'])) for e in persisted}
    known_after={refkey(e['canonical_id'],e['after_version']) for e in persisted}
    pairs=[]; client=None
    for cid,current in collection['snapshots'].items():
        old=state['snapshots'].get(cid)
        targets=([(old,current)] if key(current) not in known_after else [])+future_pairs(current,collection['future'].get(cid,[]))
        for old,new in targets:
            if not old or (key(old),key(new)) in known or old['version_id']==new['version_id']: continue
            client=client or LawClient(metrics=metrics)
            params={'target':'oldAndNew','MST':new['version_id']} if new['source_kind']=='law' else {'target':'admrulOldAndNew','ID':new['version_id']}
            try: payload,ev=client.fetch('lawService.do',**params)
            except (ApiError,ValueError): payload=None; ev=None
            pairs.append({'before':old,'after':new,'official_comparison':payload,'comparison_evidence':ev})
    if pairs: collection['history_backfill']={'snapshots':[],'pairs':pairs}

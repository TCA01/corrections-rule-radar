"""Content-addressed official versions and resolvable event references."""
from pipeline.normalize import digest
from pipeline.diff.articles import changed_articles

def key(s):
    return s['version_id']+'-'+s['metadata']['effective_date']+'-'+digest(s['hashes'])[:16]

def url(s): return '/api/v1/rules/'+s['canonical_id']+'/versions/'+key(s)+'.json'

def reference(s):
    return {'version_id':s['version_id'],'effective_date':s['metadata']['effective_date'],'snapshot_url':url(s),'official_source_url':s['official_source_url']}

def index_snapshots(collection,history):
    values=list(collection['snapshots'].values())+[s for vs in collection['future'].values() for s in vs]+history
    return {(s['canonical_id'],s['version_id'],digest(s['hashes'])):s for s in values}

def enrich_event(event,index,current=None,*,effective_baseline=None):
    result=dict(event)
    new=index.get((event['canonical_id'],event['new_version'],digest(event['new_hashes'])))
    old=index.get((event['canonical_id'],event['old_version'],digest(event['old_hashes']))) if event['old_version'] else None
    if not new or (event['old_version'] and not old): raise ValueError('EVENT_VERSION_REFERENCE_MISSING')
    result.update({'old_reference':reference(old) if old else None,'new_reference':reference(new)})
    # A baseline future event has no observed old version. Compare against the
    # actual current baseline and disclose that comparison separately.
    existing=event.get('articles_compared_to')
    retained=next((v for v in index.values() if url(v)==existing['snapshot_url']),None) if existing else None
    if existing and retained is None: raise ValueError('EVENT_COMPARISON_REFERENCE_MISSING')
    comparison=effective_baseline or retained or old or (current if event['change_type']=='FUTURE_EFFECTIVE_VERSION' else None)
    from pipeline.diff.effective_states import display_articles
    articles=display_articles(comparison,new) if effective_baseline else event['changed_articles'] if retained is not None and 'changed_articles' in event else changed_articles(comparison,new)
    result.update({'changed_articles':articles,'articles_compared_to':reference(comparison) if comparison else None})
    return result

"""Deterministic observed changes. No legal interpretation or inferred repeal."""
from pipeline.normalize import digest

EVENT_TYPES=('NEW_RULE','RULE_RENAMED','RULE_AMENDED','FUTURE_EFFECTIVE_VERSION','EFFECTIVE_DATE_CHANGED','ARTICLE_CHANGED','APPENDIX_CHANGED','ATTACHMENT_CHANGED','RULE_REPEALED','RULE_REMOVED_FROM_CORRECTIONS_SEED','NEW_CORRECTIONS_SEED','DISCOVERY_CANDIDATE')

def event(kind,old,new,detected_at,evidence=None):
    identity={'canonical_id':new['canonical_id'],'change_type':kind,'old_version':old['version_id'] if old else None,'new_version':new['version_id'],'effective_date':new['metadata']['effective_date'],'old_hashes':old['hashes'] if old else None,'new_hashes':new['hashes'],'evidence':evidence or {'old_hashes':old['hashes'] if old else None,'new_hashes':new['hashes']}}
    return {**identity,'event_id':'evt-'+digest(identity),'detected_at':detected_at,'official_source_url':new['official_source_url']}

def compare(old,new,detected_at,*,repeal_evidence=None):
    if old and old['canonical_id']!=new['canonical_id']: raise ValueError('DIFF_IDENTITY_MISMATCH')
    if old is None: return [event('NEW_RULE',None,new,detected_at)]
    kinds=[]
    if old['metadata']['name']!=new['metadata']['name']: kinds.append('RULE_RENAMED')
    if old['metadata']['effective_date']!=new['metadata']['effective_date']: kinds.append('EFFECTIVE_DATE_CHANGED')
    if old['version_id']!=new['version_id']: kinds.append('RULE_AMENDED')
    if old['hashes']['body_hash']!=new['hashes']['body_hash']: kinds.append('ARTICLE_CHANGED')
    if old['hashes']['appendix_hash']!=new['hashes']['appendix_hash']: kinds.append('APPENDIX_CHANGED')
    if old['hashes']['attachment_link_hash']!=new['hashes']['attachment_link_hash']: kinds.append('ATTACHMENT_CHANGED')
    # Only explicit official repeal metadata, linked to this identity/version.
    if new['metadata'].get('amendment_type') in ('폐지','타법폐지'):
        if not repeal_evidence or repeal_evidence.get('canonical_id')!=new['canonical_id'] or repeal_evidence.get('version_id')!=new['version_id'] or repeal_evidence.get('source')!='OFFICIAL_HISTORY':
            raise ValueError('REPEAL_REQUIRES_REVIEW')
        if old['metadata'].get('amendment_type') not in ('폐지','타법폐지') or old['version_id']!=new['version_id']:
            kinds.append('RULE_REPEALED')
    return [event(k,old,new,detected_at,repeal_evidence if k=='RULE_REPEALED' else None) for k in kinds]

def future_events(old_versions,new_versions,detected_at):
    known={digest({'id':s['version_id'],'effective_date':s['metadata']['effective_date'],'hashes':s['hashes']}) for s in old_versions}
    return [event('FUTURE_EFFECTIVE_VERSION',None,s,detected_at) for s in new_versions if digest({'id':s['version_id'],'effective_date':s['metadata']['effective_date'],'hashes':s['hashes']}) not in known]

def seed_events(old_ids,new_ids,snapshots,detected_at):
    events=[]
    for cid in sorted(set(new_ids)-set(old_ids)):
        if cid in snapshots: events.append(event('NEW_CORRECTIONS_SEED',None,snapshots[cid],detected_at))
    for cid in sorted(set(old_ids)-set(new_ids)):
        if cid in snapshots: events.append(event('RULE_REMOVED_FROM_CORRECTIONS_SEED',None,snapshots[cid],detected_at))
    return events

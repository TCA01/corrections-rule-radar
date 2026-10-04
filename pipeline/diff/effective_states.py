"""Canonical future chains and deterministic, full-body effective-state diffs."""
import re
from pipeline.registry import as_list

def state_key(s):
    return (s['canonical_id'],s['version_id'],s['metadata']['effective_date'])

def future_pairs(current,future):
    """Current is authoritative even when an archive shares its effective date."""
    unique={}
    dates={}
    for s in future:
        if s['canonical_id']!=current['canonical_id']: raise ValueError('FUTURE_IDENTITY_MISMATCH')
        day=s['metadata']['effective_date']
        if not day or day<=current['metadata']['effective_date']: raise ValueError('FUTURE_DATE_NOT_AFTER_CURRENT')
        key=state_key(s)
        if key in unique and unique[key]['hashes']!=s['hashes']: raise ValueError('AMBIGUOUS_EFFECTIVE_STATE')
        if day in dates and dates[day]!=key: raise ValueError('AMBIGUOUS_FUTURE_EFFECTIVE_DATE')
        unique[key]=s; dates[day]=key
    previous=current; pairs=[]
    for s in sorted(unique.values(),key=lambda v:v['metadata']['effective_date']):
        pairs.append((previous,s)); previous=s
    return pairs

def full_articles(before,after):
    from pipeline.diff.history import article_groups,article_diff
    result=article_diff(article_groups(before['body']),article_groups(after['body']),after['metadata']['effective_date'])
    if result is None: raise ValueError('UPCOMING_STRUCTURED_COMPARISON_UNAVAILABLE')
    return result

def display_articles(before,after):
    return [{**a,'change_type':{'REMOVED':'DELETED','RENAMED':'MODIFIED'}.get(a['change_type'],a['change_type'])} for a in full_articles(before,after)]

def staged_evidence(before,after):
    """Require same promulgation, changed articles and a dated commencement clause.

    A changed effective-date field alone remains a correction. No law IDs or
    target dates are encoded here; proof comes from the API's addendum structure.
    """
    if not before or before['version_id']!=after['version_id'] or before['metadata']['effective_date']>=after['metadata']['effective_date']: return None
    if before['metadata']['issue_date']!=after['metadata']['issue_date']: return None
    try:
        articles=full_articles(before,after)
        if not articles: return None
    except (ValueError,KeyError,TypeError): return None
    def strings(value):
        if isinstance(value,str): yield value
        elif isinstance(value,list):
            for item in value: yield from strings(item)
    addenda=after['body'].get('addenda')
    if not isinstance(addenda,dict): return None
    for entry in as_list(addenda.get('부칙단위')):
        if not isinstance(entry,dict) or str(entry.get('부칙공포번호'))!=str(after['metadata']['issue_number']): continue
        text='\n'.join(strings(entry.get('부칙내용')))
        commencement=re.split(r'제\s*2\s*조\s*\(',text,1)[0]
        timing=r'공포\s*후\s*\d+\s*(?:개월|년)|\d{4}년\s*\d+월\s*\d+일'
        def article_pattern(number):
            parts=number.split('의')
            return r'제\s*'+parts[0]+r'\s*조'+(r'\s*의\s*'+parts[1] if len(parts)>1 else r'(?!\s*의\s*\d)')
        covered=all(any(re.search(article_pattern(a['article_number']),line) and re.search(timing,line) for line in commencement.splitlines()) for a in articles)
        if covered and '다만' in commencement and re.search(r'제\s*1\s*조\s*\(시행일\)',commencement):
            return {'source':'LAWGO_STRUCTURED_ADDENDUM','issue_number':str(entry['부칙공포번호']),
                    'before_effective_date':before['metadata']['effective_date'],'after_effective_date':after['metadata']['effective_date'],
                    'before_body_hash':before['hashes']['body_hash'],'after_body_hash':after['hashes']['body_hash'],
                    'commencement_clause':text}
    return None

def reconcile_upcoming(existing,collection,at):
    """Replace only active future events whose pairing/classification is wrong.

    Past events retain their exact objects and IDs. Original detection times are
    retained. Correct active events keep their original evidence and IDs too.
    """
    from pipeline.diff.history import make_event,merge
    pairs=[p for cid,current in collection['snapshots'].items() for p in future_pairs(current,collection['future'].get(cid,[]))]
    result=list(existing); replacements=[]
    for before,after in pairs:
        key=state_key(after)
        old=[e for e in result if (e['canonical_id'],e['after_version']['identifier'],e['after_version']['effective_date'])==key and e['after_version']['body_hash']==after['hashes']['body_hash']]
        detected=min((e['detected_at'] for e in old),default=at)
        candidate=make_event(before,after,detected)
        if not candidate: continue
        correct=next((e for e in old if e['before_version']==candidate['before_version'] and e['after_version']==candidate['after_version'] and e['changed_articles']==candidate['changed_articles'] and e['change_types']==candidate['change_types'] and e['comparison_scope']=='FULL_STRUCTURED_BODY'),None)
        if not correct and any(e['event_id']==candidate['event_id'] for e in old):
            from pipeline.normalize import digest
            candidate['event_id']='evt-'+digest({'original_event_id':candidate['event_id'],'comparison_semantics':'PREVIOUS_EFFECTIVE_STATE_FULL_STRUCTURED_BODY','changed_articles':candidate['changed_articles']})
        selected=correct or candidate
        retired=[e['event_id'] for e in old if e['event_id']!=selected['event_id']]
        if retired: replacements.append({'retired_event_ids':retired,'replacement_event_id':selected['event_id'],'canonical_id':key[0],'effective_date':key[2],'reason':'PREVIOUS_EFFECTIVE_STATE_PAIR_OR_STAGED_CLASSIFICATION'})
        result=[e for e in result if e not in old]+[selected]
    return merge([],result),replacements

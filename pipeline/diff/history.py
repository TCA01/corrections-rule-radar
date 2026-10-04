"""Persistent exact-version comparisons from official structured API evidence.

Event identity is independent of publication time and current/future placement.
Official comparison text is an excerpt (including official omission markers),
not a reconstructed full legal text. Full normalized bodies provide fallback.
"""
import re
from datetime import date,timedelta
from pipeline.normalize import digest,plain,date as api_date
from pipeline.registry import unwrap,as_list
from pipeline.diff.articles import ARTICLE,text_lines
from pipeline.publication.versions import reference
from pipeline.normalize.appendices import appendix_status

def identity(s):
    if s is None: return None
    return {'canonical_id':s['canonical_id'],'identifier':s['version_id'],
            'effective_date':s['metadata']['effective_date'],'body_hash':s['hashes']['body_hash'],
            'appendix_hash':s['hashes']['appendix_hash']}

def version(s):
    return {**reference(s),'identifier':s['version_id'],'body_hash':s['hashes']['body_hash']}

def article_groups(body):
    raw=body.get('articles')
    law=isinstance(raw,dict) and '조문단위' in raw
    items=as_list(raw.get('조문단위')) if law else as_list(raw)
    groups={}; active=None
    for item in items:
        if law and isinstance(item,dict) and item.get('조문여부') not in (None,'조문'): continue
        content='\n'.join(text_lines(item)) if isinstance(item,dict) else str(item or '').strip()
        match=ARTICLE.match(content)
        if match:
            number=match[1]+('의'+match[2] if match[2] else '')
            if number in groups: raise ValueError('DUPLICATE_ARTICLE_NUMBER')
            active=number
            groups[number]={'article_key':'article-'+number,'article_number':number,
                            'article_title':match[0].strip(),'text':content}
        elif not law and active and content:
            if re.match(r'^제\s*\d+\s*(편|장|절|관)',content): active=None
            else: groups[active]['text']+='\n'+content
    return groups or None

def article_diff(old,new,effective):
    if old is None or new is None: return None
    result=[]
    for number in sorted(set(old)|set(new),key=lambda n:tuple(int(i) for i in n.split('의'))):
        left=old.get(number); right=new.get(number)
        if left and right and left['text']==right['text']: continue
        chosen=right or left
        kind='ADDED' if left is None else 'REMOVED' if right is None else 'MODIFIED'
        if left and right and left['article_title']!=right['article_title']:
            if left['text'].replace(left['article_title'],'',1)==right['text'].replace(right['article_title'],'',1): kind='RENAMED'
        result.append({k:chosen[k] for k in ('article_key','article_number','article_title')}|
                      {'change_type':kind,'before_text':left['text'] if left else None,
                       'after_text':right['text'] if right else None,'effective_date':effective})
    return result

def official_articles(payload,before,after):
    root=unwrap(payload); kind=after['source_kind']
    id_field='법령ID' if kind=='law' else '행정규칙ID'
    serial_field='법령일련번호' if kind=='law' else '행정규칙일련번호'
    for prefix,s in (('구조문',before),('신조문',after)):
        meta=root.get(prefix+'_기본정보',{})
        if not s or str(meta.get(id_field))!=s['stable_identifier'] or str(meta.get(serial_field))!=s['version_id'] or api_date(meta.get('시행일자'))!=s['metadata']['effective_date']:
            raise ValueError('OFFICIAL_COMPARISON_PAIR_MISMATCH')
    maps=[]
    for prefix in ('구조문','신조문'):
        rows=as_list(root.get(prefix+'목록',{}).get('조문'))
        # The API wraps comparative paragraphs in presentation tags. Strip only
        # those strings; never fetch or parse an HTML page/document.
        maps.append(article_groups({'articles':[plain(r.get('content','')) for r in rows]}))
    if not all(maps): raise ValueError('OFFICIAL_COMPARISON_TEXT_UNAVAILABLE')
    # Omitted unchanged articles are not removals/additions. Official comparative
    # lists are partial: compare only matched article numbers, and use full bodies
    # for article additions/removals outside that partial list.
    shared=set(maps[0])&set(maps[1])
    excerpt=article_diff({k:maps[0][k] for k in shared},{k:maps[1][k] for k in shared},after['metadata']['effective_date']) or []
    omission=re.compile(r'\([^)]*(?:생략|현행과 같음)[^)]*\)')
    excerpt=[a for a in excerpt if omission.sub('',a['before_text'] or '')!=omission.sub('',a['after_text'] or '')]
    return excerpt

def appendix_diff(before,after):
    def mapping(s): return {(a['sequence'],a['branch'],a['type']):a for a in s['appendices']} if s else {}
    old=mapping(before); new=mapping(after); changes=[]
    for key in sorted(set(old)|set(new),key=str):
        left=old.get(key); right=new.get(key)
        if left and right and {k:v for k,v in left.items() if k not in ('url','pdf_url')}=={k:v for k,v in right.items() if k not in ('url','pdf_url')}: continue
        removed=right is None or appendix_status(right)=='REMOVED'
        kind='APPENDIX_REMOVED' if removed else 'APPENDIX_ADDED' if left is None else 'APPENDIX_METADATA_CHANGED'
        changes.append({'change_type':kind,'status':'REMOVED' if removed else 'AVAILABLE',
                        'before_metadata':left,'after_metadata':right})
    return changes

def make_event(before,after,at,*,official_comparison=None,comparison_evidence=None):
    if before and before['canonical_id']!=after['canonical_id']: raise ValueError('HISTORY_IDENTITY_MISMATCH')
    correction=bool(before and before['version_id']==after['version_id'])
    from pipeline.diff.effective_states import staged_evidence
    staged=staged_evidence(before,after) if correction else None
    kinds=[]
    if staged: kinds.append('STAGED_EFFECTIVE_DATE')
    elif correction and before['metadata']['effective_date']!=after['metadata']['effective_date']: kinds.append('EFFECTIVE_DATE_CORRECTED')
    metadata_fields=('name','rule_type','issue_date','issue_number','ministry','department','amendment_type')
    if correction and any(before['metadata'][k]!=after['metadata'][k] for k in metadata_fields): kinds.append('METADATA_CORRECTED')
    if before and not correction: kinds.append('RULE_AMENDED')
    if before and before['metadata']['name']!=after['metadata']['name'] and not correction: kinds.append('RULE_RENAMED')
    appendices=appendix_diff(before,after) if before else []
    kinds+=list(dict.fromkeys(a['change_type'] for a in appendices))
    source=None; available=False; scope='FULL_STRUCTURED_BODY'; fallback=None; articles=None
    if official_comparison is not None and before:
        try:
            articles=official_articles(official_comparison,before,after)
            source='LAWGO_OLD_NEW' if after['source_kind']=='law' else 'LAWGO_ADMIN_OLD_NEW'
            available=True; scope='OFFICIAL_COMPARISON_EXCERPT'
        except (ValueError,KeyError,TypeError): fallback='OFFICIAL_COMPARISON_PAIR_OR_TEXT_UNAVAILABLE'
    else: fallback='OFFICIAL_COMPARISON_UNAVAILABLE'
    if articles is None and before:
        try: articles=article_diff(article_groups(before['body']),article_groups(after['body']),after['metadata']['effective_date'])
        except (ValueError,TypeError,KeyError): articles=None
        if articles is not None: source='STRUCTURED_SNAPSHOT_DIFF'
    body_changed=bool(before and before['hashes']['body_hash']!=after['hashes']['body_hash'])
    if not body_changed: articles=[]
    if articles: kinds.append('ARTICLE_CHANGED')
    if after['metadata'].get('amendment_type') in ('폐지','타법폐지'): kinds.append('RULE_REPEALED')
    if before is None: kinds.append('NEW_RULE' if after['metadata'].get('amendment_type')=='제정' else 'HISTORICAL_VERSION')
    if not kinds: return None
    status='COMPARISON_UNAVAILABLE' if before is None or articles is None else 'AVAILABLE'
    reason='BEFORE_VERSION_UNAVAILABLE' if before is None else 'STRUCTURED_ARTICLES_UNAVAILABLE' if articles is None else None
    event_identity={'canonical_id':after['canonical_id'],'before':identity(before),'after':identity(after)}
    if staged: event_identity['transition']='STAGED_EFFECTIVE_DATE'
    elif correction: event_identity['correction']={k:after['metadata'][k] for k in metadata_fields}
    result={'event_id':'evt-'+digest(event_identity),'canonical_id':after['canonical_id'],
            'regulation_name':after['metadata']['name'],'regulation_type':after['metadata']['rule_type'],
            'change_type':kinds[0],'change_types':list(dict.fromkeys(kinds)),'detected_at':at,
            'promulgation_or_issue_date':after['metadata']['issue_date'],'effective_date':after['metadata']['effective_date'],
            'before_version':version(before) if before else None,'after_version':version(after),
            'changed_articles':articles or [],'changed_article_count':len(articles or []),
            'appendix_changes':appendices,'official_old_new_available':available,'comparison_source':source,
            'comparison_scope':scope,'comparison_status':status,'comparison_unavailable_reason':reason,
            'fallback_reason':fallback,'comparison_evidence':comparison_evidence if available else None,
            'official_source_url':after['official_source_url']}
    if staged: result['staged_effective_evidence']=staged
    return result

def merge(existing,candidates):
    known={e['event_id']:e for e in existing}
    for e in candidates:
        if e: known.setdefault(e['event_id'],e)
    return sorted(known.values(),key=lambda e:(e['effective_date'],e['event_id']),reverse=True)

def recent(events,today,days=90):
    if isinstance(today,str): today=date.fromisoformat(today)
    cutoff=(today-timedelta(days=days-1)).isoformat()
    return [e for e in events if cutoff<=e['effective_date']<=today.isoformat()]

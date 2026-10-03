"""Canonical textual article comparison, never legal interpretation.

Compare normalized official texts, excluding chapter headings and amendment
flags alone. Singleton XML objects and nested paragraphs/items are supported.
"""
import re
from pipeline.registry import as_list

ARTICLE=re.compile(r'^제\s*(\d+)\s*조(?:\s*의\s*(\d+))?\s*(?:\(([^)]*)\))?')

def text_lines(value):
    if isinstance(value,str): return [value.strip()] if value.strip() else []
    if isinstance(value,list): return [line for item in value for line in text_lines(item)]
    if not isinstance(value,dict): return []
    lines=[]
    # JSON object order is never semantic. Keep parent text before its children
    # even after sort_keys serialization or XML parser key ordering.
    for key in ('조문내용','항내용','호내용','목내용','내용','항','호','목'):
        if key in value: lines.extend(text_lines(value[key]))
    return lines

def article_map(body):
    raw=body.get('articles') if isinstance(body,dict) else None
    if raw is None: return None
    items=as_list(raw.get('조문단위')) if isinstance(raw,dict) and '조문단위' in raw else as_list(raw)
    result={}
    for item in items:
        if isinstance(item,str): content=item.strip(); meta={}
        elif isinstance(item,dict):
            if item.get('조문여부') not in (None,'조문'): continue
            meta=item; content='\n'.join(text_lines(item))
        else: continue
        match=ARTICLE.match(content)
        # Administrative bodies include chapter headings and unattached prose.
        # Unknown structure is unavailable, never an invented article deletion.
        if not match: continue
        number=match[1]+('의'+match[2] if match[2] else '')
        key=meta.get('조문키') or 'article-'+number
        title=meta.get('조문제목') or match[3] or ''
        display='제'+match[1]+'조'+('의'+match[2] if match[2] else '')+('('+title+')' if title else '')
        if key in result: raise ValueError('DUPLICATE_ARTICLE_KEY')
        result[key]={'article_key':key,'article_number':number,'article_title':display,'text':content}
    return result or None

def changed_articles(before,after):
    if not before or not after: return []
    if before['canonical_id']!=after['canonical_id']: raise ValueError('ARTICLE_IDENTITY_MISMATCH')
    old=article_map(before['body']); new=article_map(after['body'])
    if old is None or new is None: return []
    changes=[]
    for key in list(new)+[k for k in old if k not in new]:
        left=old.get(key); right=new.get(key)
        if left and right and left['text']==right['text']: continue
        article=right or left
        changes.append({k:article[k] for k in ('article_key','article_number','article_title')}|{'change_type':'ADDED' if not left else 'DELETED' if not right else 'MODIFIED','before_text':left['text'] if left else None,'after_text':right['text'] if right else None,'effective_date':after['metadata']['effective_date']})
    return changes

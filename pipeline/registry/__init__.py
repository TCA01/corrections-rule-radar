"""Identifier semantics from official list/body schema, never guessed from ID."""
import re
from urllib.parse import urlparse,parse_qs

def normalized_title(value):
    return re.sub(r'\s+','',value).replace('ㆍ','·')

def unwrap(obj):
    if not isinstance(obj,dict) or len(obj)!=1: raise ValueError('ROOT_SCHEMA_CHANGED')
    value=next(iter(obj.values()))
    if not isinstance(value,dict): raise ValueError('EMPTY_API_RESULT')
    if value.get('resultCode','00')!='00': raise ValueError('API_RESULT_ERROR')
    return value

def as_list(value):
    return value if isinstance(value,list) else [value] if value else []

def identifiers(item,kind):
    stable=str(item['행정규칙ID'] if kind=='admrul' else item['법령ID'])
    serial=str(item['행정규칙일련번호'] if kind=='admrul' else item['법령일련번호'])
    url=item.get('행정규칙상세링크' if kind=='admrul' else '법령상세링크')
    if url:
        query=parse_qs(urlparse(url).query)
        linked=query.get('ID' if kind=='admrul' else 'MST',[None])[0]
        if linked and linked!=serial: raise ValueError('IDENTIFIER_LINK_MISMATCH')
    if not stable.isdigit() or not serial.isdigit(): raise ValueError('INVALID_IDENTIFIER')
    return stable,serial

def detail_url(kind, serial):
    if kind=='admrul': return 'https://www.law.go.kr/LSW/admRulLsInfoP.do?admRulSeq='+serial
    return 'https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq='+serial

"""Content hashes exclude transport and timestamps; attachments are metadata only."""
import hashlib
import json
import re
from urllib.parse import urljoin,urlparse,parse_qsl,urlencode,urlunparse
from pipeline.registry import as_list,unwrap,detail_url

def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()

def date(value):
    v=str(value or '')
    return v[:4]+'-'+v[4:6]+'-'+v[6:8] if re.fullmatch(r'\d{8}',v) else None

def text(value):
    if isinstance(value,dict): return value.get('content') or None
    return str(value) if value not in (None,'') else None

def safe_url(value):
    if not value: return None
    p=urlparse(urljoin('https://www.law.go.kr',str(value)))
    if p.hostname not in ('law.go.kr','www.law.go.kr'): raise ValueError('UNTRUSTED_OFFICIAL_URL')
    q=[(k,v) for k,v in parse_qsl(p.query) if k.lower()!='oc']
    return urlunparse(('https',p.netloc,p.path,'',urlencode(q),''))

def plain(value):
    if isinstance(value,str):
        return re.sub(r'<[^>]*>','',value).strip()
    if isinstance(value,list): return [plain(v) for v in value]
    if isinstance(value,dict): return {k:plain(v) for k,v in value.items() if k not in ('생성일자','수정일자','담당자명','전화번호')}
    return value

def snapshot(payload, kind, serial, evidence):
    root=unwrap(payload); m=root.get('행정규칙기본정보' if kind=='admrul' else '기본정보')
    if not isinstance(m,dict): raise ValueError('METADATA_MISSING')
    stable=str(m.get('행정규칙ID' if kind=='admrul' else '법령ID',''))
    if not stable.isdigit(): raise ValueError('IDENTITY_MISSING')
    if kind=='admrul' and str(m.get('행정규칙일련번호'))!=serial: raise ValueError('SERIAL_MISMATCH')
    meta={'name':text(m.get('행정규칙명' if kind=='admrul' else '법령명_한글')),'rule_type':text(m.get('행정규칙종류' if kind=='admrul' else '법종구분')),'issue_date':date(m.get('발령일자' if kind=='admrul' else '공포일자')),'issue_number':text(m.get('발령번호' if kind=='admrul' else '공포번호')),'effective_date':date(m.get('시행일자')),'ministry':text(m.get('소관부처명' if kind=='admrul' else '소관부처')),'department':text(m.get('담당부서기관명')),'amendment_type':text(m.get('제개정구분명' if kind=='admrul' else '제개정구분')),'official_state':text(m.get('현행여부'))}
    if not meta['name'] or not meta['effective_date']: raise ValueError('METADATA_INCOMPLETE')
    body=plain({'articles':root.get('조문내용' if kind=='admrul' else '조문'),'addenda':root.get('부칙')})
    if not body['articles']: raise ValueError('STRUCTURED_BODY_MISSING')
    if kind=='law' and (not isinstance(body['articles'],dict) or not as_list(body['articles'].get('조문단위'))): raise ValueError('STRUCTURED_BODY_MISSING')
    appendix=[]
    for a in as_list(root.get('별표',{}).get('별표단위')):
        appendix.append({'title':text(a.get('별표제목')),'type':text(a.get('별표구분')),'sequence':str(a.get('별표번호','')),'branch':str(a.get('별표가지번호','')),'url':safe_url(a.get('별표서식파일링크')),'pdf_url':safe_url(a.get('별표서식PDF파일링크'))})
    appendix.sort(key=lambda a:(a['sequence'],a['branch']))
    attachments=[]
    att=root.get('첨부파일',{})
    if isinstance(att,dict):
        for a in as_list(att.get('첨부파일단위',att if '첨부파일명' in att else None)):
            attachments.append({'title':text(a.get('첨부파일명')),'url':safe_url(a.get('첨부파일링크')),'type':'OFFICIAL_ATTACHMENT'})
    appendix_meta=[{k:v for k,v in a.items() if k not in ('url','pdf_url')} for a in appendix]
    links={'appendices':[{k:a[k] for k in ('sequence','branch','url','pdf_url')} for a in appendix],'attachments':attachments}
    return {'canonical_id':kind+'-'+stable,'source_kind':kind,'stable_identifier':stable,'version_id':serial,'metadata':meta,'body':body,'appendices':appendix,'attachments':attachments,'official_source_url':detail_url(kind,serial),'hashes':{'metadata_hash':digest(meta),'body_hash':digest(body),'appendix_hash':digest(appendix_meta),'attachment_link_hash':digest(links)},'evidence':evidence}

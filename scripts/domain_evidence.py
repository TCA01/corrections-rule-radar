"""Extract official purpose/scope/headings for classification review, no attachments."""
import json
import re
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.snapshot import write_json

def strings(value):
    if isinstance(value,str): yield value
    elif isinstance(value,list):
        for v in value: yield from strings(v)
    elif isinstance(value,dict):
        for k,v in value.items():
            if k in ('조문내용','조문제목','항내용'): yield from strings(v)
            elif isinstance(v,(dict,list)): yield from strings(v)

def evidence(s):
    values=list(strings(s['body']['articles']))
    purpose=next((t for t in values if re.match(r'제1조\s*\(목\s*적\)',t)),None)
    scope=next((t for t in values if re.match(r'제\d+조\s*\(적용범위\)',t)),None)
    headings=[m.group(1) for t in values for m in [re.match(r'제\d+조(?:의\d+)?\s*\(([^)]+)\)',t)] if m]
    supporting=[t for t in values if re.match(r'제\d+조\s*\((순회점검반의 임무|활동분야)\)',t)]
    return {'purpose':purpose,'scope':scope,'supporting_articles':supporting,'article_headings':list(dict.fromkeys(headings)),'official_department':s['metadata']['department'],'official_source_url':s['official_source_url'],'version_id':s['version_id'],'metadata_hash':s['hashes']['metadata_hash'],'body_hash':s['hashes']['body_hash']}

def main():
    state=json.loads(Path('data/registry/state.json').read_text(encoding='utf-8')); result={}
    for cid,s in state['snapshots'].items():
        ev=evidence(s)
        if not ev['purpose'] and s['metadata']['amendment_type']=='폐지':
            candidates=[json.loads(p.read_text(encoding='utf-8')) for p in (Path('data/snapshots')/cid).glob('*.json')]
            candidates=[v for v in candidates if v['metadata']['amendment_type'] not in ('폐지','타법폐지')]
            if candidates:
                historic=max(candidates,key=lambda v:v['metadata']['effective_date']); ev['historical_scope_evidence']=evidence(historic)
        result[cid]={'current_name':s['metadata']['name'],**ev}
        purpose=ev['purpose'] or ev.get('historical_scope_evidence',{}).get('purpose') or '(공식 목적조문 없음)'
        print(cid+' | '+s['metadata']['name']+' | '+purpose[:400])
    write_json('data/reports/domain_evidence.json',result)

if __name__=='__main__': main()

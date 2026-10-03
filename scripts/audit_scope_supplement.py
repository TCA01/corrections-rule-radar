"""Report-only full-text MoJ search to catch titles without correction words."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json
from scripts.audit_scope import OUT, fingerprint
from scripts.collect import search
from pipeline.law_api import LawClient
from pipeline.snapshot import write_json
from pipeline.registry import identifiers,detail_url
from pipeline.normalize import snapshot

def main():
    before=fingerprint(); c=LawClient(cache='data/raw_cache/phase1c')
    searches=[]; bodies={}; failures=[]
    existing=json.loads((OUT/'candidate_bodies.json').read_text(encoding='utf-8'))
    registry=json.loads(Path('data/registry/rules.json').read_text(encoding='utf-8'))
    seen=set(existing)|{r['canonical_id'] for r in registry}
    for word in ('교정','교도소','구치소'):
        items,ev=search(c,'admrul',query=word,search=2,org='1270000',nw=1)
        searches.append({'query':word,'search':2,'org':'1270000','count':len(items),'items':items,'evidence':ev})
        for item in items:
            stable,serial=identifiers(item,'admrul'); cid='admrul-'+stable
            if cid in seen: continue
            seen.add(cid)
            try:
                payload,evidence=c.fetch('lawService.do',target='admrul',ID=serial)
                record={'list_item':item,'payload':payload,'evidence':evidence,'official_url':detail_url('admrul',serial)}
                try: record['snapshot']=snapshot(payload,'admrul',serial,evidence)
                except ValueError as exc: record['body_review_reason']=str(exc)
                bodies[cid]=record
            except Exception: failures.append(cid)
        print('FULL_TEXT_COMPLETE '+word+' '+str(len(items)),flush=True)
        write_json(OUT/'supplement.json',{'searches':searches,'bodies':bodies,'failures':failures,'production_unchanged':before==fingerprint()})

if __name__=='__main__': main()

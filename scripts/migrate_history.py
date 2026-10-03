"""Rehearse, then explicitly publish schema 1.3 for trusted 68 only."""
import argparse,copy,json,sys,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import sync
from scripts.validate_public import validate
from scripts.observe import public_fingerprint
from pipeline.snapshot import write_json

def run(publish=False):
    root=sync.ROOT; state=sync.read('data/registry/state.json',{})
    rows=sync.read('data/registry/rules.json',[])
    backfill=sync.read('data/staging/phase1e_backfill.json',{})
    if len(rows)!=68 or len(backfill.get('records',[]))!=68 or any(r['status']!='PASS' for r in backfill['records']): raise ValueError('HISTORY_BACKFILL_COVERAGE_REQUIRES_REVIEW')
    collection={'complete':True,'registry':rows,'snapshots':state['snapshots'],'future':state['future'],'resolution':[{'canonical_id':r['canonical_id'],'status':'RESOLVED'} for r in rows],'history_backfill':backfill}
    if publish: return sync.sync(collection)
    out=root/'data/staging'; out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='phase1e-rehearsal-',dir=out) as tmp:
        target=Path(tmp)
        for rel in ('data/registry/state.json','data/registry/rules.json','data/registry/events.json'):
            write_json(target/rel,json.loads((root/rel).read_text(encoding='utf8')))
        import shutil
        shutil.copytree(root/'public/api/v1',target/'public/api/v1')
        # Retain exact archives and all local normalized evidence for migrated
        # event references, without modifying any production file.
        shutil.copytree(root/'data/snapshots',target/'data/snapshots')
        with patch.object(sync,'ROOT',target):
            first=sync.sync(copy.deepcopy(collection)); validation=validate(target/'public/api/v1')
            good=public_fingerprint(target)
            second=sync.sync(copy.deepcopy(collection))
            if second['result']!='NO_CHANGE' or good!=public_fingerprint(target): raise ValueError('MIGRATION_NOT_IDEMPOTENT')
            result={'first':first,'second':second,'validation':validation,'production_unchanged':True}
    write_json(root/'data/reports/phase1e_rehearsal.json',result)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');args=p.parse_args()
    print(json.dumps(run(args.publish),ensure_ascii=False))

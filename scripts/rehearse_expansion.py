"""Actual publication logic in an isolated directory; no deployment."""
import copy,json,shutil,sys,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import sync
from scripts.observe import public_fingerprint
from scripts.validate_public import validate
from pipeline.snapshot import write_json

ROOT=Path(__file__).resolve().parents[1]
def load(path): return json.loads((ROOT/path).read_text(encoding='utf8'))

def candidate():
    c=load('data/staging/phase1f_collection.json'); c['approved_expansion']='PHASE1F'; c['history_backfill']=load('data/staging/phase1f_backfill.json')
    # Historical official names are useful aliases, never identity matching keys.
    names={}
    for s in c['history_backfill']['snapshots']: names.setdefault(s['canonical_id'],set()).add(s['metadata']['name'])
    for row in c['registry']:
        row['historical_names']=list(dict.fromkeys(row['historical_names']+sorted(n for n in names.get(row['canonical_id'],[]) if n!=row['current_name'])))
    return c

def run():
    c=candidate(); old_history=load('data/registry/change_history.json')
    with tempfile.TemporaryDirectory(prefix='phase1f-rehearsal-',dir=ROOT/'data/staging') as tmp:
        target=Path(tmp)
        for rel in ('data/registry','data/snapshots','public/api/v1'):
            shutil.copytree(ROOT/rel,target/rel)
        write_json(target/'data/reports/phase1d_api_eligibility.json',load('data/reports/phase1d_api_eligibility.json'))
        with patch.object(sync,'ROOT',target):
            first=sync.sync(copy.deepcopy(c)); verified=validate(target/'public/api/v1'); good=public_fingerprint(target)
            bad=copy.deepcopy(c); cid=bad['registry'][-1]['canonical_id']; bad['resolution'][-1].update({'status':'REVIEW','review_reason':'SIMULATED_API_TIMEOUT'}); bad['snapshots'].pop(cid); bad['registry'].pop()
            failed=sync.sync(bad)
            if failed['result']!='BLOCKED' or public_fingerprint(target)!=good: raise ValueError('EXPANDED_LAST_GOOD_RECOVERY_FAILED')
            next_c=copy.deepcopy(c); next_c.pop('approved_expansion')
            second=sync.sync(next_c)
            if second['result']!='NO_CHANGE' or public_fingerprint(target)!=good: raise ValueError('EXPANSION_IDEMPOTENCY_FAILED')
            after=json.loads((target/'data/registry/change_history.json').read_text(encoding='utf8'))
            indexed={e['event_id']:e for e in after}
            if any(indexed.get(e['event_id'])!=e for e in old_history): raise ValueError('PERSISTENT_68_HISTORY_CHANGED')
            result={'first':first,'simulated_failure':failed['result'],'second':second,'validation':verified,'old_history_retained':True,'last_good_bytes_and_mtimes_preserved':True,'production_publication':False}
    write_json(ROOT/'data/reports/phase1f_rehearsal.json',result)
    return result

if __name__=='__main__': print(json.dumps(run(),ensure_ascii=False))

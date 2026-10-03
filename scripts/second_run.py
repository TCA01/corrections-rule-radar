"""Repeat LIVE collection; compare public bytes, mtimes and event IDs."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.law_api import ApiError
from pipeline.normalize import digest
from pipeline.snapshot import write_json
from scripts.collect import run
from scripts.sync import sync,read

def fingerprint():
    root=Path('public/api/v1')
    return {str(p.relative_to(root)).replace('\\','/'):{'sha256':digest(p.read_text(encoding='utf-8')),'mtime_ns':p.stat().st_mtime_ns} for p in root.rglob('*.json')}

def main():
    before=fingerprint(); old_ids=[e['event_id'] for e in read('data/registry/events.json',[])]
    run()
    result=sync(read('data/staging/collection.json',None)); after=fingerprint(); new_ids=[e['event_id'] for e in read('data/registry/events.json',[])]
    report={'live_recollection':True,'result':result,'public_bytes_and_mtimes_identical':before==after,'event_ids_identical':old_ids==new_ids,'public_file_count':len(after),'status':'PASS' if result['result']=='NO_CHANGE' and before==after and old_ids==new_ids else 'FAIL'}
    write_json('data/reports/second_run.json',report)
    print(json.dumps(report),flush=True)

if __name__=='__main__':
    try: main()
    except ApiError as e: print(e.code); sys.exit(1)
    except Exception: print('SECOND_RUN_FAILED'); sys.exit(1)

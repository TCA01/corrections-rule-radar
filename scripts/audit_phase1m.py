"""Read-only operational evidence capture; never writes production legal state."""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.snapshot import write_json

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'data/reports'
STAGING = ROOT / 'data/staging/phase1m'

def read(path):
    return json.loads(path.read_text(encoding='utf8'))

def gh(*args):
    return subprocess.check_output(['gh', *args], cwd=ROOT).decode('utf8')

def freeze():
    files = [p for folder in ('public/api/v1', 'data/registry', 'data/snapshots') for p in (ROOT/folder).rglob('*') if p.is_file()]
    value = {'at': datetime.now(timezone.utc).isoformat(), 'head': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
             'dataset_version': read(ROOT/'public/api/v1/manifest.json')['dataset_version'],
             'files': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
             'original_user_report_sha256': hashlib.sha256((ROOT/'data/reports/phase1g_legacy_rehearsal.json').read_bytes()).hexdigest()}
    path = REPORTS/'phase1m_before.json'
    if path.exists(): raise ValueError('BEFORE_EVIDENCE_ALREADY_EXISTS')
    write_json(path, value)
    print(json.dumps({'status':'PASS','files':len(files),'dataset_version':value['dataset_version']}))

def official():
    from pipeline.law_api import LawClient
    from pipeline.law_api.search import search
    from pipeline.registry import identifiers, unwrap
    from pipeline.normalize import snapshot
    client = LawClient(cache=STAGING/'raw_cache')
    current, ce = client.fetch('lawService.do', target='admrul', LID='35611')
    try: current_root = unwrap(current)
    except ValueError: current_root = None
    items, he = search(client, 'admrul', query='미결수용인 분리수용 관련 지침', nw=2)
    exact = [i for i in items if identifiers(i,'admrul')[0]=='35611']
    if not exact: raise ValueError('OFFICIAL_HISTORY_MISSING')
    latest = max(exact,key=lambda i:(i['발령일자'],i['행정규칙일련번호']))
    serial = identifiers(latest,'admrul')[1]
    payload, evidence = client.fetch('lawService.do',target='admrul',ID=serial)
    sn = snapshot(payload,'admrul',serial,evidence)
    write_json(STAGING/'official_body.json',payload)
    write_json(STAGING/'official_snapshot.json',sn)
    value = {'status':'PASS','canonical_id':sn['canonical_id'],'version_id':serial,'metadata':sn['metadata'],
             'official_source_url':sn['official_source_url'],'hashes':sn['hashes'],'structured_body_present':bool(sn['body']['articles']),
             'current_lid_root_keys':list(current_root) if current_root else [],'current_evidence':ce,
             'exact_history_rows':exact,'history_evidence':he,'body_evidence':evidence}
    write_json(REPORTS/'phase1m_official_repeal.json',value)
    print(json.dumps(value,ensure_ascii=False))

def history():
    repo = 'repos/TCA01/corrections-rule-radar'
    runs = json.loads(gh('api',repo+'/actions/runs?created=%3E%3D2026-10-06T15%3A00%3A00Z&per_page=100'))['workflow_runs']
    result = []
    for r in runs:
        jobs = json.loads(gh('api',repo+f'/actions/runs/{r["id"]}/jobs'))['jobs']
        row = {k:r.get(k) for k in ('id','name','event','created_at','run_started_at','updated_at','status','conclusion','head_sha','html_url')}
        row['jobs'] = [{k:j.get(k) for k in ('name','started_at','completed_at','conclusion','steps')} for j in jobs]
        if r['name']=='Production regulation sync' and r['status']=='completed':
            log = gh('run','view',str(r['id']),'--repo','TCA01/corrections-rule-radar','--log')
            row['schedule_log_evidence'] = [line for line in log.splitlines() if 'SCHEDULE:' in line]
        result.append(row)
    value = {'as_of':datetime.now(timezone.utc).isoformat(),'runs':result,
             'repository':{k:v for k,v in json.loads(gh('api',repo)).items() if k in ('default_branch','archived','disabled')},
             'workflow':json.loads(gh('api',repo+'/actions/workflows/production.yml')),
             'variables':json.loads(gh('api',repo+'/actions/variables'))}
    write_json(REPORTS/'phase1m_run_history.json',value)
    print(json.dumps({'as_of':value['as_of'],'runs':[{k:r[k] for k in ('id','name','event','conclusion','created_at')} for r in result]}))

if __name__=='__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('mode',choices=['freeze','official','history'])
    globals()[parser.parse_args().mode]()

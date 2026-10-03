"""Strict generated-state staging and 30-day heartbeat; never arbitrary git add."""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.operations import heartbeat_due,now
from pipeline.snapshot import write_json

ROOT=Path(__file__).resolve().parents[1]
EXACT={'data/registry/state.json','data/registry/rules.json','data/registry/events.json','data/registry/change_history.json','data/seed/corrections.json','data/ops/deployment.json'}
def allowed(path):
    if '\\' in path or any(part in ('.','..','') for part in path.split('/')): return False
    return path in EXACT or bool(re.fullmatch(r'public/api/v1/(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.json',path)) or bool(re.fullmatch(r'data/snapshots/(law|admrul)-\d+/[A-Za-z0-9_.-]+\.json',path))
def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT).decode().strip()
def last_activity(): return git('log','-1','--format=%cI')
def prepare(*,published,at=None,last_change=None):
    at=at or now(); marker=ROOT/'data/ops/deployment.json'
    old=json.loads(marker.read_text(encoding='utf-8')) if marker.exists() else {}
    manifest=json.loads((ROOT/'public/api/v1/manifest.json').read_text(encoding='utf-8')); version=manifest['dataset_version']
    if published:
        old.update({'pending_dataset_version':version,'last_deployed_dataset_version':old.get('last_deployed_dataset_version')}); write_json(marker,old)
        changed=git('ls-files','--modified','--others','--exclude-standard').splitlines()
        paths=[p for p in changed if allowed(p)]
    else:
        paths=[]
        if heartbeat_due(last_change or last_activity(),at):
            write_json(ROOT/'data/ops/heartbeat.json',{'last_heartbeat':at,'reason':'30_DAYS_WITHOUT_REPOSITORY_COMMIT'})
            paths=['data/ops/heartbeat.json']
    if paths: git('add','--',*paths)
    # On a new host/bootstrap there may be no prior deployment marker. A manual
    # enabled run can deploy the validated existing baseline too.
    pending=old.get('pending_dataset_version') or (version if not old.get('last_deployed_dataset_version') else None)
    return {'public_changed':published,'commit_needed':bool(paths),'deploy_needed':pending is not None,'dataset_version':version,'heartbeat_only':paths==['data/ops/heartbeat.json']}
def acknowledge(version):
    current=json.loads((ROOT/'public/api/v1/manifest.json').read_text(encoding='utf-8'))['dataset_version']
    if version!=current: raise ValueError('DEPLOYMENT_DATASET_MISMATCH')
    write_json(ROOT/'data/ops/deployment.json',{'pending_dataset_version':None,'last_deployed_dataset_version':version,'last_successful_deployment':now()}); git('add','--','data/ops/deployment.json')
def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--ack-deployed'); args=parser.parse_args()
    if args.ack_deployed: acknowledge(args.ack_deployed); return
    report=json.loads((ROOT/'data/reports/production_sync.json').read_text(encoding='utf-8'))
    if report['result'] not in ('PUBLISHED','NO_CHANGE'): raise ValueError('UNTRUSTED_PUBLICATION')
    result=prepare(published=report['result']=='PUBLISHED')
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a',encoding='utf-8') as f:
            for key,value in result.items(): f.write(f'{key}={str(value).lower() if isinstance(value,bool) else value}\n')
    print(json.dumps(result))
if __name__=='__main__': main()

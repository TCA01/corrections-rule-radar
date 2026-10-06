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
from pipeline.operations.public_status import status_hash

ROOT=Path(__file__).resolve().parents[1]
EXACT={'data/registry/state.json','data/registry/rules.json','data/registry/events.json','data/registry/change_history.json','data/registry/provenance.json','data/registry/business_domains.json','data/registry/scope_approval.json','data/registry/scope_approvals/phase1g.json','data/seed/business_domains.json','data/seed/corrections.json','data/ops/deployment.json'}
def allowed(path):
    if '\\' in path or any(part in ('.','..','') for part in path.split('/')): return False
    return path in EXACT or bool(re.fullmatch(r'public/api/v1/(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.json',path)) or bool(re.fullmatch(r'data/snapshots/(law|admrul)-\d+/[A-Za-z0-9_.-]+\.json',path))
def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT).decode().strip()
def last_activity(): return git('log','-1','--format=%cI')
def prepare(*,published,force_deploy=False,at=None,last_change=None):
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
    ops_hash=status_hash(ROOT)
    ops_pending=bool(ops_hash and ops_hash!=old.get('last_deployed_ops_sha256'))
    if ops_pending:
        old['pending_ops_sha256']=ops_hash
        write_json(marker,old)
        paths=list(dict.fromkeys(paths+['public/api/v1/ops-status.json','data/ops/deployment.json']))
    if paths: git('add','--',*paths)
    # On a new host/bootstrap there may be no prior deployment marker. A manual
    # enabled run can deploy the validated existing baseline too.
    pending=old.get('pending_dataset_version') or (version if not old.get('last_deployed_dataset_version') else None)
    return {'public_changed':published,'ops_changed':ops_pending,'commit_needed':bool(paths),'deploy_needed':(pending is not None) or ops_pending or force_deploy,'dataset_version':version,'heartbeat_only':paths==['data/ops/heartbeat.json']}
def acknowledge(version):
    current=json.loads((ROOT/'public/api/v1/manifest.json').read_text(encoding='utf-8'))['dataset_version']
    if version!=current: raise ValueError('DEPLOYMENT_DATASET_MISMATCH')
    write_json(ROOT/'data/ops/deployment.json',{'pending_dataset_version':None,'pending_ops_sha256':None,'last_deployed_dataset_version':version,'last_deployed_ops_sha256':status_hash(ROOT),'last_successful_deployment':now()}); git('add','--','data/ops/deployment.json')
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--ack-deployed')
    parser.add_argument('--force-deploy', action='store_true')
    args=parser.parse_args()
    if args.ack_deployed: acknowledge(args.ack_deployed); return
    report=json.loads((ROOT/'data/reports/production_sync.json').read_text(encoding='utf-8'))
    if report['result'] not in ('PUBLISHED','NO_CHANGE'): raise ValueError('UNTRUSTED_PUBLICATION')
    force = bool(args.force_deploy or (os.environ.get('FORCE_DEPLOY', '').lower() == 'true'))
    result=prepare(published=report['result']=='PUBLISHED', force_deploy=force)
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a',encoding='utf-8') as f:
            for key,value in result.items(): f.write(f'{key}={str(value).lower() if isinstance(value,bool) else value}\n')
    print(json.dumps(result))
if __name__=='__main__': main()

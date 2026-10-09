"""Successful scan status, deliberately outside legal dataset identity."""
import json, os, hashlib
from pathlib import Path
from pipeline.snapshot import write_json
from pipeline.validation import validate_contract

def status_hash(root):
    path=Path(root)/'public/api/v1/ops-status.json'
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None

def publish_status(root, report, context=None):
    if report['result'] not in ('PUBLISHED','NO_CHANGE'): return False
    folder=Path(root)/'public/api/v1'
    manifest=json.loads((folder/'manifest.json').read_text(encoding='utf8'))
    rules=json.loads((folder/'rules.json').read_text(encoding='utf8'))['rules']
    path=folder/'ops-status.json'
    previous=json.loads(path.read_text(encoding='utf8')) if path.exists() else {}
    context=context or {'trigger':'MANUAL'}
    trigger=context['trigger']
    run_id=context.get('github_run_id','')
    value={'schema_version':'1.5','status_scope':'LAST_SUCCESSFUL_SCAN',
           'last_scan_started_at':report['started_at'],'last_scan_completed_at':report['finished_at'],
           'last_scan_status':'OK','last_scan_result':report['result'],
           'last_scan_rule_count':len(rules),'last_scan_current_count':sum(r['status']=='CURRENT' for r in rules),
           'last_scan_failures':0,'last_good_dataset_version':manifest['dataset_version'],
           'schedule_kst':['08:37','20:37'], 'trigger':trigger,
           'last_scheduled_scan':previous.get('last_scheduled_scan')}
    if run_id: value['github_run_id']=run_id
    if trigger=='SCHEDULE':
        cron=context.get('schedule_cron','')
        if cron not in ('37 23 * * *','37 11 * * *'): raise ValueError('UNVERIFIED_SCHEDULE_CRON')
        value['schedule_cron']=cron
        value['last_scheduled_scan']={'started_at':report['started_at'],'completed_at':report['finished_at'],
            'result':report['result'],'dataset_version':manifest['dataset_version'],'cron':cron,'github_run_id':run_id}
    validate_contract('ops-status',value)
    temp=folder/'ops-status.tmp'
    write_json(temp,value); os.replace(temp,folder/'ops-status.json')
    return True

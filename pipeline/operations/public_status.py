"""Successful scan status, deliberately outside legal dataset identity."""
import json, os, hashlib
from pathlib import Path
from pipeline.snapshot import write_json
from pipeline.validation import validate_contract

def status_hash(root):
    path=Path(root)/'public/api/v1/ops-status.json'
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None

def publish_status(root, report):
    if report['result'] not in ('PUBLISHED','NO_CHANGE'): return False
    folder=Path(root)/'public/api/v1'
    manifest=json.loads((folder/'manifest.json').read_text(encoding='utf8'))
    rules=json.loads((folder/'rules.json').read_text(encoding='utf8'))['rules']
    value={'schema_version':'1.5','status_scope':'LAST_SUCCESSFUL_SCAN',
           'last_scan_started_at':report['started_at'],'last_scan_completed_at':report['finished_at'],
           'last_scan_status':'OK','last_scan_result':report['result'],
           'last_scan_rule_count':len(rules),'last_scan_current_count':sum(r['status']=='CURRENT' for r in rules),
           'last_scan_failures':0,'last_good_dataset_version':manifest['dataset_version'],
           'schedule_kst':['08:37','20:37']}
    validate_contract('ops-status',value)
    temp=folder/'ops-status.tmp'
    write_json(temp,value); os.replace(temp,folder/'ops-status.json')
    return True

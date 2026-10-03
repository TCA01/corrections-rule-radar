"""Portable offline validation runner; concise diagnostics, no raw tracebacks."""
import io
import json
import os
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.snapshot import write_json
from pipeline.validation import validate_contract,assert_schema_freeze

def scan_secret():
    secret=os.environ.get('LAW_API_OC','')
    if not secret: return {'status':'NOT_VERIFIED','files':[]}
    needle=secret.encode(); hits=[]
    for p in Path('.').rglob('*'):
        if not p.is_file() or any(part in ('.git','.venv','__pycache__') for part in p.parts): continue
        if needle in p.read_bytes(): hits.append(str(p).replace('\\','/'))
    return {'status':'PASS' if not hits else 'FAIL','file_count':len(hits),'files':hits}

def main():
    assert_schema_freeze()
    suite=unittest.defaultTestLoader.discover('tests')
    stream=io.StringIO(); result=unittest.TextTestRunner(stream=stream,verbosity=0).run(suite)
    report={'tests':result.testsRun,'passed':result.wasSuccessful(),'failures':len(result.failures),'errors':len(result.errors),'failure_test_ids':[t.id() for t,_ in result.failures+result.errors],'secret_scan':scan_secret()}
    public=Path('public/api/v1'); checked=0; schema_failures=[]
    for p in public.rglob('*.json'):
        rel=str(p.relative_to(public)).replace('\\','/')
        schema='version' if '/versions/' in rel else 'changes' if rel.startswith('changes/') else 'rule' if rel.startswith('rules/') else p.stem
        try: validate_contract(schema,json.loads(p.read_text(encoding='utf-8'))); checked+=1
        except Exception: schema_failures.append(rel)
    report['public_contract']={'validated_file_count':checked,'failed_files':schema_failures,'status':'PASS' if checked and not schema_failures else 'FAIL'}
    write_json('data/reports/tests.json',report)
    print(json.dumps(report,ensure_ascii=False))
    return 0 if result.wasSuccessful() and not schema_failures and report['secret_scan']['status']=='PASS' else 1

if __name__=='__main__': sys.exit(main())

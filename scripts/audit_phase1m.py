"""Read-only operational evidence capture; never writes production legal state."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import urllib.request
from collections import Counter
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
    pages = json.loads(gh('api', '--paginate', '--slurp', repo+'/actions/runs?created=%3E%3D2026-10-06T15%3A00%3A00Z&per_page=100'))
    runs = [run for page in pages for run in page['workflow_runs']]
    assert len(runs) == len({run['id'] for run in runs})
    result = []
    for r in runs:
        jobs = json.loads(gh('api',repo+f'/actions/runs/{r["id"]}/jobs'))['jobs']
        row = {k:r.get(k) for k in ('id','name','event','created_at','run_started_at','updated_at','status','conclusion','head_sha','html_url')}
        row['jobs'] = [{k:j.get(k) for k in ('name','started_at','completed_at','conclusion','steps')} for j in jobs]
        if r['name']=='Production regulation sync' and r['status']=='completed':
            log = gh('run','view',str(r['id']),'--repo','TCA01/corrections-rule-radar','--log')
            row['schedule_log_evidence'] = [line for line in log.splitlines() if 'SCHEDULE:' in line]
            row['failure_log_evidence'] = [line for line in log.splitlines()
                if 'FAIL: test_' in line or 'AssertionError: Counter(' in line]
        result.append(row)
    value = {'as_of':datetime.now(timezone.utc).isoformat(),'runs':result,
             'query_started_at_utc':'2026-10-06T15:00:00Z','pagination_pages':len(pages),
             'all_runs_captured':len(runs)==pages[0]['total_count'],
             'repository':{k:v for k,v in json.loads(gh('api',repo)).items() if k in ('default_branch','archived','disabled')},
             'workflow':json.loads(gh('api',repo+'/actions/workflows/production.yml')),
             'variables':json.loads(gh('api',repo+'/actions/variables'))}
    write_json(REPORTS/'phase1m_run_history.json',value)
    print(json.dumps({'as_of':value['as_of'],'runs':[{k:r[k] for k in ('id','name','event','conclusion','created_at')} for r in result]}))

def ci(run_id):
    meta=json.loads(gh('run','view',str(run_id),'--repo','TCA01/corrections-rule-radar','--json','databaseId,event,headSha,createdAt,startedAt,updatedAt,conclusion,jobs'))
    log=re.sub(r'(?:\x1b|\^\[)\[[0-9;]*m','',gh('run','view',str(run_id),'--repo','TCA01/corrections-rule-radar','--log'))
    proof=[line for line in log.splitlines() if '"tests": 173' in line or re.search(r'Tests\s+102 passed',line) or '"artifact_file_count": 548' in line]
    assert meta['conclusion']=='success' and len(proof)==3
    write_json(REPORTS/f'phase1m_ci_{run_id}.json',{'status':'PASS','run':meta,'validation_log_evidence':proof})
    print(json.dumps({'status':'PASS','run_id':run_id,'evidence':proof}))

def live(run_id):
    base='https://corrections-rule-radar.web.app/api/v1/'
    def fetch(rel):
        req=urllib.request.Request(base+rel,headers={'Cache-Control':'no-cache','Accept':'application/json'})
        with urllib.request.urlopen(req,timeout=30) as response: return json.load(response)
    manifest=fetch('manifest.json'); health=fetch('health.json'); rules=fetch('rules.json'); ops=fetch('ops-status.json')
    assert manifest['dataset_version']==health['dataset_version']==rules['dataset_version']==ops['last_good_dataset_version']
    assert ops['github_run_id']==str(run_id) and ops['trigger']=='MANUAL'
    scheduled_run=json.loads(gh('api','repos/TCA01/corrections-rule-radar/actions/runs/'+ops['last_scheduled_scan']['github_run_id']))
    assert scheduled_run['event']=='schedule' and scheduled_run['conclusion']=='success'
    completed=datetime.fromisoformat(ops['last_scheduled_scan']['completed_at'].replace('Z','+00:00'))
    assert datetime.fromisoformat(scheduled_run['created_at'].replace('Z','+00:00'))<=completed<=datetime.fromisoformat(scheduled_run['updated_at'].replace('Z','+00:00'))
    scope=set(read(ROOT/'data/registry/state.json')['seed_ids'])
    assert {r['canonical_id'] for r in rules['rules']}==scope and len(scope)==107
    target=fetch('rules/admrul-35611.json'); official=read(STAGING/'official_snapshot.json')
    assert target['current']['version_id']==official['version_id']
    assert target['current']['metadata']==official['metadata'] and target['rule']['status']=='REPEALED'
    assert target['current']['hashes']['body_hash']==official['hashes']['body_hash']
    upcoming=[]
    for cid in ('law-001668','law-001671'):
        detail=fetch('rules/'+cid+'.json')
        upcoming += [{'canonical_id':cid,'date':s['metadata']['effective_date'],'version_id':s['version_id'],
                      'baseline':s['articles_compared_to'],'incremental':len(s['changed_articles']),
                      'cumulative':len(s['cumulative_changed_articles'])} for s in detail['upcoming']]
    value={'status':'PASS','checked_at':datetime.now(timezone.utc).isoformat(),'run_id':run_id,
        'dataset_version':manifest['dataset_version'],'published_at':manifest['published_at'],
        'counts':dict(Counter(r['status'] for r in rules['rules'])),'tracked':len(rules['rules']),
        'ops':ops,'last_scheduled_run_event_verified':scheduled_run['event'],'official_repeal_body_matches':True,'upcoming':upcoming}
    write_json(REPORTS/f'phase1m_live_{run_id}.json',value)
    write_json(REPORTS/'phase1m_live.json',value)
    print(json.dumps(value,ensure_ascii=True))

def legal_fingerprint():
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ('public/api/v1','data/registry','data/snapshots')
            for p in (ROOT/folder).rglob('*.json') if p.name!='ops-status.json'}

def capture(final=False):
    path=REPORTS/('phase1m_final_baseline.json' if final else 'phase1m_recovery_baseline.json')
    if path.exists(): raise ValueError('RECOVERY_BASELINE_ALREADY_EXISTS')
    write_json(path,{'at':datetime.now(timezone.utc).isoformat(),'files':legal_fingerprint(),
                    'dataset_version':read(ROOT/'public/api/v1/manifest.json')['dataset_version']})
    print('Recovered legal-state fingerprint captured.')

def capture_final():
    capture(final=True)

def preservation():
    original=read(REPORTS/'phase1m_before.json')
    immutable=[n for n,h in original['files'].items() if n.startswith('data/snapshots/') and hashlib.sha256((ROOT/n).read_bytes()).hexdigest()!=h]
    prior=json.loads(subprocess.check_output(['git','show','dea5cc0:data/registry/state.json'],cwd=ROOT).decode('utf8'))
    current=read(ROOT/'data/registry/state.json')
    changed=[cid for cid,s in prior['snapshots'].items() if any(s['hashes'][k]!=current['snapshots'][cid]['hashes'][k] for k in ('metadata_hash','body_hash','appendix_hash'))]
    future_preserved={cid:[(s['version_id'],s['metadata']['effective_date'],s['hashes']['body_hash']) for s in future]
                      for cid,future in prior['future'].items()}=={
                      cid:[(s['version_id'],s['metadata']['effective_date'],s['hashes']['body_hash']) for s in future]
                      for cid,future in current['future'].items()}
    baseline_path=REPORTS/'phase1m_final_baseline.json'
    if not baseline_path.exists(): baseline_path=REPORTS/'phase1m_recovery_baseline.json'
    baseline=read(baseline_path)
    no_change=baseline['files']==legal_fingerprint()
    value={'status':'PASS' if not immutable and future_preserved and no_change else 'FAIL',
           'immutable_original_snapshots_preserved':not immutable,'drifted_snapshots':immutable,
           'changed_current_rule_ids':changed,'future_states_preserved':future_preserved,
           'approved_107_ids_preserved':set(prior['seed_ids'])==set(current['seed_ids']) and len(current['seed_ids'])==107,
           'no_change_all_legal_bytes_and_snapshot_set_identical':no_change,
           'no_change_dataset_version_identical':baseline['dataset_version']==read(ROOT/'public/api/v1/manifest.json')['dataset_version'],
           'no_change_baseline':baseline_path.name,
           'original_user_report_preserved':hashlib.sha256((ROOT/'data/reports/phase1g_legacy_rehearsal.json').read_bytes()).hexdigest()==original['original_user_report_sha256']}
    assert value['approved_107_ids_preserved'] and value['original_user_report_preserved']
    write_json(REPORTS/'phase1m_preservation.json',value)
    print(json.dumps(value)); assert value['status']=='PASS'

if __name__=='__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('mode',choices=['freeze','official','history','live','ci','capture','capture_final','preservation']); parser.add_argument('--run-id',type=int)
    args=parser.parse_args()
    if args.mode in ('live','ci'): globals()[args.mode](args.run_id)
    else: globals()[args.mode]()

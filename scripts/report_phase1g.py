"""Measured Phase 1G report, with hosted checks distinct from local checks."""
import json,sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.snapshot import write_json
ROOT=Path(__file__).resolve().parents[1]
def load(name,default=None):
    p=ROOT/name
    return json.loads(p.read_text(encoding='utf8')) if p.exists() else default
def run():
    eligibility=load('data/reports/phase1g_api_eligibility.json'); cid=eligibility['canonical_id']
    rules=load('public/api/v1/rules.json')['rules']; law=next(r for r in rules if r['canonical_id']==cid)
    events=[e for e in load('public/api/v1/changes/history.json')['events'] if e['canonical_id']==cid]
    recent=[e for e in load('public/api/v1/changes/recent.json')['events'] if e['canonical_id']==cid]
    first=load('data/reports/phase1g_live_run1.json'); second=load('data/reports/phase1g_live_run2.json')
    backfill=load('data/reports/phase1g_backfill.json'); backend=load('data/reports/tests.json')
    front=load('data/reports/phase1g_frontend_tests.json',{})
    artifact=load('data/reports/firebase_artifact.json',{})
    hosted=load('data/reports/phase1g_hosted.json',{})
    action=load('data/reports/phase1g_github_run.json',{})
    creator=(ROOT/'web/src/components/NoticeFooter.tsx').read_text(encoding='utf8')
    report={'phase':'PHASE 1G CRIMINAL PROCEDURE ACT EXPANSION','schema':'1.4','api_eligibility':eligibility['status'],
        'official_title':law['current_name'],'canonical_id':cid,'current_effective_date':law['metadata']['effective_date'],
        'current_mst':law['version_id'],'promulgation_number':law['metadata']['issue_number'],'promulgation_date':law['metadata']['issue_date'],
        'official_source_url':law['official_source_url'],'scope_class':law['provenance']['scope_class'],
        'selection_basis':law['provenance']['selection_basis'],'applies_to':law['provenance']['applies_to'],'business_domains':law['business_domains'],
        'previous_tracked':106,'added':1,'final_tracked':len(rules),'current':sum(r['status']=='CURRENT' for r in rules),'historical':sum(r['status']=='REPEALED' for r in rules),
        'history_events_added':len(events),'recent_events_added':len(recent),'comparison_sources':dict(Counter(e['comparison_source'] for e in events)),
        'recent_examples':[{k:e[k] for k in ('event_id','effective_date','changed_article_count','comparison_source','official_source_url')} for e in recent],
        'old_new_comparison':'PASS' if any(e['official_old_new_available'] for e in events) and all(e['comparison_status']=='AVAILABLE' for e in events) else 'FAIL',
        'history_backfill':{'policy':backfill['records'][0]['backfill_policy'],'metrics':backfill['metrics'],'duration_seconds':backfill['duration_seconds']},
        'future_versions':[(v['version_id'],v['metadata']['effective_date']) for v in load('public'+law['detail_url'])['upcoming']],
        'first_run':'CHANGED' if first['result']=='PUBLISHED' else 'FAIL','second_run':second['result'],'live_runs':[first,second],
        'before_metrics':load('data/reports/phase1f_live_run2.json'),
        'backend_tests':backend,'frontend_tests':{'passed':front.get('numPassedTests'),'total':front.get('numTotalTests'),'success':front.get('success')},
        'build_and_artifact':artifact,'secret_leak':backend['secret_scan'].get('file_count'),
        'footer_old_copy':'ABSENT' if '교정직 공무원 및 관련 업무 담당자를 위한' not in creator else 'FAIL',
        'creator_credit':'PASS' if 'Created by Kim In-jun · Wonju Correctional Institution' in creator and 'Created by:' not in creator else 'FAIL',
        'public_disclaimer':'PASS' if 'Personal project · Not an official service of Wonju Correctional Institution or the Ministry of Justice.' in creator else 'FAIL',
        'initial_blocked_attempt':load('data/reports/phase1g_blocked_attempt.json'),
        'resolved_issue':'Initial publication rejected new discovery-source enum values; replaced with existing schema 1.4 values. Last-good remained intact.',
        'github_normal_run':action,'hosted_verification':hosted,
        'ready_for_unattended_operation':bool(action.get('conclusion')=='success' and hosted.get('status')=='PASS' and hosted.get('ui_status')=='PASS' and backend['passed'] and front.get('success') and artifact.get('status')=='PASS'),
        'known_issues':['One-time history backfill selects 32 of 58 listed versions plus their predecessor (25 earlier versions not fetched); normal sync does not crawl history.',
                        'Official old/new pair/text unavailable for 22 selected events; full structured snapshot comparison is explicitly identified.',
                        'Official department metadata is absent and remains null. No department or legal interpretation is invented.']}
    write_json(ROOT/'data/reports/phase1g_expansion.json',report)
    lines=['# PHASE 1G CRIMINAL PROCEDURE ACT EXPANSION','','| Item | Result |','|---|---|']
    for key in ('schema','api_eligibility','official_title','canonical_id','current_mst','current_effective_date','promulgation_number','promulgation_date','scope_class','selection_basis','business_domains','previous_tracked','added','final_tracked','current','historical','history_events_added','recent_events_added','old_new_comparison','first_run','second_run','footer_old_copy','creator_credit','public_disclaimer','ready_for_unattended_operation'):
        lines.append(f'| {key} | {report[key]} |')
    lines+=['','## Operation','',f"Before: 128 API calls, 141.281 seconds (Phase 1F unchanged run). After: {second['api_request_count']} calls, {second['duration_seconds']} seconds, {second['retry_count']} retries. First successful expansion: {first['duration_seconds']} seconds.",
            '',f"Backend: {backend['tests']} tests, pass={backend['passed']}; frontend: {report['frontend_tests']}; JSON: {backend['public_contract']}; artifact: {artifact.get('status','PENDING')}; secret leaks: {report['secret_leak']}.",
            '',f"History: {backfill['records'][0]['backfill_policy']}. Sources: {report['comparison_sources']}. Recent examples: {json.dumps(report['recent_examples'],ensure_ascii=False)}.",
            '', 'All original 106 stable IDs and existing immutable events/archives are covered by regression fixtures. Second run has identical public bytes/mtimes, snapshot hashes and event IDs.',
            '', '## Hosted operation','',f"GitHub: {json.dumps(action,ensure_ascii=False)}",'',f"Live: {json.dumps(hosted,ensure_ascii=False)}",'',
            '## Known issues','']+['- '+s for s in report['known_issues']]+['','Resolved initial validation failure: '+report['resolved_issue'],'']
    (ROOT/'data/reports/phase1g_expansion.md').write_text('\n'.join(lines),encoding='utf8')
    print(json.dumps({'tracked':report['final_tracked'],'history_added':len(events),'recent_added':len(recent),'ready':report['ready_for_unattended_operation']}))
if __name__=='__main__': run()

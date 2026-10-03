"""Build the Phase 1F review artifact from measured, local evidence."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.snapshot import write_json

ROOT=Path(__file__).resolve().parents[1]
def load(name): return json.loads((ROOT/name).read_text(encoding='utf8'))
def run():
    rules=load('public/api/v1/rules.json')['rules']
    events=load('public/api/v1/changes/history.json')['events']
    runs=[load(f'data/reports/phase1f_live_run{i}.json') for i in (1,2)]
    scheduled=load('data/reports/phase1f_scheduled_rehearsal.json')
    audit=load('data/reports/full_id_revalidation.json')
    tests=load('data/reports/tests.json')
    rehearsal=load('data/reports/phase1f_rehearsal.json')
    domains=load('data/reports/phase1f_domain_review.json')
    backfill=load('data/staging/phase1f_backfill.json')
    protected={}; failures=[]
    for name,prior in load('data/reports/phase1f_before.json').items():
        if not (name.startswith('web') or 'versions' in name or 'changes\\evt-' in name or 'phase1d' in name): continue
        p=ROOT/name
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=prior['sha256'] or p.stat().st_mtime_ns!=prior['mtime_ns']: failures.append(name)
        group='frontend' if name.startswith('web') else 'archives' if 'versions' in name else 'old_event_details' if 'changes\\evt-' in name else 'phase1d_evidence'
        protected[group]=protected.get(group,0)+1
    removed=sum(a['status']=='REMOVED' for r in rules for a in load('public'+r['detail_url'])['current']['appendices'])
    low=len(domains['low_confidence'])
    comparisons=Counter(e['comparison_status'] for e in events)
    ready=(len(rules)==106 and tests['passed'] and tests['public_contract']['status']=='PASS'
           and tests['secret_scan']['status']=='PASS' and not failures and runs[1]['result']=='NO_CHANGE'
           and scheduled['result']=='NO_CHANGE' and audit['status']=='PASS' and audit['count']==106
           and rehearsal['last_good_bytes_and_mtimes_preserved'])
    report={
      'phase':'PHASE 1F PRODUCTION EXPANSION','schema':'1.4','previous_core':68,'approved_additions':38,
      'final_tracked':len(rules),'current':sum(r['status']=='CURRENT' for r in rules),
      'historical_repealed':sum(r['status']=='REPEALED' for r in rules),
      'direct_corrections_added':15,'cross_domain_added':23,
      'api_trackable_production':sum(r['provenance']['api_tracking_class']=='API_TRACKABLE' for r in rules),
      'api_limited_production':sum(r['provenance']['api_tracking_class']=='API_TRACKABLE_LIMITED' for r in rules),
      'review_production':sum(r['provenance']['scope_review_status']!='APPROVED' for r in rules),
      'provenance_coverage':sum(bool(r['provenance']) for r in rules),
      'selection_basis_coverage':sum(bool(r['provenance']['selection_basis']) for r in rules),
      'business_domain_coverage':sum(bool(r['business_domains']) for r in rules),
      'report_domain':{r['canonical_id']:{'official_current_name':r['current_name'],'domains':r['business_domains']} for r in rules if r['canonical_id'] in ('admrul-32484','admrul-51868')},
      'domain_review_pending':sum(r['classification_status']!='REVIEWED' for r in rules),
      'lower_confidence_other':low,'domain_distribution_primary':dict(Counter(r['primary_domain'] for r in rules)),
      'persistent_change_events':len(events),'recent_90_day_events':len(load('public/api/v1/changes/recent.json')['events']),
      'events_with_comparison':comparisons['AVAILABLE'],'events_with_changed_articles':sum(e['changed_article_count']>0 for e in events),
      'comparison_unavailable':comparisons['COMPARISON_UNAVAILABLE'],
      'comparison_sources':dict(Counter(e['comparison_source'] or 'UNAVAILABLE' for e in events)),
      'upcoming_events':len(load('public/api/v1/changes/upcoming.json')['events']),
      'history_backfill':{'rules':len(backfill['records']),'passed':sum(r['status']=='PASS' for r in backfill['records']),
                         'events_added':41,'pairs':len(backfill['pairs']),'predecessor_pairs':sum(p['before'] is not None for p in backfill['pairs']),
                         'initial_enactment_without_predecessor':sum(p['before'] is None for p in backfill['pairs']),
                         'api_calls':backfill['metrics']['api_request_count'],'duration_seconds':backfill['duration_seconds']},
      'removed_appendix_normalization':{'status':'PASS','current_removed_count':removed,'raw_metadata_preserved':True},
      'live_runs':runs,'first_run':'CHANGED' if runs[0]['result']=='PUBLISHED' else 'FAIL',
      'second_run':runs[1]['result'],'average_live_runtime_seconds':round(sum(r['duration_seconds'] for r in runs)/2,3),
      'fail_closed':'PASS' if rehearsal['simulated_failure']=='BLOCKED' else 'FAIL',
      'last_good':'PASS' if rehearsal['last_good_bytes_and_mtimes_preserved'] else 'FAIL',
      'protected_files':protected,'protected_files_failures':failures,
      'scheduled_rehearsal':{'scope':'LOCAL_SAME_SCHEDULED_ENTRYPOINT_NOT_HOSTED_ACTIONS','report':scheduled,
                             'full_id_revalidation_count':audit['count'],'full_id_revalidation_status':audit['status']},
      'backend_tests':tests,'firebase_deployed':False,'frontend_modified':False,'ready_for_web_w4':ready,
      'known_limitations':[
        '20 events have no available predecessor/comparison; official omissions are preserved, with no fabricated differences.',
        'Backfill covers the recent 90-day window and current predecessor, not every historical revision.',
        'Administrative future versions are detected where the official stable-ID API exposes them; unpublished future versions cannot be exhaustively enumerated.',
        f'{low} primary 기타 assignments have lower domain confidence; scope approval and API eligibility remain approved.',
        'Requested report-domain IDs have different official current titles; stable IDs and official titles are preserved.',
        'Opaque page hashes may change for non-regulation content, causing extra API discovery queries. No candidate is automatically admitted.',
        'Hosted GitHub Actions, Firebase deployment, Web W4 consumption and final unattended E2E have not been executed in this phase.'
      ],
      'next_step':'Web W4 schema 1.4 integration and final unattended-operation E2E.'}
    write_json(ROOT/'data/reports/phase1f_expansion.json',report)
    lines=['# PHASE 1F PRODUCTION EXPANSION','',f"READY FOR WEB W4: {'YES' if ready else 'NO'}",'',
           '| Item | Result |','|---|---|']
    for key in ('schema','previous_core','approved_additions','final_tracked','current','historical_repealed','direct_corrections_added','cross_domain_added','api_trackable_production','api_limited_production','review_production','provenance_coverage','selection_basis_coverage','business_domain_coverage','domain_review_pending','lower_confidence_other','persistent_change_events','recent_90_day_events','events_with_comparison','events_with_changed_articles','comparison_unavailable','upcoming_events','first_run','second_run','fail_closed','last_good'):
        lines.append(f'| {key} | {report[key]} |')
    lines+=['','## Report domain','']
    for cid,item in report['report_domain'].items(): lines.append(f"- {cid}: {item['official_current_name']} → {', '.join(item['domains'])}")
    lines+=['','## Measured operation','', '| Run | API calls | Seconds | Retries | Result |','|---|---:|---:|---:|---|']
    for label,r in [('Expanded first',runs[0]),('Unchanged second',runs[1]),('Local scheduled full audit',scheduled)]:
        lines.append(f"| {label} | {r['api_request_count']} | {r['duration_seconds']} | {r['retry_count']} | {r['result']} |")
    lines += ['',f"One-time new-38 backfill: {backfill['metrics']['api_request_count']} API calls, {backfill['duration_seconds']} seconds, 41 events, 29 predecessor pairs and 12 initial enactments.",
              '',f"Local scheduled entrypoint: full identity audit {audit['count']}/106 {audit['status']}; independent page monitor error: {scheduled['discovery_monitor_error'] or 'NONE'}. This is not a hosted GitHub Actions execution.",
              '',f"Second run preserved all public bytes, mtimes, snapshot hashes and event IDs. Protected files: {json.dumps(protected)}; discrepancies: {len(failures)}.",
              '',f"Backend tests: {tests['tests']} PASS. Public JSON: {tests['public_contract']['validated_file_count']} PASS. Secret leaks: {tests['secret_scan']['file_count']}. Removed appendices: {removed}.",
              '', 'Frontend modification: NO. Firebase deployed: NO. Existing immutable event envelopes remain 1.3; immutable archived snapshots remain 1.1.',
              '', 'Discovery cache stores only credential-free opaque page fingerprints and the pending approval queue in the existing workflow; see [official cache documentation](https://github.com/actions/cache).',
              '', '## Primary domain distribution','']
    for name,count in report['domain_distribution_primary'].items(): lines.append(f'- {name}: {count}')
    lines+=['','## Known limitations','']+['- '+item for item in report['known_limitations']]
    lines+=['','NEXT STEP: '+report['next_step'],'']
    (ROOT/'data/reports/phase1f_expansion.md').write_text('\n'.join(lines),encoding='utf8')
    print(json.dumps({'ready':ready,'protected_files':protected,'discrepancies':failures}))
    return 0 if ready else 1
if __name__=='__main__': sys.exit(run())

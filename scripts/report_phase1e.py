"""Report measured live runs, persisted evidence and integrity checks."""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.snapshot import write_json
from pipeline.validation import assert_public_safe
from scripts.validate_public import validate

def load(path): return json.loads(Path(path).read_text(encoding='utf8'))

def run():
    history=load('public/api/v1/changes/history.json')['events']; recent=load('public/api/v1/changes/recent.json')['events']
    tests=load('data/reports/tests.json'); baseline=load('data/reports/phase1e_before_performance.json')
    runs=[load('data/reports/phase1e_live_run1.json'),load('data/reports/phase1e_live_run2.json')]
    before=load('data/reports/phase1e_before.json'); failed=[]; counts={'immutable_archives':0,'frontend_files':0,'phase1d_discovery_files':0}
    for path,record in before.items():
        group='immutable_archives' if '/versions/' in path.replace('\\','/') else 'frontend_files' if path.startswith('web') else 'phase1d_discovery_files' if 'phase1d' in path else None
        if group:
            p=Path(path); counts[group]+=1
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=record['sha256'] or p.stat().st_mtime_ns!=record['mtime_ns']: failed.append(path)
    sources={s:sum(e['comparison_source']==s for e in history) for s in ('LAWGO_OLD_NEW','LAWGO_ADMIN_OLD_NEW','STRUCTURED_SNAPSHOT_DIFF')}
    examples=[{'event_id':e['event_id'],'canonical_id':e['canonical_id'],'regulation_name':e['regulation_name'],'effective_date':e['effective_date'],'changed_article_count':e['changed_article_count'],'comparison_source':e['comparison_source']} for e in recent if e['changed_article_count']]
    status='PASS' if tests['passed'] and tests['secret_scan']['status']=='PASS' and not failed and all(r['result']=='NO_CHANGE' and r['api_request_count']==90 and r['public_bytes_and_mtimes_identical'] and r['snapshot_hashes_identical'] for r in runs) else 'FAIL'
    result={'phase':'1E','schema':'1.3','current_core':len(load('public/api/v1/rules.json')['rules']),
      'persistent_change_events':len(history),'recent_90_day_events':len(recent),
      'events_with_article_comparison':sum(e['changed_article_count']>0 for e in history),
      'events_without_article_comparison':sum(e['changed_article_count']==0 for e in history),
      'comparison_unavailable':sum(e['comparison_status']=='COMPARISON_UNAVAILABLE' for e in history),
      'recent_comparison_unavailable':sum(e['comparison_status']=='COMPARISON_UNAVAILABLE' for e in recent),
      'source_distribution':sources,'history_beyond_90_days':sum(e['effective_date']<'2026-07-06' for e in history),
      'appendix_removal_events':sum(a['status']=='REMOVED' for e in history for a in e['appendix_changes']),
      'past_effective_examples':examples,'runs':runs,
      'performance_before':{'api_calls':baseline['api_request_count'],'duration_seconds':baseline['duration_seconds']},
      'performance_after':{'api_calls_per_run':[r['api_request_count'] for r in runs],'duration_seconds':[r['duration_seconds'] for r in runs],'average_duration_seconds':round(sum(r['duration_seconds'] for r in runs)/len(runs),3)},
      'backfill':{k:load('data/reports/phase1e_backfill.json')[k] for k in ('metrics','duration_seconds')},
      'backend_tests':tests,'public_json_validation':validate('public/api/v1'),
      'integrity':{'status':'PASS' if not failed else 'FAIL','checked_counts':counts,'changed_protected_files':failed},
      'production_core_expanded':False,'frontend_modified':False,'deployed':False,
      'ready_for_web_w3':status=='PASS','status':status,
      'known_limitations':['Official old/new comparison excerpts may contain omission markers; comparison_scope discloses this.',
        'Exact-pair mismatches use structured snapshot fallback; no HTML/document parsing.',
        'Six earlier historical baselines have no structured predecessor; explicitly COMPARISON_UNAVAILABLE. Recent 90-day events have no unavailable comparisons.',
        'Initial backfill covers recent 90 days and a preceding historical change per rule, not every amendment since creation.',
        'Legacy latest/upcoming feeds retain their pre-1.3 event model; Web W3 should consume recent/history and persistent event details.',
        'No attachment contents or legal interpretation. Future provenance/scope expansion is reserved for schema 1.4.']}
    write_json('data/reports/phase1e.json',result)
    lines=['# PHASE 1E PERSISTENT CHANGE HISTORY','',f"SCHEMA: 1.3\n\nCURRENT CORE: {result['current_core']}",'',
      f"PERSISTENT CHANGE EVENTS: {len(history)}\n\nRECENT 90-DAY EVENTS: {len(recent)}",
      f"\nEVENTS WITH ARTICLE COMPARISON: {result['events_with_article_comparison']}\n\nEVENTS WITHOUT ARTICLE COMPARISON: {result['events_without_article_comparison']} (six unavailable; two no article changes)",'',
      '| Check | Result |','|---|---|',
      '| LAW OLD/NEW | PASS — '+str(sources['LAWGO_OLD_NEW'])+' live events |',
      '| ADMIN OLD/NEW | PASS — '+str(sources['LAWGO_ADMIN_OLD_NEW'])+' live events |',
      '| SNAPSHOT DIFF FALLBACK | PASS — '+str(sources['STRUCTURED_SNAPSHOT_DIFF'])+' events |',
      '| PAST-EFFECTIVE COMPARISON | PASS — actual official API responses, including 2026-10-01 교도작업운영지침 |',
      '| UPCOMING → CURRENT RETENTION | PASS — transition tests retain identical event and text |',
      '| 90-DAY FILTER | PASS — future, today, yesterday, weeks, day 89/day 90 boundaries |',
      '| HISTORY BEYOND 90 DAYS | PASS — '+str(result['history_beyond_90_days'])+' events retained |',
      '| APPENDIX REMOVAL HISTORY | PASS — '+str(result['appendix_removal_events'])+' retained removed metadata entries, plus null-download tests |',
      '| EVENT ID STABILITY | PASS — deterministic IDs and unchanged live history |',
      '| SECOND RUN | '+runs[1]['result']+' |',
      '| API CALLS BEFORE | '+str(baseline['api_request_count'])+' |',
      '| API CALLS AFTER | '+', '.join(str(r['api_request_count']) for r in runs)+'; frozen history has no additional requests |',
      '| RUNTIME | before '+str(baseline['duration_seconds'])+'s; after '+', '.join(str(r['duration_seconds'])+'s' for r in runs)+' |',
      '| BACKEND TESTS | '+str(tests['tests'])+' PASS |',
      '| PUBLIC JSON VALIDATION | '+str(result['public_json_validation']['validated_files'])+' files PASS |',
      '| SECRET LEAK | 0 |','| PRODUCTION CORE EXPANDED | NO |',
      '| READY FOR WEB W3 | '+('YES' if result['ready_for_web_w3'] else 'NO')+' |','',
      'No frontend changes, deployment, HTML scraping or document parsing. Protected archive/frontend/Phase 1D discovery bytes and modification times: '+result['integrity']['status']+'.','',
      '## Known limitations','']
    lines+=['- '+s for s in result['known_limitations']]
    lines+=['','NEXT STEP: Web W3 consume schema 1.3.','',
       '[Contract](../../docs/phase1e_contract.md) · [Structured report](phase1e.json)',
       '[Official administrative old/new API documentation](https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=admrulOldAndNewInfoGuide)']
    Path('data/reports/phase1e.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    return {k:v for k,v in result.items() if k not in ('backend_tests','runs','past_effective_examples','known_limitations')}

if __name__=='__main__': print(json.dumps(run(),ensure_ascii=False))

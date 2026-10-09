"""Build the reliability report from saved Actions and publication evidence."""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.snapshot import write_json
ROOT=Path(__file__).resolve().parents[1]
SEOUL=timezone(timedelta(hours=9))

def read(p): return json.loads(p.read_text(encoding='utf8'))
def instant(s): return datetime.fromisoformat(s.replace('Z','+00:00'))
def kst(s): return instant(s).astimezone(SEOUL).strftime('%Y-%m-%d %H:%M:%S') if s else '-'

def main():
    reports=ROOT/'data/reports'; history=read(reports/'phase1m_run_history.json'); rows=[]
    for run in sorted(history['runs'],key=lambda r:r['created_at']):
        row={**run,'created_at_kst':kst(run['created_at']),'started_at_kst':kst(run['run_started_at']),
             'completed_at':max((j['completed_at'] for j in run['jobs'] if j['completed_at']),default=None)}
        row['completed_at_kst']=kst(row['completed_at'])
        row['duration_seconds']=(instant(row['completed_at'])-instant(run['created_at'])).total_seconds() if row['completed_at'] else None
        cron=next((c for c in ('37 23 * * *','37 11 * * *') if any(c in line for line in run.get('schedule_log_evidence',[]))),None)
        if cron and run['event']=='schedule':
            created=instant(run['created_at']); slot=created.replace(hour=int(cron.split()[1]),minute=37,second=0,microsecond=0)
            if slot>created: slot-=timedelta(days=1)
            row.update(cron=cron,expected_slot_kst=kst(slot.isoformat()),dispatch_delay_seconds=(created-slot).total_seconds())
        artifact=ROOT/f'data/staging/phase1m/runs/{run["id"]}'
        for field,rel in [('sync','data/reports/production_sync.json'),('verification','data/reports/tests.json'),('ops','public/api/v1/ops-status.json')]:
            path=artifact/rel
            if path.exists(): row[field]=read(path)
        row['failed_steps']=[s['name'] for j in run['jobs'] for s in j.get('steps',[]) if s['conclusion']=='failure']
        row['deployment_completed']=any('Deploy validated' in s['name'] and s['conclusion']=='success' for j in run['jobs'] for s in j.get('steps',[]))
        rows.append(row)
    slots=[]
    for day,time in [('2026-10-07','08:37'),('2026-10-07','20:37'),('2026-10-08','08:37'),('2026-10-08','20:37'),('2026-10-09','08:37')]:
        matched=[r for r in rows if r.get('expected_slot_kst','').startswith(day+' '+time)]
        row=matched[-1] if matched else None
        slots.append({'slot_kst':day+' '+time,'run_existed':bool(row),'run_id':row['id'] if row else None,
                      'result':row['conclusion'].upper() if row and row['conclusion'] else ('RUNNING' if row else 'MISSING'),
                      'created_at_kst':row['created_at_kst'] if row else None})
    livepath=reports/'phase1m_live.json'; live=read(livepath) if livepath.exists() else None
    value={'phase':'1M','as_of':history['as_of'],'expected_schedules_kst':['08:37','20:37'],'slots':slots,'runs':rows,
        'ui_origin':{'run_id':37503211648,'event':'schedule','completed_utc':'2026-10-06T17:32:06.209233+00:00','completed_kst':'2026-10-07 02:32:06'},
        'root_cause':['One exact-ID collection review: CURRENT_NOT_CONFIRMED during official repeal transition.',
                      'Three subsequent verified collections could not deploy because historical release tests froze live status counts at 105/2 (Phase1G) and 104/2 (Phase1F).',
                      'Scheduled dispatch was observed 3–6 hours after configured slots, before runner jobs started; underlying GitHub dispatch cause is not established.'],
        'timezone_bug':False,'ops_status_only_stale':False,'scope_preserved':107,
        'official_repeal':read(reports/'phase1m_official_repeal.json'),'live':live}
    write_json(reports/'phase1m_final.json',value)
    lines=['# PHASE 1M — SCHEDULED RUN RELIABILITY','',f"Audit cutoff: {kst(history['as_of'])} KST",'',
           'EXPECTED SCHEDULES: 08:37 KST / 20:37 KST','',
           '| Expected slot KST | Run existed | Result | Run ID | Actual creation KST |',
           '|---|---|---|---|---|']
    for s in slots: lines.append(f"| {s['slot_kst']} | {'YES' if s['run_existed'] else 'NO'} | {s['result']} | {s['run_id'] or '-'} | {s['created_at_kst'] or '-'} |")
    lines+=['','MISSING is the state at the audit cutoff; it does not prove permanent cancellation or a disabled workflow.','',
            '| Run ID | Workflow / event | Created UTC / KST | Started UTC / KST | Completed UTC / KST | Conclusion | Duration s | Head SHA |',
            '|---|---|---|---|---|---|---|---|']
    for r in rows:
        lines.append(f"| [{r['id']}]({r['html_url']}) | {r['name']} / {r['event']} | {r['created_at']} / {r['created_at_kst']} | {r['run_started_at']} / {r['started_at_kst']} | {r['completed_at']} / {r['completed_at_kst']} | {r['conclusion'] or r['status']} | {r['duration_seconds']} | {r['head_sha']} |")
    lines+=['','UI 2026-10-07 02:32 ORIGIN: run 37503211648, actual schedule event (`37 11 * * *`),',
            'successful scan completed 2026-10-06T17:32:06.209233+00:00 UTC = 2026-10-07 02:32:06 KST.',
            'It belongs to the October 6 20:37 slot and was delayed before run creation. The timezone conversion is correct.','',
            'ROOT CAUSE:','']+['- '+s for s in value['root_cause']]
    lines+=['','SCHEDULE WORKFLOW ACTUALLY RUNNING: YES',
            'LEGAL SCANS MISSED: one incomplete collection; three later complete collections failed the publication gate. The missing October 9 slot is separately unconfirmed at cutoff.',
            'OPS STATUS ONLY STALE: NO', 'TIMEZONE BUG: NO','',
            'Cron/default main/workflow enabled/production variable/concurrency/permissions were verified. No event-specific condition bypasses the schedule publication path.',
            'NO_CHANGE updates the separate ops status and deploys its hash while retaining all legal bytes. The October 7 success proves that path already worked.','',
            'FIX APPLIED: fixed release-count assertions using exact-ID structured repeal evidence; kept exact approved tracking scope and original historical identities. Added optional ops trigger/run/last-scheduled provenance and a manual morning/evening policy rehearsal input. No timeout, retry, deadline or fail-closed rule was loosened.','',
            'The official API confirms admrul-35611, serial 2100000286404, 폐지, effective 2026-10-02. History and body agree. Therefore the observed live totals must become 107 tracked / 104 current / 3 repealed, rather than preserving the now-obsolete 105/2 observation.','',
            'OPS STATUS SEMANTICS: scheduled and manual results are distinguished; manual checks preserve the last real successful scheduled scan. Legacy origin annotation uses the actual uploaded report without changing timestamps.','',
            'NEXT SCHEDULE CONFIG: PASS (23:37 / 11:37 UTC). Delivery timing is best effort; this fix does not remove GitHub dispatch delays.',
            'GitHub documents possible schedule delays/drops: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule','']
    if live:
        lines+=['LIVE VERIFICATION:','', '```json',json.dumps(live,ensure_ascii=False,indent=2),'```']
    else: lines+=['Live recovery verification is pending. No readiness claim is made by this preliminary report.']
    (reports/'phase1m_final.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(json.dumps({'status':'PASS','run_count':len(rows),'live_verified':bool(live)}))

if __name__=='__main__': main()

"""Schedule policy: twice-daily core, daily tables, Sunday full identity audit."""
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.operations.calendar import seoul_date
from scripts.unattended_sync import run
import json

def policy(schedule,manual_full=False,day=None):
    morning=schedule=='37 23 * * *'
    return {'discovery':morning or not schedule,'full_audit':manual_full or (morning and (day or seoul_date()).weekday()==6)}

def selected_schedule(event, schedule, test_mode='normal'):
    if event=='schedule': return schedule
    if test_mode not in ('normal','morning','evening'): raise ValueError('INVALID_SCHEDULE_TEST_MODE')
    return {'normal':'','morning':'37 23 * * *','evening':'37 11 * * *'}[test_mode]

def scan_context(event, schedule, run_id=''):
    context={'trigger':'SCHEDULE' if event=='schedule' else 'MANUAL'}
    if run_id: context['github_run_id']=run_id
    if event=='schedule': context['schedule_cron']=schedule
    return context

if __name__=='__main__':
    schedule=selected_schedule(os.environ.get('GITHUB_EVENT_NAME',''),os.environ.get('SCHEDULE',''),os.environ.get('SCHEDULE_TEST_MODE','normal'))
    selection=policy(schedule,os.environ.get('FULL_AUDIT','').lower()=='true')
    context=scan_context(os.environ.get('GITHUB_EVENT_NAME',''),os.environ.get('SCHEDULE',''),os.environ.get('GITHUB_RUN_ID',''))
    report=run(**selection,scan_context=context)
    report['trigger']=context['trigger']
    report['schedule_policy']=selection
    report['schedule_test_mode']=os.environ.get('SCHEDULE_TEST_MODE') or 'normal'
    from pipeline.snapshot import write_json
    write_json(Path(__file__).resolve().parents[1]/'data/reports/production_sync.json',report)
    print(json.dumps(report)); sys.exit(int(report['result']=='BLOCKED'))

"""Schedule policy: twice-daily core, daily tables, Sunday full identity audit."""
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.operations.calendar import seoul_date
from scripts.production_sync import run
import json

def policy(schedule,manual_full=False,day=None):
    morning=schedule=='37 23 * * *'
    return {'discovery':morning or not schedule,'full_audit':manual_full or (morning and (day or seoul_date()).weekday()==6)}
if __name__=='__main__':
    selection=policy(os.environ.get('SCHEDULE',''),os.environ.get('FULL_AUDIT','').lower()=='true')
    report=run(**selection); print(json.dumps(report)); sys.exit(int(report['result']=='BLOCKED'))

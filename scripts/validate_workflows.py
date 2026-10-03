"""Static YAML/policy validation (not a hosted Actions execution)."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import yaml
from pipeline.snapshot import write_json

ROOT=Path(__file__).resolve().parents[1]
def validate(root=ROOT):
    production=yaml.load((root/'.github/workflows/production.yml').read_text(encoding='utf-8'),Loader=yaml.BaseLoader)
    ci=yaml.load((root/'.github/workflows/validation.yml').read_text(encoding='utf-8'),Loader=yaml.BaseLoader)
    if {r['cron'] for r in production['on']['schedule']}!={'37 23 * * *','37 11 * * *'}: raise ValueError('INVALID_SYNC_CRON')
    if 'workflow_dispatch' not in production['on'] or production['concurrency']['cancel-in-progress']!='false': raise ValueError('UNSAFE_CONCURRENCY')
    steps=production['jobs']['sync']['steps']; text=json.dumps(production)
    for command in ('scripts/scheduled_sync.py','scripts/verify.py','npm test','npm run build','scripts/verify_artifact.py','scripts/generated_commit.py'):
        if command not in text: raise ValueError('MISSING_PRODUCTION_GATE')
    names=[s.get('name','') for s in steps]
    if names.index('Verify exact hosting artifact')>names.index('Deploy validated candidate to Firebase Hosting'): raise ValueError('DEPLOY_BEFORE_VALIDATION')
    deploy=next(s for s in steps if s.get('uses','').startswith('FirebaseExtended/'))
    if deploy.get('if')!="steps.state.outputs.deploy_needed == 'true'" or deploy['with']['channelId']!='live': raise ValueError('UNGUARDED_DEPLOY')
    if 'PRODUCTION_PIPELINE_ENABLED' not in production['jobs']['sync']['if']: raise ValueError('PRODUCTION_NOT_GATED')
    if any('pull_request_target' in workflow['on'] for workflow in (production,ci)): raise ValueError('UNTRUSTED_TRIGGER')
    if any('git add .' in s.get('run','') or 'git add -A' in s.get('run','') for s in steps): raise ValueError('UNBOUNDED_GENERATED_COMMIT')
    headers=json.loads((root/'firebase.json').read_text(encoding='utf-8'))['hosting']
    if headers['public']!='web/dist' or 'rewrites' in headers: raise ValueError('INVALID_HOSTING_ROOT_OR_API_FALLBACK')
    cache={r['source']:r['headers'][0]['value'] for r in headers['headers']}
    if 'no-cache' not in cache['/index.html'] or 'must-revalidate' not in cache['/api/v1/**'] or 'immutable' not in cache['/assets/**']: raise ValueError('INVALID_CACHE_POLICY')
    return {'status':'PASS','scope':'STATIC_VALIDATION_ONLY','cron_utc':['37 23 * * *','37 11 * * *'],'cron_kst':['08:37','20:37'],'firebase_cache_policy':'PASS'}
if __name__=='__main__':
    report=validate(); write_json(ROOT/'data/reports/workflows.json',report); print(json.dumps(report))

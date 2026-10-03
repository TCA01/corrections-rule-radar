"""Post-deploy public probe before acknowledgment; never authenticates requests."""
import json
import os
import re
import time
import urllib.request

def verify(project,expected):
    if not re.fullmatch(r'[a-z][a-z0-9-]{4,29}',project or ''): raise ValueError('FIREBASE_PROJECT_ID_REQUIRED')
    if not re.fullmatch(r'ds-[a-f0-9]{64}',expected or ''): raise ValueError('DATASET_VERSION_REQUIRED')
    for attempt in range(3):
        try:
            for path in ('manifest.json','health.json','rules.json'):
                request=urllib.request.Request(f'https://{project}.web.app/api/v1/{path}',headers={'Cache-Control':'no-cache','Accept':'application/json'})
                with urllib.request.urlopen(request,timeout=30) as response: value=json.load(response)
                if value['dataset_version']!=expected: raise ValueError('HOSTED_DATASET_MISMATCH')
            return {'status':'PASS','dataset_version':expected}
        except Exception:
            if attempt==2: raise ValueError('HOSTED_RELEASE_NOT_VERIFIED') from None
            time.sleep(5)
if __name__=='__main__': print(json.dumps(verify(os.environ.get('FIREBASE_PROJECT_ID'),os.environ.get('DATASET_VERSION'))))

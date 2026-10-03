"""All public outputs are checked for leaks and schemas before publication."""
import json
import hashlib
import os
import re
from pathlib import Path
from urllib.parse import quote,quote_plus

def assert_schema_freeze():
    root=Path(__file__).resolve().parents[2]
    lock=root/'schemas/api_v1_candidate.lock.json'
    if not lock.exists(): raise ValueError('API_V1_FREEZE_MISSING')
    frozen=json.loads(lock.read_text(encoding='utf-8'))
    actual={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'schemas').glob('*.schema.json'))}
    if frozen['schema_version']!='1.2' or frozen['schema_sha256']!=actual: raise ValueError('API_V1_SCHEMA_DRIFT_REQUIRES_EXPLICIT_REVIEW')
    return True

def assert_public_safe(value,*,text=False):
    # Compiled text must not be JSON-escaped: an object key followed by an
    # escaped quote otherwise resembles a Windows drive path (d:\\...).
    data=value if text else json.dumps(value,ensure_ascii=False)
    secret=os.environ.get('LAW_API_OC','')
    if secret and any(s in data for s in (secret,quote(secret,safe=''),quote_plus(secret))): raise ValueError('SECRET_LEAK')
    if re.search(r'LAW_API_OC|(?<![A-Za-z0-9])[A-Za-z]:[\\/]|file://|traceback|[?&]OC=',data,re.I): raise ValueError('PUBLIC_INFORMATION_LEAK')
    user=os.environ.get('USERNAME','')
    if user and re.search(r'(?<!\w)'+re.escape(user)+r'(?!\w)',data,re.I): raise ValueError('USERNAME_LEAK')
    return True

def validate_contract(name,value):
    from jsonschema import Draft202012Validator,FormatChecker
    schema=json.loads((Path(__file__).resolve().parents[2]/'schemas'/f'{name}.schema.json').read_text(encoding='utf-8'))
    Draft202012Validator(schema,format_checker=FormatChecker()).validate(value)
    assert_public_safe(value)

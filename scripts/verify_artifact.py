"""Inspect the exact Firebase hosting artifact; no source/private payload allowed."""
import json
import re
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.validation import assert_public_safe
from pipeline.snapshot import write_json
from scripts.validate_public import validate

def verify(folder):
    folder=Path(folder).resolve()
    if not (folder/'index.html').is_file() or not list((folder/'assets').glob('*.js')): raise ValueError('INCOMPLETE_WEB_BUILD')
    html=(folder/'index.html').read_text(encoding='utf-8')
    for url in re.findall(r'(?:src|href)="(/assets/[^"]+)"',html):
        if not (folder/url.lstrip('/')).is_file(): raise ValueError('MISSING_WEB_ASSET')
    count=0
    for p in folder.rglob('*'):
        if p.is_symlink(): raise ValueError('ARTIFACT_SYMLINK')
        if not p.is_file(): continue
        rel=p.relative_to(folder).as_posix()
        if rel!='index.html' and not (rel.startswith('assets/') and p.suffix in ('.js','.css')) and not (rel.startswith('api/v1/') and p.suffix=='.json'): raise ValueError('UNEXPECTED_ARTIFACT_FILE')
        if rel.startswith('assets/') and not re.fullmatch(r'.+-[A-Za-z0-9_-]{8,}\.(js|css)',p.name): raise ValueError('ASSET_NOT_CONTENT_HASHED')
        content=p.read_text(encoding='utf-8'); assert_public_safe(content,text=True)
        if re.search(r'AIza[0-9A-Za-z_-]{35}|-----BEGIN .*PRIVATE KEY-----|"private_key"\s*:',content): raise ValueError('ARTIFACT_CREDENTIAL')
        count+=1
    public=validate(folder/'api/v1')
    return {'status':'PASS','artifact_file_count':count,'api':public,'secret_leak_count':0}
if __name__=='__main__':
    report=verify('web/dist'); write_json('data/reports/firebase_artifact.json',report); print(json.dumps(report))

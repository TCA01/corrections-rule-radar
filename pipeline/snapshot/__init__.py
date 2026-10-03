"""Immutable content-addressed evidence index and normalized versions."""
import json
from pathlib import Path
from pipeline.normalize import digest

def write_json(path,value):
    path=Path(path); data=(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8')
    if path.exists() and path.read_bytes()==data: return False
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp'); temp.write_bytes(data); temp.replace(path)
    return True

def save_snapshot(value):
    key=digest({k:v for k,v in value.items() if k!='evidence'})
    path=Path('data/snapshots')/value['canonical_id']/(value['version_id']+'-'+key[:16]+'.json')
    if not path.exists(): write_json(path,value)
    return str(path).replace('\\','/')

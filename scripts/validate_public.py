"""Validate complete static API, dataset consistency and resolvable references."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.validation import validate_contract,assert_schema_freeze

def validate(folder):
    assert_schema_freeze(); folder=Path(folder); manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    count=0
    for p in folder.rglob('*.json'):
        rel=p.relative_to(folder).as_posix(); value=json.loads(p.read_text(encoding='utf-8'))
        name='version' if '/versions/' in rel else 'rule' if rel.startswith('rules/') else 'changes' if rel.startswith('changes/') else p.stem
        validate_contract(name,value)
        if 'dataset_version' in value and value['dataset_version']!=manifest['dataset_version']: raise ValueError('MIXED_DATASET')
        refs=[]
        if name=='rule':
            refs=[value['articles_compared_to'],value['current']['version_reference']]
            refs += [r for v in value['upcoming'] for r in (v['version_reference'],v['articles_compared_to'])]
        elif name=='changes': refs=[r for e in value['events'] for r in (e['old_reference'],e['new_reference'],e['articles_compared_to'])]
        for ref in refs:
            if not ref: continue
            target=folder/ref['snapshot_url'].removeprefix('/api/v1/')
            if not target.resolve().is_relative_to(folder.resolve()) or not target.is_file(): raise ValueError('MISSING_VERSION_REFERENCE')
            version=json.loads(target.read_text(encoding='utf-8'))['version']
            if version['version_id']!=ref['version_id'] or version['metadata']['effective_date']!=ref['effective_date']: raise ValueError('VERSION_REFERENCE_MISMATCH')
        count+=1
    rules=json.loads((folder/'rules.json').read_text(encoding='utf-8'))['rules']
    if len(rules)!=manifest['rule_count'] or len(set(r['canonical_id'] for r in rules))!=len(rules): raise ValueError('INVALID_RULE_COUNT')
    for row in rules:
        if not (folder/row['detail_url'].removeprefix('/api/v1/')).is_file(): raise ValueError('MISSING_RULE_DETAIL')
    return {'status':'PASS','validated_files':count,'rule_count':len(rules),'dataset_version':manifest['dataset_version']}
if __name__=='__main__': print(json.dumps(validate(Path('public/api/v1'))))

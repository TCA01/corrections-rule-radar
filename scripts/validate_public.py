"""Validate complete static API, dataset consistency and resolvable references."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.validation import validate_contract,assert_schema_freeze

def validate(folder,*,contract_validator=None):
    contract_validator=contract_validator or validate_contract
    assert_schema_freeze(); folder=Path(folder); manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    count=0
    for p in folder.rglob('*.json'):
        rel=p.relative_to(folder).as_posix(); value=json.loads(p.read_text(encoding='utf-8'))
        name='version' if '/versions/' in rel else 'rule' if rel.startswith('rules/') else ('change' if p.stem.startswith('evt-') else p.stem if p.stem in ('recent','history') else 'changes') if rel.startswith('changes/') else p.stem
        contract_validator(name,value)
        if name=='ops-status':
            from datetime import datetime
            if datetime.fromisoformat(value['last_scan_completed_at']) < datetime.fromisoformat(value['last_scan_started_at']): raise ValueError('OPS_TIME_ORDER')
            if value['last_scan_current_count']>value['last_scan_rule_count']: raise ValueError('OPS_COUNT_MISMATCH')
        if 'dataset_version' in value and value['dataset_version']!=manifest['dataset_version']: raise ValueError('MIXED_DATASET')
        refs=[]
        if name=='rule':
            refs=[value['articles_compared_to'],value['current']['version_reference']]
            refs += [r for v in value['upcoming'] for r in (v['version_reference'],v['articles_compared_to'],v['cumulative_articles_compared_to'])]
            previous=value['current']['version_reference']
            for future in value['upcoming']:
                if future['articles_compared_to']!=previous: raise ValueError('UPCOMING_INCREMENTAL_BASELINE_MISMATCH')
                if future['cumulative_articles_compared_to']!=value['current']['version_reference']: raise ValueError('UPCOMING_CUMULATIVE_BASELINE_MISMATCH')
                previous=future['version_reference']
        elif name=='changes': refs=[r for e in value['events'] for r in (e['old_reference'],e['new_reference'],e['articles_compared_to'])]
        elif name in ('history','recent','change'):
            events=[value['event']] if name=='change' else value['events']
            if len({e['event_id'] for e in events})!=len(events): raise ValueError('DUPLICATE_HISTORY_EVENT')
            refs=[r for e in events for r in (e['before_version'],e['after_version'])]
            for event in events:
                if event['changed_article_count']!=len(event['changed_articles']): raise ValueError('ARTICLE_COUNT_MISMATCH')
                if event['official_old_new_available']!=(event['comparison_source'] in ('LAWGO_OLD_NEW','LAWGO_ADMIN_OLD_NEW')): raise ValueError('COMPARISON_SOURCE_MISMATCH')
                detail=folder/'changes'/(event['event_id']+'.json')
                if not detail.exists() or json.loads(detail.read_text(encoding='utf8'))['event']!=event: raise ValueError('HISTORY_DETAIL_MISMATCH')
        for ref in refs:
            if not ref: continue
            target=folder/ref['snapshot_url'].removeprefix('/api/v1/')
            if not target.resolve().is_relative_to(folder.resolve()) or not target.is_file(): raise ValueError('MISSING_VERSION_REFERENCE')
            version=json.loads(target.read_text(encoding='utf-8'))['version']
            if version['version_id']!=ref['version_id'] or version['metadata']['effective_date']!=ref['effective_date']: raise ValueError('VERSION_REFERENCE_MISMATCH')
            if 'body_hash' in ref and version['hashes']['body_hash']!=ref['body_hash']: raise ValueError('HISTORY_BODY_HASH_MISMATCH')
        count+=1
    rules=json.loads((folder/'rules.json').read_text(encoding='utf-8'))['rules']
    if len(rules)!=manifest['rule_count'] or len(set(r['canonical_id'] for r in rules))!=len(rules): raise ValueError('INVALID_RULE_COUNT')
    for row in rules:
        if not (folder/row['detail_url'].removeprefix('/api/v1/')).is_file(): raise ValueError('MISSING_RULE_DETAIL')
        if row['provenance']['canonical_source_url']!=row['official_source_url']: raise ValueError('PROVENANCE_SOURCE_MISMATCH')
        if row['provenance']['api_tracking_class']!='API_TRACKABLE' or row['provenance']['scope_review_status']!='APPROVED' or row['classification_status']!='REVIEWED' or not row['business_domains']: raise ValueError('PRODUCTION_REVIEW_OR_INELIGIBLE')
        if (row['status']=='REPEALED')!=(row['provenance']['scope_class']=='HISTORICAL_REPEALED'): raise ValueError('HISTORICAL_STATUS_MISMATCH')
    history=json.loads((folder/'changes/history.json').read_text(encoding='utf8'))['events']
    recent=json.loads((folder/'changes/recent.json').read_text(encoding='utf8'))['events']
    known={e['event_id']:e for e in history}; core={r['canonical_id'] for r in rules}
    if any(e['event_id'] not in known or known[e['event_id']]!=e for e in recent): raise ValueError('RECENT_NOT_IN_HISTORY')
    for event in history:
        if event['canonical_id'] not in core: raise ValueError('HISTORY_OUTSIDE_CORE')
        for ref in (event['before_version'],event['after_version']):
            if ref:
                v=json.loads((folder/ref['snapshot_url'].removeprefix('/api/v1/')).read_text(encoding='utf8'))['version']
                if v['canonical_id']!=event['canonical_id']: raise ValueError('HISTORY_CANONICAL_ID_MISMATCH')
    for row in rules:
        detail=json.loads((folder/row['detail_url'].removeprefix('/api/v1/')).read_text(encoding='utf8'))
        for future in detail['upcoming']:
            matching=[e for e in history if e['canonical_id']==row['canonical_id'] and e['after_version']['snapshot_url']==future['version_reference']['snapshot_url']]
            if future['changed_articles'] and len(matching)!=1: raise ValueError('UPCOMING_HISTORY_EVENT_MISSING_OR_DUPLICATE')
            for event in matching:
                if event['before_version']['snapshot_url']!=future['articles_compared_to']['snapshot_url']: raise ValueError('UPCOMING_HISTORY_BASELINE_MISMATCH')
                normalized=[{**a,'change_type':{'REMOVED':'DELETED','RENAMED':'MODIFIED'}.get(a['change_type'],a['change_type'])} for a in event['changed_articles']]
                if normalized!=future['changed_articles']: raise ValueError('UPCOMING_HISTORY_ARTICLES_MISMATCH')
    return {'status':'PASS','validated_files':count,'rule_count':len(rules),'dataset_version':manifest['dataset_version']}
if __name__=='__main__': print(json.dumps(validate(Path('public/api/v1'))))

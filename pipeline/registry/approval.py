"""Explicit one-time scope approvals, bound to reviewed structured evidence."""
import json
from collections import Counter
from pipeline.normalize import digest

def approved_candidates(report):
    candidates=[r for r in report['records'] if r['group']=='NEW_39' and r['scope_pass'] and r['eligibility_result']=='API_TRACKABLE' and r['production_eligible']]
    listed={r['canonical_id'] for r in report['final_recommended_additions']}
    if len(candidates)!=38 or listed!={r['canonical_id'] for r in candidates} or Counter(r['scope_class'] for r in candidates)!=Counter({'DIRECT_CORRECTIONS':15,'CROSS_DOMAIN_CORRECTIONS':23}): raise ValueError('APPROVED_38_SCOPE_DISCREPANCY_STOP')
    return candidates

def verify_expansion(root,state,collection):
    if collection.get('approved_expansion')=='PHASE1G':
        report=json.loads((root/'data/reports/phase1g_api_eligibility.json').read_text(encoding='utf8'))
        approval=json.loads((root/'data/registry/scope_approvals/phase1g.json').read_text(encoding='utf8'))
        old=set(state['seed_ids']); new=set(collection['snapshots']); additions=set(approval['additions'])
        if (report['status']!='PASS' or report['api_tracking_class']!='API_TRACKABLE' or report['official_title']!='형사소송법'
            or approval['status']!='APPROVED' or approval['evidence_hash']!=digest(report)
            or set(approval['previous_ids'])!=old or additions!={report['canonical_id']}
            or len(old)!=106 or len(new)!=107 or new!=old|additions or old&additions): raise ValueError('SCOPE_APPROVAL_MISMATCH')
        return True
    if collection.get('approved_expansion')!='PHASE1F': return False
    report=json.loads((root/'data/reports/phase1d_api_eligibility.json').read_text(encoding='utf8'))
    approved=approved_candidates(report)
    approval=json.loads((root/'data/registry/scope_approval.json').read_text(encoding='utf8'))
    old=set(state['seed_ids']); new=set(collection['snapshots']); additions={r['canonical_id'] for r in approved}
    if approval['evidence_hash']!=digest(report) or approval['status']!='APPROVED' or set(approval['previous_ids'])!=old or set(approval['additions'])!=additions or len(old)!=68 or len(new)!=106 or new!=old|additions or old&additions: raise ValueError('SCOPE_APPROVAL_MISMATCH')
    return True

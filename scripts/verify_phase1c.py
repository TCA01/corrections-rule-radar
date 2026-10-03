"""Audit completeness, official identity evidence and no-publication checks."""
import json
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.audit_scope import fingerprint,protected_changes,OUT
from pipeline.snapshot import write_json

def main():
    report=json.loads(Path('data/reports/phase1c_scope_audit.json').read_text(encoding='utf-8'))
    registry=json.loads(Path('data/registry/rules.json').read_text(encoding='utf-8'))
    original=json.loads((OUT/'production_before.json').read_text(encoding='utf-8'))
    records=report['current_records']; candidates=report['discovery_candidates']
    required=('canonical_id','current_name','status','scope_class','selection_basis','applies_to','official_seed_name','official_seed_url','canonical_lawgo_url','evidence','confidence','review_note')
    checks={
        'exact_registry_coverage':{r['canonical_id'] for r in registry}=={r['canonical_id'] for r in records} and len(records)==len(registry),
        'required_record_provenance':all(all(k in r for k in required) and r['selection_basis'] and r['evidence']['official_seed'] and r['evidence']['api_identity'] for r in records),
        'official_seed_complete':sum(report['official_current_seed'].values())==len(report['official_seed']) and all(r['status']=='RESOLVED' for r in report['official_seed']),
        'unique_logical_ids':not report['duplicate_logical_ids'] and len({c['canonical_id'] for c in candidates})==len(candidates),
        'discovery_only':all(c['status']=='DISCOVERY_CANDIDATE' and not c['production_member'] for c in candidates),
        'known_cross_scope_preserved':any(c['canonical_id']=='admrul-30248' and c['scope_class_candidate']=='CROSS_DOMAIN_CORRECTIONS' for c in candidates),
        'known_direct_candidates_proven':all(any(c['canonical_id']==cid and c['scope_class_candidate']=='DIRECT_CORRECTIONS' and c['official_evidence']['text_evidence'].get('purpose') for c in candidates) for cid in ('admrul-78303','admrul-97044')),
        'system_map_gaps_resolved':not report['discovery_coverage']['system_map_missing_candidates'],
        'production_contents_and_mtimes_preserved':not protected_changes(original,fingerprint()),
        'live_evidence_no_errors':not report['integrity']['errors'] and not report['supplement_failures'],
    }
    secret=os.environ.get('LAW_API_OC','').strip()
    files=list(OUT.rglob('*.json'))+list(Path('data/reports').glob('phase1c*.*'))
    checks['credential_leak_zero']=bool(secret) and not any(secret in p.read_text(encoding='utf-8') for p in files if p.is_file())
    write_json('data/reports/phase1c_verification.json',{'checks':checks,'pass_count':sum(checks.values()),'check_count':len(checks),'production_file_count':sum(not p.startswith('web') for p in original),'frontend_external_drift':sorted(p for p in original if p.startswith('web') and original[p]!=fingerprint().get(p))})
    print(json.dumps(checks))
    if not all(checks.values()): raise ValueError('AUDIT_VERIFICATION_FAILED')

if __name__=='__main__': main()

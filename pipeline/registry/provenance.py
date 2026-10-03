"""Release-approved scope is preserved by stable ID, never inferred by a UI."""
import copy

def apply_provenance(collection,registry=None):
    result=copy.deepcopy(collection)
    mappings=(registry or {}).get('rules',{})
    for row in result['registry']:
        cid=row['canonical_id']; source=row.get('provenance') or mappings.get(cid)
        if not source: raise ValueError('APPROVED_PROVENANCE_MISSING')
        row['provenance']=copy.deepcopy(source)
        row['provenance']['canonical_source_url']=result['snapshots'][cid]['official_source_url']
        if row.get('status')=='REPEALED': row['provenance']['scope_class']='HISTORICAL_REPEALED'
        if row['provenance']['scope_review_status']!='APPROVED' or row['provenance']['api_tracking_class']!='API_TRACKABLE': raise ValueError('INELIGIBLE_PRODUCTION_PROVENANCE')
    return result

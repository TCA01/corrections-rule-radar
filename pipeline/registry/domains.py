"""Apply reviewed mappings only to the exact reviewed official content."""
import copy

def apply_domains(collection,domain_registry):
    result=copy.deepcopy(collection)
    if domain_registry is None: return result
    mappings={r['canonical_id']:r for r in domain_registry['rules']}
    for rule in result['registry']:
        cid=rule['canonical_id']; mapping=mappings.get(cid); snapshot=result['snapshots'][cid]
        basis=mapping['classification_basis'] if mapping else {}
        verified=bool(mapping and mapping['review_status']=='REVIEWED' and mapping['current_name']==snapshot['metadata']['name'] and basis.get('body_hash')==snapshot['hashes']['body_hash'] and basis.get('metadata_hash')==snapshot['hashes']['metadata_hash'])
        rule['primary_domain']=mapping['primary_domain'] if verified else None
        rule['secondary_domains']=mapping['secondary_domains'] if verified else []
        rule['business_domains']=([rule['primary_domain']]+rule['secondary_domains']) if verified else []
        rule['classification_status']='REVIEWED' if verified else 'REVIEW'
    return result

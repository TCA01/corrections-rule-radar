"""Validate every file before switching the local dataset; keep a rollback copy."""
import json
import os
import uuid
from pathlib import Path
from pipeline.normalize import digest
from pipeline.snapshot import write_json
from pipeline.validation import validate_contract,assert_schema_freeze
from pipeline.publication.versions import index_snapshots,enrich_event,reference,url
from pipeline.diff.articles import changed_articles

SCHEMA_VERSION='1.2'

def public_snapshot(s,status='HISTORICAL'):
    return {**{k:s[k] for k in ('canonical_id','source_kind','stable_identifier','version_id','metadata','body','appendices','attachments','official_source_url','hashes')},'version_status':status,'version_reference':reference(s)}

def build_contract(collection,events,published_at,history=None):
    summaries=[]; files={}; future=collection['future']
    index=index_snapshots(collection,history or [])
    events=[enrich_event(e,index,collection['snapshots'].get(e['canonical_id'])) for e in events]
    for r in sorted(collection['registry'],key=lambda r:r['canonical_id']):
        cid=r['canonical_id']; s=collection['snapshots'][cid]
        summary={'canonical_id':cid,'source_kind':r['source_kind'],'current_name':r['current_name'],'seed_names':r['seed_names'],'historical_names':r['historical_names'],'corrections_category':r['corrections_category'],'business_domains':r['business_domains'],'primary_domain':r.get('primary_domain'),'secondary_domains':r.get('secondary_domains',[]),'classification_status':r['classification_status'],'status':r.get('status','CURRENT'),'version_id':s['version_id'],'metadata':s['metadata'],'official_source_url':s['official_source_url'],'detail_url':'/api/v1/rules/'+cid+'.json'}
        summaries.append(summary)
        prior=[v for v in index.values() if v['canonical_id']==cid and v['metadata']['effective_date']<s['metadata']['effective_date']]
        old=max(prior,key=lambda v:(v['metadata']['effective_date'],v['metadata']['issue_date'] or '',v['version_id'])) if prior else None
        upcoming=[{**public_snapshot(v,'FUTURE'),'changed_articles':changed_articles(s,v),'articles_compared_to':reference(s)} for v in future.get(cid,[])]
        files['rules/'+cid+'.json']=('rule',{'schema_version':SCHEMA_VERSION,'rule':summary,'current':public_snapshot(s,summary['status']),'upcoming':upcoming,'changed_articles':changed_articles(old,s),'articles_compared_to':reference(old) if old else None})
    needed={url(s):s for s in list(collection['snapshots'].values())+[s for vs in future.values() for s in vs]}
    for s in history or []:
        if s.get('version_status')=='ARCHIVE': needed[url(s)]=s
    for e in events:
        for ref in (e['old_reference'],e['new_reference'],e['articles_compared_to']):
            if ref:
                needed[ref['snapshot_url']]=next(s for s in index.values() if url(s)==ref['snapshot_url'])
    for name,value in files.values():
        if name=='rule' and value['articles_compared_to']:
            ref=value['articles_compared_to']; needed[ref['snapshot_url']]=next(v for v in index.values() if url(v)==ref['snapshot_url'])
    # Version snapshots are immutable and have a stable ARCHIVE status. Current /
    # future placement belongs to the rule detail, not the content-addressed file.
    # Preserve already-frozen archive format/bytes at existing immutable URLs.
    for path,s in needed.items(): files[path.removeprefix('/api/v1/')]=('version',{'schema_version':'1.1','version':public_snapshot(s,'ARCHIVE')})
    semantic={'schema_version':SCHEMA_VERSION,'rules':summaries,'snapshots':{k:public_snapshot(v) for k,v in collection['snapshots'].items()},'future':{k:[public_snapshot(v) for v in vs] for k,vs in future.items()},'events':events,'article_comparisons':{k:{'changed_articles':v['changed_articles'],'articles_compared_to':v['articles_compared_to'],'upcoming':v['upcoming']} for k,(n,v) in files.items() if n=='rule'}}
    version='ds-'+digest(semantic)
    upcoming_ids={(s['canonical_id'],s['version_id'],s['metadata']['effective_date']) for versions in future.values() for s in versions}
    latest=[e for e in events if (e['canonical_id'],e['new_version'],e['effective_date']) not in upcoming_ids]
    upcoming=[e for e in events if (e['canonical_id'],e['new_version'],e['effective_date']) in upcoming_ids]
    common={'schema_version':SCHEMA_VERSION,'dataset_version':version}
    for rel,(schema,value) in list(files.items()):
        if schema=='rule': files[rel]=(schema,{**value,'dataset_version':version})
    files['rules.json']=('rules',{**common,'rules':summaries})
    files['changes/latest.json']=('changes',{**common,'events':latest})
    files['changes/upcoming.json']=('changes',{**common,'events':upcoming})
    files['health.json']=('health',{**common,'status':'OK','last_successful_sync':published_at,'publication_status':'PUBLISHED','rule_count':len(summaries),'review_count':0,'classification_review_count':sum(s['classification_status']=='REVIEW' for s in summaries),'health_scope':'PUBLISHED_DATASET'})
    files['manifest.json']=('manifest',{**common,'published_at':published_at,'rules_url':'/api/v1/rules.json','latest_changes_url':'/api/v1/changes/latest.json','upcoming_changes_url':'/api/v1/changes/upcoming.json','health_url':'/api/v1/health.json','rule_count':len(summaries),'API_V1_CANDIDATE':True})
    return version,files

def publish(files,root):
    assert_schema_freeze()
    root=Path(root).resolve(); output=root/'public/api/v1'; staging=root/'data/staging'/('public-'+uuid.uuid4().hex); backup=root/'data/staging'/('backup-'+uuid.uuid4().hex)
    for p in (output,staging,backup):
        if not p.is_relative_to(root): raise ValueError('PUBLICATION_PATH_ESCAPE')
    for rel,(name,value) in files.items():
        path=staging/rel
        if not path.resolve().is_relative_to(staging): raise ValueError('PUBLICATION_PATH_ESCAPE')
        validate_contract(name,value); write_json(path,value)
    output.parent.mkdir(parents=True,exist_ok=True)
    existed=output.exists()
    if existed: os.replace(output,backup)
    try: os.replace(staging,output)
    except Exception:
        if existed: os.replace(backup,output)
        raise ValueError('PUBLICATION_ROLLED_BACK') from None
    return output

"""Materialize self-contained JSON Schema contracts for TS/Kotlin generation."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.snapshot import write_json
from pipeline.diff import EVENT_TYPES

def obj(properties,required=None): return {'type':'object','properties':properties,'required':required if required is not None else list(properties),'additionalProperties':False}
def arr(items): return {'type':'array','items':items}
S={'type':'string'}; NS={'type':['string','null']}; D={'type':['string','null'],'format':'date'}; TS={'type':'string','format':'date-time'}; ID={'type':'string','pattern':r'^(law|admrul)-\d+$'}; H={'type':'string','pattern':'^[a-f0-9]{64}$'}; URL={'type':'string','format':'uri','pattern':r'^https://(www\.)?law\.go\.kr/'}; NURL={'anyOf':[URL,{'type':'null'}]}; N={'type':'integer','minimum':0}
META=obj({'name':S,'rule_type':NS,'issue_date':D,'issue_number':NS,'effective_date':D,'ministry':NS,'department':NS,'amendment_type':NS,'official_state':NS})
HASHES=obj({k:H for k in ('metadata_hash','body_hash','appendix_hash','attachment_link_hash')})
APP=obj({'title':NS,'type':NS,'sequence':S,'branch':S,'url':NURL,'pdf_url':NURL})
ATT=obj({'title':NS,'url':NURL,'type':{'const':'OFFICIAL_ATTACHMENT'}})
REF=obj({'version_id':S,'effective_date':D,'snapshot_url':{'type':'string','pattern':r'^/api/v1/rules/(law|admrul)-\d+/versions/\d+-\d{4}-\d{2}-\d{2}-[a-f0-9]{16}\.json$'},'official_source_url':URL})
DOM={'enum':['수용·보안','접견·외부교통','보관금품','분류·가석방','교육·교화','작업·직업훈련','급식·복지','의료','심리치료','인권·청원','민원','인사·조직','정보화','민영교도소','기타']}
SNAP=obj({'canonical_id':ID,'source_kind':{'enum':['law','admrul']},'stable_identifier':{'type':'string','pattern':'^\d+$'},'version_id':S,'metadata':META,'body':obj({'articles':{},'addenda':{}}),'appendices':arr(APP),'attachments':arr(ATT),'official_source_url':URL,'hashes':HASHES,'version_status':{'enum':['CURRENT','FUTURE','REPEALED','REVIEW','HISTORICAL','ARCHIVE']},'version_reference':REF})
RULE=obj({'canonical_id':ID,'source_kind':{'enum':['law','admrul']},'current_name':S,'seed_names':arr(S),'historical_names':arr(S),'corrections_category':{'enum':['법률','대통령령','법무부령','예규','훈령']},'business_domains':arr({'enum':['수용·보안','접견·외부교통','보관금품','분류·가석방','교육·교화','작업·직업훈련','급식·복지','의료','심리치료','인권·청원','민원','인사·조직','정보화','민영교도소','기타']}),'classification_status':{'enum':['REVIEW','REVIEWED']},'status':{'enum':['CURRENT','REPEALED','REVIEW']},'version_id':S,'metadata':META,'official_source_url':URL,'detail_url':{'type':'string','pattern':r'^/api/v1/rules/(law|admrul)-\d+\.json$'}})
EVENT=obj({'event_id':{'type':'string','pattern':'^evt-[a-f0-9]{64}$'},'canonical_id':ID,'change_type':{'enum':list(EVENT_TYPES)},'old_version':NS,'new_version':S,'effective_date':D,'old_hashes':{'anyOf':[HASHES,{'type':'null'}]},'new_hashes':HASHES,'evidence':{'type':'object'},'detected_at':TS,'official_source_url':URL})
RULE['properties'].update({'primary_domain':{'anyOf':[DOM,{'type':'null'}]},'secondary_domains':arr(DOM)})
RULE['required']+=['primary_domain','secondary_domains']
EVENT['properties'].update({'old_reference':{'anyOf':[REF,{'type':'null'}]},'new_reference':REF})
EVENT['required']+=['old_reference','new_reference']
COMMON={'schema_version':{'const':'1.1'},'dataset_version':{'type':'string','pattern':'^ds-[a-f0-9]{64}$'}}
ARTICLE=obj({'article_key':S,'article_number':S,'article_title':S,'change_type':{'enum':['ADDED','MODIFIED','DELETED']},'before_text':NS,'after_text':NS,'effective_date':D})
COMPARISON={'changed_articles':arr(ARTICLE),'articles_compared_to':{'anyOf':[REF,{'type':'null'}]}}
COMPARED_SNAP={**SNAP,'properties':{**SNAP['properties'],**COMPARISON},'required':SNAP['required']+list(COMPARISON)}
EVENT['properties'].update(COMPARISON); EVENT['required']+=list(COMPARISON)
COMMON['schema_version']={'const':'1.2'}
contracts={
 'manifest':obj({**COMMON,'published_at':TS,'rules_url':{'const':'/api/v1/rules.json'},'latest_changes_url':{'const':'/api/v1/changes/latest.json'},'upcoming_changes_url':{'const':'/api/v1/changes/upcoming.json'},'health_url':{'const':'/api/v1/health.json'},'rule_count':N,'API_V1_CANDIDATE':{'const':True}}),
 'rules':obj({**COMMON,'rules':arr(RULE)}),
 'rule':obj({**COMMON,'rule':RULE,'current':SNAP,'upcoming':arr(COMPARED_SNAP),**COMPARISON}),
 'version':obj({'schema_version':{'const':'1.1'},'version':SNAP}),
 'changes':obj({**COMMON,'events':arr(EVENT)}),
 'health':obj({**COMMON,'status':{'enum':['OK','DEGRADED']},'last_successful_sync':TS,'publication_status':{'enum':['PUBLISHED','BLOCKED']},'rule_count':N,'review_count':N,'classification_review_count':N,'health_scope':{'const':'PUBLISHED_DATASET'}})
}
for name,schema in contracts.items(): write_json('schemas/'+name+'.schema.json',{'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:corrections-rule-radar:api:v1:'+name,'title':name,**schema})

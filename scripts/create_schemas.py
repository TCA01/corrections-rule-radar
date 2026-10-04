"""Materialize self-contained JSON Schema contracts for TS/Kotlin generation."""
import sys
import copy
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
DOM={'enum':['수용·보안','접견·외부교통','보관금품','분류·가석방','교육·교화','작업·직업훈련','급식·복지','의료','심리치료','인권·청원','민원','인사·조직','정보화','민영교도소','보고','기타']}
SNAP=obj({'canonical_id':ID,'source_kind':{'enum':['law','admrul']},'stable_identifier':{'type':'string','pattern':'^\d+$'},'version_id':S,'metadata':META,'body':obj({'articles':{},'addenda':{}}),'appendices':arr(APP),'attachments':arr(ATT),'official_source_url':URL,'hashes':HASHES,'version_status':{'enum':['CURRENT','FUTURE','REPEALED','REVIEW','HISTORICAL','ARCHIVE']},'version_reference':REF})
RULE=obj({'canonical_id':ID,'source_kind':{'enum':['law','admrul']},'current_name':S,'seed_names':arr(S),'historical_names':arr(S),'corrections_category':{'enum':['법률','대통령령','법무부령','예규','훈령']},'business_domains':arr({'enum':['수용·보안','접견·외부교통','보관금품','분류·가석방','교육·교화','작업·직업훈련','급식·복지','의료','심리치료','인권·청원','민원','인사·조직','정보화','민영교도소','기타']}),'classification_status':{'enum':['REVIEW','REVIEWED']},'status':{'enum':['CURRENT','REPEALED','REVIEW']},'version_id':S,'metadata':META,'official_source_url':URL,'detail_url':{'type':'string','pattern':r'^/api/v1/rules/(law|admrul)-\d+\.json$'}})
EVENT=obj({'event_id':{'type':'string','pattern':'^evt-[a-f0-9]{64}$'},'canonical_id':ID,'change_type':{'enum':list(EVENT_TYPES)},'old_version':NS,'new_version':S,'effective_date':D,'old_hashes':{'anyOf':[HASHES,{'type':'null'}]},'new_hashes':HASHES,'evidence':{'type':'object'},'detected_at':TS,'official_source_url':URL})
RULE['properties'].update({'primary_domain':{'anyOf':[DOM,{'type':'null'}]},'secondary_domains':arr(DOM)})
RULE['required']+=['primary_domain','secondary_domains']
ARCHIVE_SNAP=copy.deepcopy(SNAP)
CURRENT_APP=obj({**APP['properties'],'status':{'enum':['AVAILABLE','REMOVED']}})
SNAP['properties']['appendices']=arr(CURRENT_APP)
RULE['properties']['business_domains']=arr(DOM)
RULE['properties']['corrections_category']['enum'].append('지침')
PROVENANCE=obj({'scope_class':{'enum':['OFFICIAL_CORRECTIONS_LIST','DIRECT_CORRECTIONS','CROSS_DOMAIN_CORRECTIONS','HISTORICAL_REPEALED']},
 'selection_basis':{'type':'string','minLength':1},'applies_to':{'type':'array','minItems':1,'items':S},
 'official_seed_name':NS,'official_seed_url':{'anyOf':[{'type':'string','format':'uri','pattern':r'^https://www\.corrections\.go\.kr/'},{'type':'null'}]},
 'canonical_source_url':URL,'discovery_source':{'type':'array','minItems':1,'items':{'enum':['CORRECTIONS_PAGE','LAW_API_KEYWORD','LAW_API_MINISTRY','CORE_SYSTEM_MAP','MANUAL_OFFICIAL_REVIEW']}},
 'scope_review_status':{'const':'APPROVED'},'api_tracking_class':{'const':'API_TRACKABLE'},
 'structured_body_source':{'const':'LAWGO_JSON_XML'},'history_source':{'const':'LAWGO_STRUCTURED_HISTORY'},'appendix_metadata_source':{'const':'LAWGO_STRUCTURED_METADATA'}})
RULE['properties'].update({'provenance':PROVENANCE,'domain_assignment_status':{'enum':['EVIDENCE_BASED','FALLBACK']}})
RULE['required']+=['provenance','domain_assignment_status']
EVENT['properties'].update({'old_reference':{'anyOf':[REF,{'type':'null'}]},'new_reference':REF})
EVENT['required']+=['old_reference','new_reference']
COMMON={'schema_version':{'const':'1.1'},'dataset_version':{'type':'string','pattern':'^ds-[a-f0-9]{64}$'}}
ARTICLE=obj({'article_key':S,'article_number':S,'article_title':S,'change_type':{'enum':['ADDED','MODIFIED','DELETED']},'before_text':NS,'after_text':NS,'effective_date':D})
COMPARISON={'changed_articles':arr(ARTICLE),'articles_compared_to':{'anyOf':[REF,{'type':'null'}]}}
COMPARED_SNAP={**SNAP,'properties':{**SNAP['properties'],**COMPARISON},'required':SNAP['required']+list(COMPARISON)}
UPCOMING_COMPARISON={'comparison_mode':{'const':'PREVIOUS_EFFECTIVE_STATE'},'comparison_source':{'const':'STRUCTURED_SNAPSHOT_DIFF'},
 'cumulative_changed_articles':arr(ARTICLE),'cumulative_articles_compared_to':REF,
 'cumulative_comparison_mode':{'const':'CURRENT_BASELINE'},'cumulative_comparison_source':{'const':'STRUCTURED_SNAPSHOT_DIFF'}}
COMPARED_SNAP['properties'].update(UPCOMING_COMPARISON); COMPARED_SNAP['required']+=list(UPCOMING_COMPARISON)
EVENT['properties'].update(COMPARISON); EVENT['required']+=list(COMPARISON)
COMMON['schema_version']={'const':'1.5'}
PREF=obj({**REF['properties'],'identifier':S,'body_hash':H})
PARTICLE={**ARTICLE,'properties':{**ARTICLE['properties'],'change_type':{'enum':['ADDED','REMOVED','MODIFIED','RENAMED','UNKNOWN_STRUCTURAL_CHANGE']}}}
APPCHANGE=obj({'change_type':{'enum':['APPENDIX_ADDED','APPENDIX_REMOVED','APPENDIX_METADATA_CHANGED']},'status':{'enum':['AVAILABLE','REMOVED']},'before_metadata':{'anyOf':[APP,{'type':'null'}]},'after_metadata':{'anyOf':[APP,{'type':'null'}]}})
PEVENT=obj({'event_id':EVENT['properties']['event_id'],'canonical_id':ID,'regulation_name':S,'regulation_type':NS,
 'change_type':{'enum':['RULE_AMENDED','RULE_RENAMED','ARTICLE_CHANGED','RULE_REPEALED','NEW_RULE','HISTORICAL_VERSION','METADATA_CORRECTED','EFFECTIVE_DATE_CORRECTED','STAGED_EFFECTIVE_DATE','APPENDIX_ADDED','APPENDIX_REMOVED','APPENDIX_METADATA_CHANGED']},
 'change_types':arr(S),'detected_at':TS,'promulgation_or_issue_date':D,'effective_date':{'type':'string','format':'date'},
 'before_version':{'anyOf':[PREF,{'type':'null'}]},'after_version':PREF,'changed_articles':arr(PARTICLE),'changed_article_count':N,'appendix_changes':arr(APPCHANGE),
 'official_old_new_available':{'type':'boolean'},'comparison_source':{'enum':['LAWGO_OLD_NEW','LAWGO_ADMIN_OLD_NEW','STRUCTURED_SNAPSHOT_DIFF',None]},
 'comparison_scope':{'enum':['FULL_STRUCTURED_BODY','OFFICIAL_COMPARISON_EXCERPT']},'comparison_status':{'enum':['AVAILABLE','COMPARISON_UNAVAILABLE']},
 'comparison_unavailable_reason':NS,'fallback_reason':NS,'comparison_evidence':{'type':['object','null']},'official_source_url':URL})
PEVENT['properties']['staged_effective_evidence']=obj({'source':{'const':'LAWGO_STRUCTURED_ADDENDUM'},'issue_number':S,'before_effective_date':D,'after_effective_date':D,'before_body_hash':H,'after_body_hash':H,'commencement_clause':S})
contracts={
 'manifest':obj({**COMMON,'published_at':TS,'rules_url':{'const':'/api/v1/rules.json'},'latest_changes_url':{'const':'/api/v1/changes/latest.json'},'upcoming_changes_url':{'const':'/api/v1/changes/upcoming.json'},'health_url':{'const':'/api/v1/health.json'},'rule_count':N,'API_V1_CANDIDATE':{'const':True}}),
 'rules':obj({**COMMON,'rules':arr(RULE)}),
 'rule':obj({**COMMON,'rule':RULE,'current':SNAP,'upcoming':arr(COMPARED_SNAP),**COMPARISON}),
 'version':obj({'schema_version':{'const':'1.1'},'version':ARCHIVE_SNAP}),
 'changes':obj({**COMMON,'events':arr(EVENT)}),
 'health':obj({**COMMON,'status':{'enum':['OK','DEGRADED']},'last_successful_sync':TS,'publication_status':{'enum':['PUBLISHED','BLOCKED']},'rule_count':N,'review_count':N,'classification_review_count':N,'health_scope':{'const':'PUBLISHED_DATASET'}})
}
contracts['manifest']['properties'].update({'recent_changes_url':{'const':'/api/v1/changes/recent.json'},'history_changes_url':{'const':'/api/v1/changes/history.json'},'change_detail_url_template':{'const':'/api/v1/changes/{event_id}.json'}})
contracts['manifest']['required']+=['recent_changes_url','history_changes_url','change_detail_url_template']
contracts['history']=obj({**COMMON,'retention':{'const':'INDEFINITE'},'events':arr(PEVENT)})
contracts['recent']=obj({**COMMON,'window_days':{'const':90},'date_basis':{'const':'EFFECTIVE_DATE_SEOUL'},'events':arr(PEVENT)})
contracts['change']=obj({'schema_version':{'enum':['1.3','1.4','1.5']},'event':PEVENT})
for name,schema in contracts.items(): write_json('schemas/'+name+'.schema.json',{'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:corrections-rule-radar:api:v1:'+name,'title':name,**schema})

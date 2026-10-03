"""Discovery never enrolls an identity in the trusted registry."""
from pipeline.normalize import digest

def candidate(identifier,name,official_url,source):
    if source not in ('CORRECTIONS_SEED','MINISTRY_OF_JUSTICE','SYSTEM_MAP'): raise ValueError('UNTRUSTED_DISCOVERY_SOURCE')
    return {'event_id':'candidate-'+digest([source,identifier]),'change_type':'DISCOVERY_CANDIDATE','identifier':identifier,'name':name,'official_source_url':official_url,'source':source,'review_status':'REVIEW','trusted':False}

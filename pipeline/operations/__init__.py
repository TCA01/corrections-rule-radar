"""Ops timestamps are separate from public dataset identity."""
from datetime import datetime,timezone,timedelta

def now(): return datetime.now(timezone.utc).isoformat()

def heartbeat_due(last_repository_change,at):
    return datetime.fromisoformat(at)-datetime.fromisoformat(last_repository_change)>=timedelta(days=30)

def health(collection,at,previous=None):
    previous=previous or {}; failures=sum(r['status']!='RESOLVED' for r in collection['resolution'])
    complete=collection.get('complete',False)
    blocked=not complete or failures>0 or len(collection['registry'])!=len(collection['resolution'])
    return {'last_attempt':at,'last_successful_sync':previous.get('last_successful_sync') if blocked else at,'api_status':'DEGRADED' if failures else 'OK' if complete else 'INCOMPLETE','core_registry_total':len(collection['resolution']),'success_count':len(collection['registry']),'review_count':failures,'failure_count':failures,'publication_status':'BLOCKED' if blocked else 'VALIDATED','last_dataset_version':previous.get('last_dataset_version')}

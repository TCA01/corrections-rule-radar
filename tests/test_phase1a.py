import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from pipeline.law_api import ApiError
from pipeline.operations.metrics import Metrics
from pipeline.publication import build_contract
from pipeline.publication.versions import url
from pipeline.registry.domains import apply_domains
from pipeline.diff import compare
from pipeline.normalize import digest
from pipeline.snapshot import write_json
from scripts import observe,sync
from test_pipeline import evidence_collection,baseline_law,load,ROOT,AT,Opener,SECRET

class Phase1ATests(unittest.TestCase):
    def setUp(self): self.collection=evidence_collection()
    def test_metric_counts_include_retries_without_parameters(self):
        import urllib.error
        from pipeline.law_api import LawClient
        err=urllib.error.HTTPError('https://example/?OC='+SECRET,500,'',{},None)
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'LAW_API_OC':SECRET}),patch('time.sleep'):
            metrics=Metrics(); c=LawClient(metrics=metrics,opener=Opener([err,b'{"LawSearch":{"totalCnt":0}}']),cache=tmp,interval=0)
            c.fetch(target='law'); report=metrics.report()
            self.assertEqual(report['api_request_count'],2); self.assertEqual(report['retry_count'],1); self.assertEqual(report['transport_error_summary'],{'HTTP_ERROR':1}); self.assertNotIn(SECRET,json.dumps(report))
    def test_success_failure_success_recovery_with_observer(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(sync,'ROOT',Path(tmp)),patch.object(observe,'ROOT',Path(tmp)),patch.dict(os.environ,{'LAW_API_OC':SECRET}):
            with patch.object(observe,'collect',return_value=self.collection):
                first=observe.observe_once()
            before=observe.public_fingerprint(tmp); previous=load(Path(tmp)/'data/ops/health.json')
            with patch.object(observe,'collect',side_effect=ApiError('TIMEOUT')):
                failure=observe.observe_once()
            degraded=load(Path(tmp)/'data/ops/health.json')
            self.assertEqual(failure['publication_status'],'BLOCKED'); self.assertEqual(before,observe.public_fingerprint(tmp)); self.assertEqual(degraded['last_successful_sync'],previous['last_successful_sync']); self.assertEqual(degraded['last_dataset_version'],previous['last_dataset_version'])
            with patch.object(observe,'collect',return_value=self.collection):
                recovered=observe.observe_once()
            restored=load(Path(tmp)/'data/ops/health.json')
            self.assertEqual(recovered['publication_status'],'NO_CHANGE'); self.assertEqual(recovered['change_count'],0); self.assertEqual(before,observe.public_fingerprint(tmp)); self.assertEqual(restored['api_status'],'OK'); self.assertGreater(restored['last_successful_sync'],previous['last_successful_sync'])
            reports=list((Path(tmp)/'data/reports/observation').glob('*.json')); self.assertEqual(len(reports),3)
            write_json(ROOT/'data/reports/observation_recovery.json',{'status':'PASS','mode':'SIMULATED_API_TIMEOUT_AFTER_SUCCESS','transitions':[first['publication_status'],failure['publication_status'],recovered['publication_status']],'last_good_public_state_preserved':True,'last_successful_sync_preserved_during_failure':True,'api_health_restored':True})
    def test_partial_failure_then_recovery(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(sync,'ROOT',Path(tmp)):
            sync.sync(self.collection); before=observe.public_fingerprint(tmp)
            broken=copy.deepcopy(self.collection); broken['resolution'][0].update({'status':'REVIEW','review_reason':'HTTP_ERROR'})
            self.assertEqual(sync.sync(broken)['result'],'BLOCKED'); self.assertEqual(before,observe.public_fingerprint(tmp))
            self.assertEqual(sync.sync(self.collection)['result'],'NO_CHANGE'); self.assertEqual(before,observe.public_fingerprint(tmp))
    def test_domain_registry_complete_and_evidence_bound(self):
        domains=load(ROOT/'data/registry/business_domains.json'); core=set(self.collection['snapshots'])
        self.assertTrue(core<=set(r['canonical_id'] for r in domains['rules']))
        taxonomy=load(ROOT/'data/seed/business_domains.json')['domains']
        for rule in domains['rules']:
            basis=rule['classification_basis']; self.assertEqual(basis['reviewer'],'CODEX_EVIDENCE_REVIEW'); self.assertFalse(basis['legal_interpretation']); self.assertTrue(basis['official_source_url'].startswith('https://www.law.go.kr/'))
            if rule['review_status']=='REVIEWED': self.assertIn(rule['primary_domain'],taxonomy)
            else: self.assertIsNone(rule['primary_domain'])
            self.assertTrue(set(rule['secondary_domains'])<=set(taxonomy)); self.assertNotIn(rule['primary_domain'],rule['secondary_domains'])
    def test_changed_body_invalidates_classification(self):
        domains=load(ROOT/'data/registry/business_domains.json'); collection=copy.deepcopy(self.collection)
        mapping=next(r for r in domains['rules'] if r['review_status']=='REVIEWED'); cid=mapping['canonical_id']
        collection['snapshots'][cid]['hashes']['body_hash']='0'*64
        applied=apply_domains(collection,domains); row=next(r for r in applied['registry'] if r['canonical_id']==cid)
        self.assertEqual(row['classification_status'],'REVIEWED'); self.assertEqual(row['business_domains'],['기타']); self.assertEqual(row['domain_assignment_status'],'FALLBACK')
    def test_event_old_new_references_resolve_to_real_versions(self):
        case=load(ROOT/'tests/fixtures/admin_replay.json'); new=case['new']; old=case['old']; cid=new['canonical_id']
        collection=copy.deepcopy(self.collection); collection['snapshots'][cid]=new
        events=compare(old,new,AT); _,files=build_contract(collection,events,AT,history=[old])
        for e in files['changes/latest.json'][1]['events']:
            self.assertEqual(e['old_reference']['version_id'],old['version_id']); self.assertEqual(e['new_reference']['version_id'],new['version_id'])
            for ref in (e['old_reference'],e['new_reference']): self.assertIn(ref['snapshot_url'].removeprefix('/api/v1/'),files)
    def test_missing_old_snapshot_blocks_event_publication(self):
        case=load(ROOT/'tests/fixtures/admin_replay.json'); events=compare(case['old'],case['new'],AT)
        with self.assertRaisesRegex(ValueError,'REFERENCE_MISSING'): build_contract(self.collection,events,AT)
    def test_archive_url_distinguishes_same_serial_effective_dates(self):
        s=copy.deepcopy(next(iter(self.collection['snapshots'].values()))); other=copy.deepcopy(s); other['metadata']['effective_date']='2099-01-01'
        self.assertNotEqual(url(s),url(other))
    def test_contract_candidate_current_future_health_and_domains(self):
        domains=load(ROOT/'data/registry/business_domains.json'); collection=apply_domains(baseline_law(self.collection),domains)
        _,files=build_contract(collection,[],AT)
        self.assertTrue(files['manifest.json'][1]['API_V1_CANDIDATE']); self.assertEqual(files['manifest.json'][1]['schema_version'],'1.4')
        detail=files['rules/law-001668.json'][1]
        self.assertEqual(detail['current']['version_status'],'CURRENT'); self.assertEqual(detail['upcoming'][0]['version_status'],'FUTURE'); self.assertIn('dataset_version',detail)
        self.assertEqual(files['health.json'][1]['health_scope'],'PUBLISHED_DATASET'); self.assertEqual(files['health.json'][1]['classification_review_count'],sum(r['classification_status']=='REVIEW' for r in collection['registry']))
    def test_schema_drift_is_blocked(self):
        from pipeline.validation import assert_schema_freeze
        self.assertTrue(assert_schema_freeze())
        actual_read=Path.read_bytes
        def drift(path):
            content=actual_read(path)
            return content+b' ' if path.name=='rule.schema.json' else content
        with patch.object(Path,'read_bytes',drift):
            with self.assertRaisesRegex(ValueError,'SCHEMA_DRIFT'): assert_schema_freeze()
    def test_current_real_examples_keep_official_versions_and_compare(self):
        # These are regression examples, never production classification/diff rules.
        cases={'admrul-36282':('2026-10-01','1389'),'admrul-36283':('2026-10-01','1390'),'admrul-35334':('2026-03-30','1384')}
        for cid,(effective,number) in cases.items():
            archived=[load(p) for p in (ROOT/'data/snapshots'/cid).glob('*.json')]
            current=next(s for s in archived if s['metadata']['effective_date']==effective and s['metadata']['issue_number']==number)
            self.assertEqual(current['metadata']['effective_date'],effective); self.assertEqual(current['metadata']['issue_number'],number)
            older=[s for s in archived if s['metadata']['effective_date']<effective]
            self.assertTrue(older)
            old=max(older,key=lambda s:s['metadata']['effective_date'])
            events=compare(old,current,AT); self.assertTrue(events)
            replay=copy.deepcopy(self.collection); replay['snapshots'][cid]=current
            _,files=build_contract(replay,events,AT,history=[old])
            for event in files['changes/latest.json'][1]['events']:
                for ref in (event['old_reference'],event['new_reference']): self.assertIn(ref['snapshot_url'].removeprefix('/api/v1/'),files)
        law=baseline_law(self.collection)['future']['law-001668'][0]
        self.assertEqual(law['metadata']['effective_date'],'2026-12-24')
        self.assertNotEqual(law['version_id'],baseline_law(self.collection)['snapshots']['law-001668']['version_id'])
    def test_actual_public_references_and_dataset_consistency(self):
        public=ROOT/'public/api/v1'; manifest=load(public/'manifest.json')
        for p in public.rglob('*.json'):
            value=load(p)
            if 'dataset_version' in value: self.assertEqual(value['dataset_version'],manifest['dataset_version'])
            if 'current' in value:
                refs=[value['current']['version_reference']]+[v['version_reference'] for v in value['upcoming']]
            else:
                events=[value['event']] if 'event' in value else value.get('events',[])
                refs=[r for e in events for r in ((e['before_version'],e['after_version']) if 'after_version' in e else (e['old_reference'],e['new_reference'])) if r]
            for ref in refs:
                path=public/ref['snapshot_url'].removeprefix('/api/v1/'); self.assertTrue(path.exists())
                version=load(path)['version']; self.assertEqual(version['version_id'],ref['version_id']); self.assertEqual(version['metadata']['effective_date'],ref['effective_date'])
                if 'body_hash' in ref: self.assertEqual(version['hashes']['body_hash'],ref['body_hash'])

if __name__=='__main__': unittest.main()

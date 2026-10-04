"""Single-law admission, current production and recovery regressions."""
import copy,hashlib,json,shutil,tempfile,unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch
from pipeline.registry.approval import verify_expansion
from pipeline.normalize import digest
from pipeline.diff.history import article_groups,recent
from pipeline.operations.calendar import seoul_date
from pipeline.validation import assert_public_safe
from scripts import sync
from scripts.observe import public_fingerprint
from test_pipeline import ROOT,load,evidence_collection

class Phase1GTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.collection=evidence_collection()
        cls.evidence=load(ROOT/'data/reports/phase1g_api_eligibility.json')
        cls.cid=cls.evidence['canonical_id']
        cls.previous=load(ROOT/'tests/fixtures/phase1g_previous_core.json')
    def test_exact_scope_delta_and_status_counts(self):
        rows=self.collection['registry']
        self.assertEqual(len(rows),107)
        self.assertEqual(set(self.collection['snapshots']),set(self.previous['previous_ids'])|{self.cid})
        self.assertEqual(Counter(r['status'] for r in rows),{'CURRENT':105,'REPEALED':2})
        self.assertEqual(sum(r['current_name']=='형사소송법' for r in rows),1)
    def test_live_identity_and_structured_current_body(self):
        sn=self.collection['snapshots'][self.cid]; report=self.evidence
        self.assertEqual(report['status'],'PASS'); self.assertEqual(sn['stable_identifier'],report['stable_law_id'])
        self.assertEqual(sn['version_id'],report['current_mst']); self.assertEqual(sn['metadata']['name'],'형사소송법')
        self.assertEqual(sn['metadata']['effective_date'],report['metadata']['effective_date'])
        self.assertTrue(article_groups(sn['body'])); self.assertTrue(sn['metadata']['issue_number'])
        self.assertTrue(sn['official_source_url'].startswith('https://www.law.go.kr/'))
    def test_scope_provenance_and_existing_domain_only(self):
        row=next(r for r in self.collection['registry'] if r['canonical_id']==self.cid); p=row['provenance']
        self.assertEqual(p['scope_class'],'CROSS_DOMAIN_CORRECTIONS'); self.assertEqual(p['scope_review_status'],'APPROVED')
        self.assertEqual(p['api_tracking_class'],'API_TRACKABLE'); self.assertTrue(p['selection_basis'])
        self.assertIn('수용기록 업무',p['applies_to']); self.assertEqual(row['business_domains'],['수용·보안'])
        taxonomy=load(ROOT/'data/seed/business_domains.json')['domains']
        self.assertEqual(len(taxonomy),16); self.assertNotIn('수용기록',taxonomy)
    def test_schema_14_and_creator_not_in_public_legal_data(self):
        manifest=load(ROOT/'public/api/v1/manifest.json'); self.assertEqual(manifest['schema_version'],'1.4')
        detail=load(ROOT/f'public/api/v1/rules/{self.cid}.json'); assert_public_safe(detail)
        self.assertNotIn('Kim In-jun',json.dumps(detail,ensure_ascii=False))
        self.assertNotIn('Wonju Correctional Institution',json.dumps(detail,ensure_ascii=False))
    def test_existing_history_and_archives_are_immutable(self):
        history=load(ROOT/'data/registry/change_history.json')
        self.assertTrue(set(self.previous['event_ids'])<={e['event_id'] for e in history})
        for name,expected in self.previous['protected_hashes'].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),expected,name)
    def test_backfill_comparisons_and_recent_are_real_pipeline_events(self):
        events=[e for e in load(ROOT/'data/registry/change_history.json') if e['canonical_id']==self.cid]
        report=load(ROOT/'data/reports/phase1g_backfill.json')['records'][0]
        self.assertEqual(len(events),report['backfill_policy']['selected_version_count'])
        self.assertEqual(len({e['event_id'] for e in events}),len(events))
        self.assertTrue(any(e['official_old_new_available'] for e in events))
        self.assertTrue(any(e['comparison_source']=='STRUCTURED_SNAPSHOT_DIFF' for e in events))
        for e in events:
            self.assertEqual(e['changed_article_count'],len(e['changed_articles']))
            self.assertIsNotNone(e['before_version']); self.assertEqual(e['comparison_status'],'AVAILABLE')
        public=load(ROOT/'public/api/v1/changes/recent.json')['events']
        self.assertEqual({e['event_id'] for e in public if e['canonical_id']==self.cid},{e['event_id'] for e in recent(events,seoul_date())})
    def test_exact_approval_and_cannot_reuse_or_expand_other_laws(self):
        c=copy.deepcopy(self.collection); c['approved_expansion']='PHASE1G'; previous={'seed_ids':self.previous['previous_ids']}
        self.assertTrue(verify_expansion(ROOT,previous,c))
        with self.assertRaisesRegex(ValueError,'SCOPE_APPROVAL_MISMATCH'): verify_expansion(ROOT,{'seed_ids':list(c['snapshots'])},c)
        c['snapshots']['law-999999']=copy.deepcopy(c['snapshots'][self.cid])
        with self.assertRaisesRegex(ValueError,'SCOPE_APPROVAL_MISMATCH'): verify_expansion(ROOT,previous,c)
    def test_new_law_failure_preserves_last_good_and_recovers(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(sync,'ROOT',Path(tmp)):
            root=Path(tmp)
            for folder in ('public/api/v1','data/registry','data/ops'): shutil.copytree(ROOT/folder,root/folder)
            before=public_fingerprint(root); state=load(root/'data/registry/state.json'); good=load(root/'data/ops/health.json')
            broken=copy.deepcopy(self.collection); broken['registry']=[r for r in broken['registry'] if r['canonical_id']!=self.cid]; broken['snapshots'].pop(self.cid)
            next(r for r in broken['resolution'] if r['canonical_id']==self.cid).update(status='REVIEW',review_reason='SIMULATED_API_FAILURE')
            self.assertEqual(sync.sync(broken)['result'],'BLOCKED'); self.assertEqual(public_fingerprint(root),before)
            self.assertEqual(load(root/'data/registry/state.json'),state)
            self.assertEqual(load(root/'data/ops/health.json')['last_dataset_version'],good['last_dataset_version'])
            self.assertEqual(sync.sync(self.collection)['result'],'NO_CHANGE'); self.assertEqual(public_fingerprint(root),before)

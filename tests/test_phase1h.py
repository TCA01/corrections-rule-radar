"""Official snapshot regressions for incremental upcoming comparisons."""
import copy,json,hashlib,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from pipeline.diff.effective_states import future_pairs,full_articles,staged_evidence,reconcile_upcoming
from pipeline.diff.history import make_event
from pipeline.publication import build_contract,publish
from pipeline.law_api.comparisons import prepare
from pipeline.normalize import digest
from scripts.validate_public import validate
from scripts.observe import public_fingerprint
from scripts import sync
from test_pipeline import ROOT,AT,load,evidence_collection

class Phase1HTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=evidence_collection(); cls.cid='law-001671'; cls.current=cls.c['snapshots'][cls.cid]
        cls.pairs=future_pairs(cls.current,cls.c['future'][cls.cid])
        cls.previous=load(ROOT/'tests/fixtures/phase1h_previous_history.json')
        cls.existing=load(ROOT/'data/registry/change_history.json')
        cls.history=[load(p)['version'] for p in (ROOT/'public/api/v1/rules').glob('*/versions/*.json')]
        cls.persistent,cls.replacements=reconcile_upcoming(cls.existing,cls.c,AT)
        _,cls.files=build_contract(cls.c,load(ROOT/'data/registry/events.json'),AT,history=cls.history,persistent=cls.persistent)
        cls.detail=cls.files['rules/'+cls.cid+'.json'][1]
    def test_first_future_uses_actual_current_despite_same_date_archive(self):
        self.assertEqual(self.current['version_id'],'290189')
        self.assertTrue(any(v['version_id']=='288579' and v['metadata']['effective_date']=='2026-10-02' for v in self.history))
        first=self.detail['upcoming'][0]
        self.assertEqual(first['articles_compared_to']['version_id'],'290189')
        self.assertEqual(first['articles_compared_to']['effective_date'],'2026-10-02')
    def test_incremental_and_cumulative_counts_and_full_pairing(self):
        expected=[('2027-02-05','2026-10-02','290189',3,3),('2027-08-05','2027-02-05','288579',2,5),('2027-12-31','2027-08-05','288579',1,6)]
        for up,(day,before,mst,inc,cum) in zip(self.detail['upcoming'],expected):
            self.assertEqual(up['metadata']['effective_date'],day)
            self.assertEqual(up['articles_compared_to']['effective_date'],before)
            self.assertEqual(up['articles_compared_to']['version_id'],mst)
            self.assertEqual(len(up['changed_articles']),inc); self.assertEqual(len(up['cumulative_changed_articles']),cum)
            self.assertEqual(up['cumulative_articles_compared_to'],self.detail['current']['version_reference'])
            self.assertEqual(up['comparison_mode'],'PREVIOUS_EFFECTIVE_STATE'); self.assertEqual(up['cumulative_comparison_mode'],'CURRENT_BASELINE')
        self.assertEqual({a['article_number'] for a in self.detail['upcoming'][1]['changed_articles']},{'220의2','244의6'})
        self.assertEqual({a['article_number'] for a in self.detail['upcoming'][2]['changed_articles']},{'59의3'})
    def test_same_mst_different_efyd_and_input_order_not_deduplicated(self):
        future=self.c['future'][self.cid]
        pairs=future_pairs(self.current,list(reversed(future))+[future[0]])
        self.assertEqual(len(pairs),3)
        self.assertEqual([v['metadata']['effective_date'] for _,v in pairs],['2027-02-05','2027-08-05','2027-12-31'])
        self.assertEqual(pairs[0][1]['version_id'],pairs[1][1]['version_id'])
        self.assertNotEqual(pairs[0][1]['hashes']['body_hash'],pairs[1][1]['hashes']['body_hash'])
        first,second=pairs[0][1],pairs[1][1]
        self.assertEqual(first['evidence']['request'],{'target':'eflaw','MST':'288579','efYd':'20270205','type':'JSON'})
        self.assertEqual(second['evidence']['request'],{'target':'eflaw','MST':'288579','efYd':'20270805','type':'JSON'})
        self.assertNotEqual(first['evidence']['raw_sha256'],second['evidence']['raw_sha256'])
    def test_staged_requires_structured_addendum_and_correction_remains(self):
        before,after=self.pairs[1]; proof=staged_evidence(before,after)
        self.assertIsNotNone(proof); self.assertIn('244조의6',proof['commencement_clause'])
        event=make_event(before,after,AT)
        self.assertEqual(event['change_type'],'STAGED_EFFECTIVE_DATE'); self.assertNotIn('EFFECTIVE_DATE_CORRECTED',event['change_types'])
        corrected=copy.deepcopy(after); corrected['body']['addenda']={}
        self.assertEqual(make_event(before,corrected,AT)['change_type'],'EFFECTIVE_DATE_CORRECTED')
    def test_history_default_article_objects_equal(self):
        for up in self.detail['upcoming']:
            event=next(e for e in self.persistent if e['canonical_id']==self.cid and e['effective_date']==up['metadata']['effective_date'])
            self.assertEqual(event['before_version']['snapshot_url'],up['articles_compared_to']['snapshot_url'])
            normalized=[{**a,'change_type':{'REMOVED':'DELETED','RENAMED':'MODIFIED'}.get(a['change_type'],a['change_type'])} for a in event['changed_articles']]
            self.assertEqual(normalized,up['changed_articles'])
    def test_unaffected_event_ids_detection_times_and_archives_immutable(self):
        for event in self.persistent:
            expected=self.previous['past_event_hashes'].get(event['event_id'])
            if expected: self.assertEqual(digest(event),expected)
        self.assertTrue(set(self.previous['past_event_hashes'])<={e['event_id'] for e in self.persistent})
        for name,expected in self.previous['immutable_hashes'].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),expected,name)
        dec=next(e for e in self.persistent if e['canonical_id']==self.cid and e['effective_date']=='2027-12-31')
        self.assertEqual(dec['event_id'],self.previous['previous_future_events'][-1]['event_id'])
        again,changes=reconcile_upcoming(self.persistent,self.c,'2026-10-05T00:00:00Z')
        self.assertEqual(again,self.persistent); self.assertEqual(changes,[])
    def test_same_day_conflicting_future_fails_closed(self):
        conflict=copy.deepcopy(self.pairs[0][1]); conflict['version_id']='999999'
        with self.assertRaisesRegex(ValueError,'AMBIGUOUS_FUTURE_EFFECTIVE_DATE'): future_pairs(self.current,[self.pairs[0][1],conflict])
    def test_known_exact_pair_makes_no_api_calls(self):
        with patch('pipeline.law_api.comparisons.LawClient') as client:
            prepare(self.c,{'seed_ids':list(self.c['snapshots']),'snapshots':self.c['snapshots']},self.persistent)
            client.assert_not_called()
    def test_candidate_publication_validation_and_recovery(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(sync,'ROOT',Path(tmp)):
            root=Path(tmp)
            for folder in ('public/api/v1','data/registry','data/ops'): shutil.copytree(ROOT/folder,root/folder)
            first=sync.sync(self.c); self.assertIn(first['result'],('PUBLISHED','NO_CHANGE'))
            self.assertEqual(validate(root/'public/api/v1')['status'],'PASS')
            before=public_fingerprint(root); saved=load(root/'data/registry/change_history.json')
            broken=copy.deepcopy(self.c); broken['complete']=False
            self.assertEqual(sync.sync(broken)['result'],'BLOCKED'); self.assertEqual(public_fingerprint(root),before)
            self.assertEqual(sync.sync(self.c)['result'],'NO_CHANGE'); self.assertEqual(public_fingerprint(root),before)
            self.assertEqual(load(root/'data/registry/change_history.json'),saved)

if __name__=='__main__': unittest.main()

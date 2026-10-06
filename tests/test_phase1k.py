import copy, json, shutil, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from scripts.audit_phase1k import independent, compare
from pipeline.diff.effective_states import full_articles, future_pairs, reconcile_upcoming
from pipeline.operations.public_status import publish_status, status_hash
from pipeline.snapshot import write_json
from scripts import generated_commit

ROOT=Path(__file__).resolve().parents[1]
def load(p): return json.loads(p.read_text(encoding='utf8'))

class Phase1KTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture=ROOT/'tests/fixtures/phase1k'
        cls.states=[load(ROOT/'public'/r['snapshot_url'].lstrip('/'))['version'] for r in load(cls.fixture/'states.json')]

    def test_independent_all_article_keys_titles_and_text_match_production(self):
        for i,(before,after) in enumerate(zip(self.states,self.states[1:])):
            changes=compare(before,after)
            self.assertEqual([c['article_number'] for c in changes],[c['article_number'] for c in full_articles(before,after)])
            self.assertEqual(len(changes),[3,2,1][i])
            self.assertEqual(len(compare(self.states[0],after)),[3,5,6][i])
        self.assertEqual([c['article_key'] for c in compare(*self.states[:2])],['0197041','0260001','0261001'])

    def test_whole_promulgation_is_97_not_incremental_three(self):
        a,b=[load(self.fixture/('package-'+n+'.json')) for n in ('281865','288579')]
        self.assertEqual(len(compare(a,b)),97)
        self.assertEqual(b['metadata']['issue_number'],'21857')
        self.assertEqual(len(independent(self.states[0]['body'])),617)
        self.assertEqual(len(independent(self.states[2]['body'])),619)

    def test_promulgation_metadata_cannot_inflate_reconciled_future(self):
        current,*future=copy.deepcopy(self.states)
        collection={'snapshots':{current['canonical_id']:current},'future':{current['canonical_id']:future},'history_backfill':{'pairs':[{'before':current,'after':future[0],'official_comparison':load(self.fixture/'promulgation.json')['payload']}]}}
        events,_=reconcile_upcoming([],collection,'2026-10-06T00:00:00Z')
        self.assertEqual(sorted(e['changed_article_count'] for e in events),[1,2,3])
        self.assertTrue(all(e['comparison_scope']=='FULL_STRUCTURED_BODY' for e in events))
        self.assertEqual(len(future_pairs(current,future)),3)
        self.assertEqual(future[0]['version_id'],future[1]['version_id'])
        self.assertNotEqual(future[0]['hashes']['body_hash'],future[1]['hashes']['body_hash'])

    def test_success_no_change_failure_recovery_status_only_and_retry_deploy(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(generated_commit,'ROOT',Path(tmp)),patch.object(generated_commit,'git',return_value=''):
            root=Path(tmp); public=root/'public/api/v1'
            public.mkdir(parents=True)
            for n in ('manifest.json','rules.json'): shutil.copy2(ROOT/'public/api/v1'/n,public/n)
            before={p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in public.glob('*.json')}
            report={'result':'NO_CHANGE','started_at':'2026-10-06T00:00:00Z','finished_at':'2026-10-06T00:05:00Z'}
            self.assertTrue(publish_status(root,report)); first=status_hash(root)
            self.assertFalse(publish_status(root,{**report,'result':'BLOCKED'})); self.assertEqual(status_hash(root),first)
            self.assertTrue(generated_commit.prepare(published=False,at=report['finished_at'],last_change=report['started_at'])['deploy_needed'])
            # Pending ops release survives a new process/check-out with no legal changes.
            self.assertTrue(generated_commit.prepare(published=False,at=report['finished_at'],last_change=report['started_at'])['deploy_needed'])
            generated_commit.acknowledge(load(public/'manifest.json')['dataset_version'])
            self.assertFalse(generated_commit.prepare(published=False,at=report['finished_at'],last_change=report['started_at'])['deploy_needed'])
            self.assertTrue(publish_status(root,{**report,'finished_at':'2026-10-06T00:06:00Z'})); self.assertNotEqual(status_hash(root),first)
            self.assertEqual({p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in public.glob('*.json') if p.name!='ops-status.json'},before)

if __name__=='__main__': unittest.main()

import copy
import json
import os
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch
from pipeline.operations.public_status import publish_status, status_hash
from scripts.scheduled_sync import policy, selected_schedule, scan_context
from status_evidence import assert_status_evidence
from test_pipeline import ROOT, evidence_collection
from scripts import sync as sync_module
from pipeline.snapshot import write_json

class Phase1MTests(unittest.TestCase):
    def test_fresh_checkout_with_stale_private_health_does_not_republish_unchanged_legal_data(self):
        collection=evidence_collection()
        with tempfile.TemporaryDirectory() as tmp,patch.object(sync_module,'ROOT',Path(tmp)):
            root=Path(tmp)
            first=sync_module.sync(collection)
            self.assertEqual(first['result'],'PUBLISHED')
            folders=('public/api/v1','data/registry')
            def fingerprint():
                return {p.relative_to(root).as_posix():(p.read_bytes(),p.stat().st_mtime_ns)
                    for folder in folders for p in (root/folder).rglob('*.json')}
            before=fingerprint()
            # Only public/registry state is committed by the production bot.
            # The next Actions checkout therefore restores old private health.
            write_json(root/'data/ops/health.json',{'last_dataset_version':'STALE_PRIVATE_VERSION'})
            repeated=copy.deepcopy(collection)
            for row in repeated['registry']: row['last_verified_at']='2026-10-09T02:00:00Z'
            for sn in repeated['snapshots'].values():
                if sn.get('repeal_evidence'):
                    sn['repeal_evidence']['history_evidence']=[{'request':{'query':'changed search wording','nw':2}}]
            second=sync_module.sync(repeated)
            self.assertEqual(second['result'],'NO_CHANGE')
            self.assertEqual(second['dataset_version'],first['dataset_version'])
            self.assertEqual(second['new_events'],0)
            self.assertEqual(second['persistent_new_events'],0)
            self.assertEqual(fingerprint(),before)

    def test_new_verified_repeal_keeps_exact_scope_without_frozen_status_count(self):
        collection=evidence_collection()
        row=next(r for r in collection['registry'] if r['source_kind']=='admrul' and r['status']=='CURRENT')
        sn=collection['snapshots'][row['canonical_id']]
        sn['metadata']['amendment_type']='폐지'; sn['metadata']['official_state']='N'
        sn['repeal_evidence']={'source':'OFFICIAL_HISTORY','canonical_id':sn['canonical_id'],
            'version_id':sn['version_id'],'amendment_type':'폐지','history_evidence':[{'request':{'target':'admrul','nw':2}}]}
        row['status']='REPEALED'; row['provenance']['scope_class']='HISTORICAL_REPEALED'
        self.assertEqual(len(collection['registry']),107)
        assert_status_evidence(self,collection)
        bad=copy.deepcopy(collection)
        bad['snapshots'][row['canonical_id']]['repeal_evidence']['version_id']='999999'
        with self.assertRaises(AssertionError): assert_status_evidence(self,bad)
        bad=copy.deepcopy(collection)
        bad['snapshots'][row['canonical_id']]['metadata']['amendment_type']='일부개정'
        with self.assertRaises(AssertionError): assert_status_evidence(self,bad)

    def test_schedule_policy_rehearsal_matches_real_policy_but_not_event(self):
        for mode,cron in [('morning','37 23 * * *'),('evening','37 11 * * *')]:
            self.assertEqual(policy(selected_schedule('workflow_dispatch','',mode),day=date(2026,10,9)),
                             policy(selected_schedule('schedule',cron),day=date(2026,10,9)))
        self.assertEqual(selected_schedule('schedule','37 11 * * *','morning'),'37 11 * * *')
        self.assertEqual(scan_context('workflow_dispatch','37 23 * * *')['trigger'],'MANUAL')
        with self.assertRaises(ValueError): selected_schedule('workflow_dispatch','','invalid')

    def test_scheduled_success_manual_failure_recovery_preserves_scheduled_freshness_and_legal_bytes(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{},clear=True):
            root=Path(tmp); public=root/'public/api/v1'; public.mkdir(parents=True)
            for name in ('manifest.json','rules.json'): shutil.copy2(ROOT/'public/api/v1'/name,public/name)
            before={p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in public.iterdir()}
            report={'result':'NO_CHANGE','started_at':'2026-10-09T00:00:00Z','finished_at':'2026-10-09T00:05:00Z'}
            env={'GITHUB_EVENT_NAME':'schedule','GITHUB_RUN_ID':'123456','SCHEDULE':'37 23 * * *'}
            self.assertTrue(publish_status(root,report,scan_context('schedule',env['SCHEDULE'],env['GITHUB_RUN_ID'])))
            initial=json.loads((public/'ops-status.json').read_text(encoding='utf8'))
            self.assertEqual(initial['trigger'],'SCHEDULE'); first=status_hash(root)
            self.assertFalse(publish_status(root,{**report,'result':'BLOCKED'})); self.assertEqual(status_hash(root),first)
            with patch.dict(os.environ,{'GITHUB_EVENT_NAME':'workflow_dispatch','GITHUB_RUN_ID':'123457','SCHEDULE_TEST_MODE':'morning'}):
                self.assertTrue(publish_status(root,{**report,'finished_at':'2026-10-09T01:05:00Z'},scan_context('workflow_dispatch','','123457')))
            manual=json.loads((public/'ops-status.json').read_text(encoding='utf8'))
            self.assertEqual(manual['trigger'],'MANUAL'); self.assertNotIn('schedule_cron',manual)
            self.assertEqual(manual['last_scheduled_scan'],initial['last_scheduled_scan'])
            self.assertEqual({p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in public.iterdir() if p.name!='ops-status.json'},before)
            with patch.dict(os.environ,{**env,'SCHEDULE':'invalid'}):
                with self.assertRaises(ValueError): publish_status(root,report,scan_context('schedule','invalid','123456'))
            self.assertEqual(json.loads((public/'ops-status.json').read_text(encoding='utf8')),manual)

if __name__=='__main__': unittest.main()

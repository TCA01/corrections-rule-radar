import copy
import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime,date
from pathlib import Path
from unittest.mock import patch
from pipeline.diff.articles import changed_articles,article_map
from pipeline.operations.calendar import d_day
from pipeline.law_api import ApiError
from pipeline.publication import build_contract,publish
from pipeline.normalize import snapshot
from pipeline.snapshot import write_json
from scripts import production_sync,sync,generated_commit,collect_core,discovery_scan
from scripts.observe import public_fingerprint
from scripts.scheduled_sync import policy
from scripts.validate_workflows import validate as workflows
from scripts.verify_artifact import verify as artifact
from test_pipeline import load,evidence_collection,baseline_law,ROOT,AT

class Phase1BTests(unittest.TestCase):
    def small_collection(self):
        source=evidence_collection(); row=next(r for r in source['registry'] if r['canonical_id']=='admrul-36282'); cid=row['canonical_id']
        return {'registry':[row],'snapshots':{cid:source['snapshots'][cid]},'future':{},'resolution':[{'canonical_id':cid,'status':'RESOLVED'}],'complete':True}
    def version(self,articles):
        s=copy.deepcopy(self.small_collection()['snapshots']['admrul-36282']); s['body']['articles']=articles; return s
    def test_singleton_nested_text_and_json_order_parity(self):
        article={'조문키':'x','조문여부':'조문','조문내용':'제5조의2(기본계획)','항':{'항내용':'① 계획','호':{'호내용':'1. 상세','목':{'목내용':'가. 하위'}}}}
        before=self.version({'조문단위':article}); after=copy.deepcopy(before)
        after['body']['articles']['조문단위']['항']['호']['목']['목내용']='가. 변경'
        diff=changed_articles(before,after); self.assertEqual(len(diff),1); self.assertEqual(diff[0]['article_title'],'제5조의2(기본계획)')
        self.assertEqual(diff,changed_articles(json.loads(json.dumps(before,sort_keys=True)),json.loads(json.dumps(after,sort_keys=True))))
        self.assertEqual(diff[0]['after_text'],'제5조의2(기본계획)\n① 계획\n1. 상세\n가. 변경')
    def test_administrative_strings_added_modified_deleted(self):
        before=self.version(['제1장 총칙','제1조(목적) 종전','제2조(삭제할 조문) 내용'])
        after=self.version(['제1장 총칙','제1조(목적) 개정','제3조(새 조문) 내용'])
        self.assertEqual([d['change_type'] for d in changed_articles(before,after)],['MODIFIED','ADDED','DELETED'])
        self.assertEqual(changed_articles(before,copy.deepcopy(before)),[])
    def test_flags_headings_and_unknown_bodies_do_not_invent_changes(self):
        before=self.version({'조문단위':[{'조문여부':'전문','조문내용':'제1장 총칙'},{'조문키':'x','조문여부':'조문','조문내용':'제1조(목적) 내용','조문변경여부':'N'}]})
        after=copy.deepcopy(before); after['body']['articles']['조문단위'][1]['조문변경여부']='Y'
        self.assertEqual(changed_articles(before,after),[])
        after['body']['articles']={'unknown':'opaque'}; self.assertEqual(changed_articles(before,after),[])
    def test_real_future_diff_backend_event_and_detail_parity(self):
        from pipeline.diff import future_events
        source=baseline_law(evidence_collection()); _,files=build_contract(source,future_events([],source['future']['law-001668'],AT),AT)
        future=files['rules/law-001668.json'][1]['upcoming'][0]
        event=next(e for e in files['changes/upcoming.json'][1]['events'] if e['canonical_id']=='law-001668')
        self.assertEqual(event['changed_articles'],future['changed_articles'])
        self.assertEqual({a['article_key'] for a in future['changed_articles']},{'article-5의2','article-53의2','article-53의3'})
        self.assertTrue(all(a['effective_date']=='2026-12-24' for a in future['changed_articles']))
    def test_future_event_keeps_comparison_after_effective_transition(self):
        from pipeline.diff import future_events
        source=baseline_law(evidence_collection()); cid='law-001668'; before=source['snapshots'][cid]
        _,files=build_contract(source,future_events([],source['future'][cid],AT),AT)
        retained=files['changes/upcoming.json'][1]['events']; after=copy.deepcopy(source)
        after['snapshots'][cid]=after['future'][cid][0]; after['future'][cid]=[]
        _,next_files=build_contract(after,retained,AT,history=[before])
        event=next_files['changes/latest.json'][1]['events'][0]
        self.assertEqual(event['changed_articles'],retained[0]['changed_articles']); self.assertEqual(event['event_id'],retained[0]['event_id'])
    def test_timezone_boundaries_and_effective_day(self):
        for instant,expected in [('2026-10-02T23:59:00+09:00',1),('2026-10-03T00:00:00+09:00',0),('2026-10-02T14:59:00+00:00',1),('2026-10-02T15:00:00+00:00',0),('2026-10-03T00:00:00+00:00',0),('2026-10-03T15:00:00+00:00',-1)]:
            with self.subTest(instant=instant): self.assertEqual(d_day('2026-10-03',datetime.fromisoformat(instant)),expected)
        with self.assertRaises(ValueError): d_day('2026-10-03',datetime(2026,10,3))
    def test_production_outages_and_recovery_preserve_last_good(self):
        collection=self.small_collection()
        with tempfile.TemporaryDirectory() as tmp,patch.object(sync,'ROOT',Path(tmp)),patch.object(production_sync,'ROOT',Path(tmp)):
            with patch.object(production_sync,'collect_core',return_value=collection): self.assertEqual(production_sync.run()['result'],'PUBLISHED')
            before=public_fingerprint(tmp); good=load(Path(tmp)/'data/ops/health.json')
            for code in ('TIMEOUT','HTTP_ERROR','AUTHENTICATION_ERROR','MALFORMED_JSON'):
                with patch.object(production_sync,'collect_core',side_effect=ApiError(code)): result=production_sync.run()
                self.assertEqual(result['result'],'BLOCKED'); self.assertEqual(before,public_fingerprint(tmp)); self.assertEqual(load(Path(tmp)/'data/ops/health.json')['last_successful_sync'],good['last_successful_sync'])
            partial=copy.deepcopy(collection); partial['complete']=False
            with patch.object(production_sync,'collect_core',return_value=partial): self.assertEqual(production_sync.run()['result'],'BLOCKED')
            with patch.object(production_sync,'collect_core',return_value=collection): recovered=production_sync.run()
            self.assertEqual(recovered['result'],'NO_CHANGE'); self.assertTrue(recovered['public_bytes_and_mtimes_identical']); self.assertEqual(load(Path(tmp)/'data/ops/health.json')['api_status'],'OK')
    def test_invalid_schema_blocks_before_public_switch(self):
        with tempfile.TemporaryDirectory() as tmp:
            _,files=build_contract(self.small_collection(),[],AT); publish(files,tmp); before=public_fingerprint(tmp)
            invalid=copy.deepcopy(files); invalid['manifest.json'][1]['rule_count']='invalid'
            with self.assertRaises(Exception): publish(invalid,tmp)
            self.assertEqual(before,public_fingerprint(tmp))
    def test_metadata_only_api_response_is_rejected(self):
        response=load(ROOT/'tests/fixtures/admin_new.json')
        from pipeline.registry import unwrap
        body=unwrap(response); body.pop('조문내용',None)
        serial=str(body['행정규칙기본정보']['행정규칙일련번호'])
        with self.assertRaisesRegex(ValueError,'STRUCTURED_BODY_MISSING'): snapshot(response,'admrul',serial,{})
    def test_empty_nested_law_body_is_rejected(self):
        from pipeline.registry import unwrap
        response=load(ROOT/'tests/fixtures/law_old_response.json'); body=unwrap(response); body['조문']={'조문단위':[]}
        with self.assertRaisesRegex(ValueError,'STRUCTURED_BODY_MISSING'): snapshot(response,'law','1',{})
    def test_core_does_not_fetch_official_pages_or_resolve_titles(self):
        collection=self.small_collection(); current=collection['snapshots']['admrul-36282']
        payload=load(ROOT/'tests/fixtures/admin_new.json')
        # Use the normalized real snapshot as the controlled transport result.
        with tempfile.TemporaryDirectory() as tmp,patch.object(collect_core,'ROOT',Path(tmp)),patch.object(collect_core,'LawClient') as client,patch.object(collect_core,'snapshot',return_value=current),patch.object(collect_core,'unwrap',return_value={'행정규칙기본정보':{'행정규칙일련번호':current['version_id']}}),patch.object(collect_core,'save_snapshot'):
            write_json(Path(tmp)/'data/registry/state.json',{'seed_ids':list(collection['snapshots']),'snapshots':collection['snapshots']}); write_json(Path(tmp)/'data/registry/rules.json',collection['registry'])
            client.return_value.fetch.return_value=(payload,{})
            result=collect_core.run(); self.assertEqual(result['resolution'][0]['status'],'RESOLVED')
            client.return_value.fetch.assert_called_once_with('lawService.do',target='admrul',LID=current['stable_identifier'])
    def test_core_identity_mismatch_is_review_and_not_silently_trusted(self):
        collection=self.small_collection(); bad=copy.deepcopy(collection['snapshots']['admrul-36282']); bad['canonical_id']='admrul-999'
        with tempfile.TemporaryDirectory() as tmp,patch.object(collect_core,'ROOT',Path(tmp)),patch.object(collect_core,'LawClient') as client,patch.object(collect_core,'snapshot',return_value=bad),patch.object(collect_core,'unwrap',return_value={'행정규칙기본정보':{'행정규칙일련번호':bad['version_id']}}):
            write_json(Path(tmp)/'data/registry/state.json',{'seed_ids':list(collection['snapshots']),'snapshots':collection['snapshots']}); write_json(Path(tmp)/'data/registry/rules.json',collection['registry']); client.return_value.fetch.return_value=({}, {})
            result=collect_core.run(); self.assertEqual(result['registry'],[]); self.assertEqual(result['resolution'][0]['review_reason'],'CANONICAL_ID_MISMATCH')
    def test_discovery_unchanged_tables_no_full_resolution_changed_tables_audited(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(discovery_scan,'ROOT',Path(tmp)),patch.object(discovery_scan,'public_page',return_value=b'opaque bytes'),patch.object(discovery_scan,'api_discovery',return_value={'api_candidates_pending':1}) as discover:
            self.assertIsNone(discovery_scan.run()); discover.assert_called_once(); discover.reset_mock()
            self.assertIsNone(discovery_scan.run()); discover.assert_not_called()
            with patch.object(discovery_scan,'public_page',return_value=b'changed bytes'):
                self.assertIsNone(discovery_scan.run()); discover.assert_called_once()
            self.assertFalse(load(Path(tmp)/'data/reports/discovery_scan.json')['production_membership_changed'])
    def test_schedule_daily_and_weekly_audit(self):
        self.assertEqual(policy('37 11 * * *',day=date(2026,10,4)),{'discovery':False,'full_audit':False})
        self.assertEqual(policy('37 23 * * *',day=date(2026,10,4)),{'discovery':True,'full_audit':True})
        self.assertEqual(policy('37 23 * * *',day=date(2026,10,5)),{'discovery':True,'full_audit':False})
    def test_heartbeat_only_after_30_days_never_changes_dataset(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(generated_commit,'ROOT',Path(tmp)),patch.object(generated_commit,'git',return_value='') as git:
            write_json(Path(tmp)/'public/api/v1/manifest.json',{'dataset_version':'ds-'+'a'*64}); before=public_fingerprint(tmp)
            self.assertFalse(generated_commit.prepare(published=False,at=AT,last_change='2026-09-03T00:00:01+00:00')['commit_needed'])
            result=generated_commit.prepare(published=False,at=AT,last_change='2026-09-03T00:00:00+00:00')
            self.assertTrue(result['heartbeat_only']); self.assertEqual(before,public_fingerprint(tmp)); git.assert_called_once_with('add','--','data/ops/heartbeat.json')
    def test_allowlist_and_deployment_retry_after_no_change(self):
        for bad in ('data/raw_cache/x.json','data/ops/health.json','web/src/App.tsx','secrets/key.json','public/api/v1/../../secret.json'): self.assertFalse(generated_commit.allowed(bad))
        self.assertTrue(generated_commit.allowed('public/api/v1/rules/law-001668.json'))
        with tempfile.TemporaryDirectory() as tmp,patch.object(generated_commit,'ROOT',Path(tmp)),patch.object(generated_commit,'git',return_value=''):
            version='ds-'+'a'*64; write_json(Path(tmp)/'public/api/v1/manifest.json',{'dataset_version':version})
            write_json(Path(tmp)/'data/ops/deployment.json',{'pending_dataset_version':version,'last_deployed_dataset_version':None})
            self.assertTrue(generated_commit.prepare(published=False,at=AT,last_change=AT)['deploy_needed'])
            generated_commit.acknowledge(version)
            self.assertFalse(generated_commit.prepare(published=False,at=AT,last_change=AT)['deploy_needed'])
    def test_workflows_and_cache_static_validation(self): self.assertEqual(workflows()['status'],'PASS')
    def test_artifact_rejects_private_files_and_secret_in_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'assets').mkdir(); (root/'index.html').write_text('<script src="/assets/app-AbCd1234.js"></script>',encoding='utf-8'); (root/'assets/app-AbCd1234.js').write_text('ok',encoding='utf-8')
            # Verify the current contract candidate independently of whether the
            # authorized production migration has already been performed.
            candidate=root/'candidate'; _,files=build_contract(self.small_collection(),[],AT); publish(files,candidate)
            shutil.copytree(candidate/'public/api/v1',root/'api/v1')
            shutil.rmtree(candidate)
            self.assertEqual(artifact(root)['status'],'PASS')
            (root/'raw.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'UNEXPECTED_ARTIFACT_FILE'): artifact(root)
            (root/'raw.json').unlink()
            with patch.dict(os.environ,{'LAW_API_OC':'ONLY_ARTIFACT_FAKE_SECRET_37289'}):
                (root/'assets/app-AbCd1234.js').write_text('ONLY_ARTIFACT_FAKE_SECRET_37289')
                with self.assertRaisesRegex(ValueError,'SECRET_LEAK'): artifact(root)

if __name__=='__main__': unittest.main()

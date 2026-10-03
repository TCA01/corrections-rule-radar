"""Offline adversarial tests and replays from live official evidence."""
import copy
import io
import json
import logging
import os
import socket
import tempfile
import traceback
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from pipeline.law_api.client import LawClient,ApiError,parse_payload,NoRedirect
from pipeline.corrections_seed import parse_seed
from pipeline.registry import identifiers,normalized_title
from pipeline.normalize import digest,snapshot,safe_url
from pipeline.diff import compare,future_events,seed_events
from pipeline.operations import health,heartbeat_due
from pipeline.publication import build_contract,publish
from pipeline.validation import assert_public_safe,validate_contract
from pipeline.discovery import candidate
from scripts import sync as sync_module

ROOT=Path(__file__).resolve().parents[1]
FIXTURES=ROOT/'tests/fixtures'
SECRET='UNREAL_TEST_CREDENTIAL_928374'
AT='2026-10-03T00:00:00+00:00'

def load(path): return json.loads(Path(path).read_text(encoding='utf-8'))

def evidence_collection():
    # Portable offline evidence: committed last-good state, not ignored staging.
    state=load(ROOT/'data/registry/state.json'); registry=load(ROOT/'data/registry/rules.json')
    return {'complete':True,'registry':registry,'snapshots':state['snapshots'],'future':state['future'],'resolution':[{'status':'RESOLVED','canonical_id':r['canonical_id']} for r in registry]}

def baseline_law(collection):
    # Keep the October regression example independent of future production runs.
    result=copy.deepcopy(collection)
    result['snapshots']['law-001668']=load(FIXTURES/'law_replay.json')['new']
    result['future']['law-001668']=load(FIXTURES/'future_replay.json')['new_versions']
    return result

class Response:
    def __init__(self,raw): self.raw=raw
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def read(self,limit=None): return self.raw

class Opener:
    def __init__(self,results): self.results=iter(results); self.count=0
    def open(self,*args,**kwargs):
        self.count+=1; value=next(self.results)
        if isinstance(value,Exception): raise value
        return Response(value)

class ClientTests(unittest.TestCase):
    def client(self,opener,cache): return LawClient(opener=opener,cache=cache,interval=0,retries=1)
    def test_missing_secret_stops(self):
        with patch.dict(os.environ,{'LAW_API_OC':''}):
            with self.assertRaisesRegex(ApiError,'WAITING_FOR_LAW_API_OC'): LawClient()
    def test_secret_echo_redacted_and_not_logged(self):
        raw=json.dumps({'LawSearch':{'law':{'법령상세링크':'/DRF/lawService.do?OC='+SECRET+'&MST=1'},'resultCode':'00'}},ensure_ascii=False).encode()
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'LAW_API_OC':SECRET}),patch('sys.stdout',new_callable=io.StringIO) as stdout:
            c=self.client(Opener([raw]),tmp); value,ev=c.fetch(target='law')
            self.assertNotIn(SECRET,json.dumps(value)); self.assertNotIn(SECRET,repr(c)); self.assertNotIn(SECRET,stdout.getvalue())
            self.assertTrue(ev['credential_redacted'])
            self.assertTrue(all(SECRET.encode() not in p.read_bytes() for p in Path(tmp).iterdir()))
            self.assertNotEqual(ev['raw_sha256'],ev['stored_sha256'])
    def test_http500_exponential_retry_then_fail(self):
        errors=[urllib.error.HTTPError('https://example/?OC='+SECRET,500,'fail',{},None)]*2
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'LAW_API_OC':SECRET}),patch('time.sleep') as sleep:
            op=Opener(errors)
            try: self.client(op,tmp).fetch(target='law')
            except ApiError as e:
                self.assertEqual(e.status,500); self.assertNotIn(SECRET,traceback.format_exc())
            else: self.fail('500 accepted')
            self.assertEqual(op.count,2); sleep.assert_called_once_with(1)
    def test_timeout_retries_and_classifies(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'LAW_API_OC':SECRET}),patch('time.sleep'):
            with self.assertRaisesRegex(ApiError,'TIMEOUT'): self.client(Opener([socket.timeout(),socket.timeout()]),tmp).fetch(target='law')
    def test_auth403_not_retried(self):
        err=urllib.error.HTTPError('https://example/?OC='+SECRET,403,'fail',{},None)
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'LAW_API_OC':SECRET}):
            op=Opener([err])
            with self.assertRaisesRegex(ApiError,'AUTHENTICATION_ERROR'): self.client(op,tmp).fetch(target='law')
            self.assertEqual(op.count,1)
    def test_xml_fallback(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'LAW_API_OC':SECRET}):
            result,ev=self.client(Opener([b'{broken',b'<LawSearch><totalCnt>0</totalCnt></LawSearch>']),tmp).fetch(target='law')
            self.assertEqual(result['LawSearch']['totalCnt'],'0'); self.assertEqual(ev['request']['type'],'XML')
    def test_malformed_json_and_xml_fail(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'LAW_API_OC':SECRET}):
            with self.assertRaisesRegex(ApiError,'MALFORMED_XML'): self.client(Opener([b'{broken',b'<broken>']),tmp).fetch(target='law')
    def test_empty_response_fails(self):
        with self.assertRaisesRegex(ApiError,'EMPTY_RESPONSE'): parse_payload(b'','JSON')
    def test_auth_payload_classified(self):
        raw=json.dumps({'LawSearch':{'resultCode':'20','resultMsg':'사용자 인증 실패'}}).encode()
        with self.assertRaisesRegex(ApiError,'AUTHENTICATION_ERROR'): parse_payload(raw,'JSON')
    def test_legal_body_auth_words_not_error(self):
        raw=json.dumps({'Law':{'조문내용':'사용자 인증과 등록되지 않은 계정의 처리'}}).encode()
        self.assertIn('Law',parse_payload(raw,'JSON'))
    def test_redirect_rejected(self):
        with self.assertRaisesRegex(ApiError,'REDIRECT_REJECTED'): NoRedirect().redirect_request(None,None,302,'',{},'https://evil.example')

class SeedAndIdentityTests(unittest.TestCase):
    def test_real_seed_counts_and_rowspans(self):
        seed=load(ROOT/'data/seed/corrections.json')
        self.assertEqual(sum(seed['counts'].values()),len(seed['entries']))
        # Baseline is evidence for this fixture, not an eternal production rule.
        for kind,file in [('law','seed_law.html'),('admrul','seed_admin.html')]:
            entries,counts=parse_seed((FIXTURES/file).read_text(encoding='utf-8'),kind,AT)
            self.assertEqual(len(entries),19 if kind=='law' else 49)
            if kind=='admrul': self.assertTrue(all(e['department'] for e in entries))
    def test_seed_not_fixed_to68(self):
        html='<h3>법률 (1개)</h3><table><caption>교정본부 관련 법령</caption><tbody><tr><td>새 규칙</td><td><a href="https://www.law.go.kr/법령/새규칙">바로가기</a></td></tr></tbody></table>'
        self.assertEqual(len(parse_seed(html,'law',AT)[0]),1)
        with self.assertRaisesRegex(ValueError,'COUNT_MISMATCH'): parse_seed(html.replace('1개','2개'),'law',AT)
    def test_seed_empty_fails(self):
        with self.assertRaisesRegex(ValueError,'SEED_EMPTY'): parse_seed('<html/>','law',AT)
    def test_admin_identifier_semantics(self):
        record={'행정규칙ID':'36282','행정규칙일련번호':'2100000285400','id':'1','행정규칙상세링크':'/DRF/lawService.do?ID=2100000285400&LID=36282'}
        self.assertEqual(identifiers(record,'admrul'),('36282','2100000285400'))
        record['행정규칙상세링크']='/DRF/lawService.do?ID=36282'
        with self.assertRaisesRegex(ValueError,'IDENTIFIER_LINK_MISMATCH'): identifiers(record,'admrul')
    def test_law_identifier_semantics(self):
        record={'법령ID':'001668','법령일련번호':'290191','id':'1','법령상세링크':'/DRF/lawService.do?MST=290191'}
        self.assertEqual(identifiers(record,'law'),('001668','290191'))
    def test_normalized_title_spacing_not_identity(self):
        self.assertEqual(normalized_title('가석방 업무 지침'),normalized_title('가석방업무지침'))
    def test_all_seed_resolution_retained(self):
        seed=load(ROOT/'data/seed/corrections.json'); report=load(ROOT/'data/reports/resolution.json')
        self.assertEqual(len(seed['entries']),len(report['entries'])); self.assertTrue(report['complete'])
        self.assertTrue(all(r['status'] in ('RESOLVED','REVIEW') for r in report['entries']))

class LiveEvidenceTests(unittest.TestCase):
    """Offline assertions on results of real requests; never substitute fake PASS."""
    def test_capabilities_all_have_official_evidence(self):
        reports=load(ROOT/'data/reports/capabilities.json')
        for key in ('LAW_OLD_NEW','ADMIN_OLD_NEW','LAW_CHANGE_HISTORY','ARTICLE_HISTORY','ARTICLE_DAY_HISTORY','LAW_APPENDICES','ADMIN_APPENDICES','DELETION_HISTORY','SYSTEM_MAP'):
            with self.subTest(capability=key):
                self.assertEqual(reports[key]['status'],'PASS'); self.assertIn('evidence',reports[key])
    def test_known_admin_revisions(self):
        cases=load(ROOT/'data/reports/known_cases.json')
        for title,when,number in [('교도작업운영지침','20261001','1389'),('교도작업특별회계운영지침','20261001','1390'),('가석방 업무지침','20260330','1384')]:
            with self.subTest(title=title): self.assertTrue(any(i['발령일자']==when and i['발령번호']==number for i in cases[title]['versions']))
    def test_current_and_future_real_law_coexist(self):
        coll=baseline_law(evidence_collection()); cid='law-001668'
        self.assertLess(coll['snapshots'][cid]['metadata']['effective_date'],'2026-12-24')
        self.assertTrue(any(s['metadata']['effective_date']=='2026-12-24' for s in coll['future'][cid]))

class ReplayTests(unittest.TestCase):
    def test_known_admin_replay_uses_actual_1389_revision(self):
        case=load(FIXTURES/'admin_replay.json')
        self.assertEqual(case['new']['metadata']['name'],'교도작업운영지침')
        self.assertEqual(case['new']['metadata']['issue_date'],'2026-10-01')
        self.assertEqual(case['new']['metadata']['issue_number'],'1389')
        self.assertNotEqual(case['old']['version_id'],case['new']['version_id'])
    def test_all_real_replays_through_same_engine(self):
        for name in ('law','admin','rename','appendix','repeal','future'):
            with self.subTest(case=name):
                case=load(FIXTURES/(name+'_replay.json'))
                if name=='future': events=future_events(case['old_versions'],case['new_versions'],AT)
                else:
                    self.assertEqual(case['old']['canonical_id'],case['new']['canonical_id'])
                    events=compare(case['old'],case['new'],AT,repeal_evidence=case['new'].get('repeal_evidence'))
                    self.assertIn('raw_sha256',case['old']['evidence'])
                self.assertIn(case['expected_type'],[e['change_type'] for e in events])
    def test_event_determinism(self):
        case=load(FIXTURES/'admin_replay.json')
        a=compare(case['old'],case['new'],AT); b=compare(case['old'],case['new'],'2026-10-04T00:00:00+00:00')
        self.assertEqual([e['event_id'] for e in a],[e['event_id'] for e in b])
    def test_missing_result_does_not_mean_repeal(self):
        events=seed_events(['law-1'],[],{},AT)
        self.assertFalse(any(e['change_type']=='RULE_REPEALED' for e in events))
    def test_repeal_requires_identity_version_evidence(self):
        case=load(FIXTURES/'repeal_replay.json')
        with self.assertRaisesRegex(ValueError,'REPEAL_REQUIRES_REVIEW'): compare(case['old'],case['new'],AT)
        wrong=copy.deepcopy(case['new']['repeal_evidence']); wrong['canonical_id']='admrul-999'
        with self.assertRaisesRegex(ValueError,'REPEAL_REQUIRES_REVIEW'): compare(case['old'],case['new'],AT,repeal_evidence=wrong)
    def test_identical_repealed_snapshot_no_change(self):
        case=load(FIXTURES/'repeal_replay.json'); s=case['new']
        self.assertEqual(compare(s,s,AT,repeal_evidence=s['repeal_evidence']),[])
    def test_timestamp_insensitive_hash(self):
        case=load(FIXTURES/'admin_replay.json'); s=case['new']; a=copy.deepcopy(s); a['evidence']['run_timestamp']='changed'
        self.assertEqual(s['hashes'],a['hashes']); self.assertEqual(digest({'b':2,'a':1}),digest({'a':1,'b':2}))
        raw=load(FIXTURES/'admin_new.json'); root=next(iter(raw.values())); before=snapshot(raw,'admrul',root['행정규칙기본정보']['행정규칙일련번호'],{})
        root['행정규칙기본정보']['생성일자']='20990101'; root['transport_timestamp']='changed'
        after=snapshot(raw,'admrul',root['행정규칙기본정보']['행정규칙일련번호'],{})
        self.assertEqual(before['hashes'],after['hashes'])
    def test_appendix_content_not_semantically_parsed(self):
        raw=load(FIXTURES/'admin_new.json'); root=next(iter(raw.values())); serial=root['행정규칙기본정보']['행정규칙일련번호']; before=snapshot(raw,'admrul',serial,{})
        for a in root.get('별표',{}).get('별표단위',[]): a['별표내용']=['UNRELATED_DOCUMENT_CONTENT']
        after=snapshot(raw,'admrul',serial,{})
        self.assertEqual(before['hashes'],after['hashes'])

class PublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.coll=evidence_collection()
    def test_complete_contract_schemas_and_android_neutral(self):
        version,files=build_contract(self.coll,[],AT)
        for rel,(schema,value) in files.items():
            with self.subTest(file=rel): validate_contract(schema,value)
        self.assertEqual(files['manifest.json'][1]['rules_url'],'/api/v1/rules.json')
        self.assertTrue(all(isinstance(r['canonical_id'],str) for r in files['rules.json'][1]['rules']))
    def test_filesystem_and_secret_leaks_rejected(self):
        with patch.dict(os.environ,{'LAW_API_OC':SECRET}):
            for value in ({'secret':SECRET},{'path':'E:\\workspace\\data'},{'traceback':'oops'},{'url':'https://www.law.go.kr/?OC=anything'}):
                with self.subTest(value_type=list(value)):
                    with self.assertRaises(ValueError): assert_public_safe(value)
    def test_public_url_strips_oc(self):
        self.assertNotIn('OC=',safe_url('/LSW/lsInfoP.do?OC=secret&lsiSeq=1'))
        with self.assertRaises(ValueError): safe_url('https://evil.example/file')
    def test_second_offline_run_no_rewrites_or_events(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(sync_module,'ROOT',Path(tmp)):
            first=sync_module.sync(self.coll); output=Path(tmp)/'public/api/v1'
            before={str(p.relative_to(output)):(p.read_bytes(),p.stat().st_mtime_ns) for p in output.rglob('*.json')}
            second=sync_module.sync(self.coll)
            after={str(p.relative_to(output)):(p.read_bytes(),p.stat().st_mtime_ns) for p in output.rglob('*.json')}
            self.assertEqual(first['result'],'PUBLISHED'); self.assertEqual(second['result'],'NO_CHANGE'); self.assertEqual(second['new_events'],0); self.assertEqual(before,after)
    def test_one_partial_and_global_failures_preserve_last_good(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(sync_module,'ROOT',Path(tmp)):
            sync_module.sync(self.coll); output=Path(tmp)/'public/api/v1'; before={str(p):p.read_bytes() for p in output.rglob('*.json')}
            for count in (1,3,len(self.coll['resolution'])):
                broken=copy.deepcopy(self.coll)
                for row in broken['resolution'][:count]: row['status']='REVIEW'; row['review_reason']='API_FAILED'
                for row in broken['resolution'][:count]: broken['snapshots'].pop(row['canonical_id'],None)
                report=sync_module.sync(broken)
                self.assertEqual(report['result'],'BLOCKED'); self.assertEqual(before,{str(p):p.read_bytes() for p in output.rglob('*.json')})
    def test_invalid_schema_does_not_replace_public(self):
        with tempfile.TemporaryDirectory() as tmp:
            _,files=build_contract(self.coll,[],AT); publish(files,tmp); p=Path(tmp)/'public/api/v1/manifest.json'; before=p.read_bytes()
            broken=copy.deepcopy(files); broken['manifest.json'][1]['rule_count']='invalid'
            with self.assertRaises(Exception): publish(broken,tmp)
            self.assertEqual(before,p.read_bytes())
    def test_incomplete_collection_blocked(self):
        c=copy.deepcopy(self.coll); c['complete']=False
        self.assertEqual(health(c,AT)['publication_status'],'BLOCKED')
    def test_new_seed_is_discovery_until_reviewed(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(sync_module,'ROOT',Path(tmp)):
            sync_module.sync(self.coll)
            new=copy.deepcopy(self.coll); s=copy.deepcopy(next(iter(new['snapshots'].values()))); s['canonical_id']='admrul-999999999'
            new['snapshots'][s['canonical_id']]=s; r=copy.deepcopy(new['registry'][0]); r['canonical_id']=s['canonical_id']; new['registry'].append(r); new['resolution'].append({'status':'RESOLVED','canonical_id':s['canonical_id']})
            before=(Path(tmp)/'public/api/v1/manifest.json').read_bytes()
            self.assertEqual(sync_module.sync(new)['result'],'BLOCKED')
            pending=load(Path(tmp)/'data/reports/discovery_candidates.json')
            self.assertFalse(pending[0]['trusted']); self.assertEqual(before,(Path(tmp)/'public/api/v1/manifest.json').read_bytes())
    def test_removed_seed_retains_history_and_public(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(sync_module,'ROOT',Path(tmp)):
            sync_module.sync(self.coll); new=copy.deepcopy(self.coll); removed=new['registry'].pop(); cid=removed['canonical_id']; new['snapshots'].pop(cid); new['resolution']=[r for r in new['resolution'] if r['canonical_id']!=cid]
            before=(Path(tmp)/'data/registry/state.json').read_bytes()
            self.assertEqual(sync_module.sync(new)['result'],'BLOCKED')
            pending=load(Path(tmp)/'data/reports/pending_seed_events.json')
            self.assertEqual(pending[0]['change_type'],'RULE_REMOVED_FROM_CORRECTIONS_SEED'); self.assertEqual(before,(Path(tmp)/'data/registry/state.json').read_bytes())
    def test_directory_switch_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            _,files=build_contract(self.coll,[],AT); publish(files,tmp); path=Path(tmp)/'public/api/v1/manifest.json'; before=path.read_bytes(); replace=os.replace; calls=0
            def failing_replace(src,dst):
                nonlocal calls
                # Allow staged per-file atomic writes; fail only dataset switch.
                if Path(src).is_dir():
                    calls+=1
                    if calls==2: raise OSError('SIMULATED_SWITCH_FAILURE')
                return replace(src,dst)
            with patch('pipeline.publication.os.replace',side_effect=failing_replace):
                with self.assertRaisesRegex(ValueError,'PUBLICATION_ROLLED_BACK'): publish(files,tmp)
            self.assertEqual(before,path.read_bytes())
    def test_heartbeat_30days_separate(self):
        self.assertTrue(heartbeat_due('2026-09-03T00:00:00+00:00',AT)); self.assertFalse(heartbeat_due('2026-09-04T00:00:00+00:00',AT))
    def test_discovery_not_trusted(self):
        c=candidate('x','new','https://www.law.go.kr/','SYSTEM_MAP'); self.assertFalse(c['trusted']); self.assertEqual(c['review_status'],'REVIEW')

if __name__=='__main__': unittest.main()

"""Adversarial persistence/lineage/date/source tests; no synthetic legal claims."""
import copy,json,os,tempfile,unittest
from datetime import date,timedelta
from pathlib import Path
from unittest.mock import patch
from pipeline.diff.history import make_event,merge,recent,article_groups
from pipeline.normalize import digest
from pipeline.publication import build_contract,publish
from pipeline.snapshot import write_json
from pipeline.validation import validate_contract,assert_public_safe
from pipeline.law_api.comparisons import prepare
from scripts import sync
from scripts.observe import public_fingerprint
from scripts.validate_public import validate
from test_pipeline import evidence_collection,ROOT,AT

class PersistentHistoryTests(unittest.TestCase):
    def versions(self,kind='admrul',effective='2026-10-02'):
        cid='admrul-36282' if kind=='admrul' else 'law-001668'
        old=copy.deepcopy(evidence_collection()['snapshots'][cid]); new=copy.deepcopy(old)
        old['version_id']='100'; new['version_id']='101'
        old['metadata']['effective_date']='2026-06-01'; new['metadata']['effective_date']=effective
        old['body']={'articles':['제1조(목적) 종전','① 원문','제2조(삭제) 문장'],'addenda':None}
        new['body']={'articles':['제1조(목적) 개정','① 바뀐 원문','제3조(추가) 새 문장'],'addenda':None}
        for s in (old,new):
            s['hashes']['body_hash']=digest(s['body']); s['hashes']['metadata_hash']=digest(s['metadata'])
        return old,new
    def collection(self,new):
        base=evidence_collection(); cid=new['canonical_id']; row=copy.deepcopy(next(r for r in base['registry'] if r['canonical_id']==cid))
        row['version_id']=new['version_id']; row['current_name']=new['metadata']['name']
        return {'complete':True,'registry':[row],'snapshots':{cid:new},'future':{},'resolution':[{'canonical_id':cid,'status':'RESOLVED'}]}
    def official(self,old,new):
        law=new['source_kind']=='law'; serial='법령일련번호' if law else '행정규칙일련번호'; stable='법령ID' if law else '행정규칙ID'
        def meta(s): return {serial:s['version_id'],stable:s['stable_identifier'],'시행일자':s['metadata']['effective_date'].replace('-','')}
        return {'Official':{'구조문_기본정보':meta(old),'신조문_기본정보':meta(new),'구조문목록':{'조문':[{'content':'제1조(목적) 종전'},{'content':'① 원문'}]},'신조문목록':{'조문':[{'content':'제1조(목적) 개정'},{'content':'① 바뀐 원문'}]}}}
    def test_stable_id_and_first_detection(self):
        old,new=self.versions(); first=make_event(old,new,AT); second=make_event(old,new,'2026-10-04T00:00:00Z')
        self.assertEqual(first['event_id'],second['event_id']); self.assertEqual(merge([first],[second]),[first])
    def test_dates_future_today_yesterday_weeks_and_older(self):
        today=date(2026,10,3); events=[]
        for offset in (1,0,-1,-30,-89,-90,-200):
            old,new=self.versions(effective=(today+timedelta(days=offset)).isoformat()); events.append(make_event(old,new,AT))
        selected=recent(events,today)
        self.assertEqual(len(selected),4); self.assertEqual(len(merge([],events)),7)
        self.assertTrue(all(e['effective_date']<='2026-10-03' for e in selected))
    def test_added_removed_modified_with_admin_continuations(self):
        old,new=self.versions(); event=make_event(old,new,AT)
        self.assertEqual([x['change_type'] for x in event['changed_articles']],['MODIFIED','REMOVED','ADDED'])
        self.assertIn('① 바뀐 원문',event['changed_articles'][0]['after_text'])
        self.assertEqual(event['comparison_source'],'STRUCTURED_SNAPSHOT_DIFF')
    def test_title_only_renamed(self):
        old,new=self.versions(); new['body']=copy.deepcopy(old['body']); new['body']['articles'][0]='제1조(새 목적) 종전'; new['hashes']['body_hash']=digest(new['body'])
        self.assertEqual(make_event(old,new,AT)['changed_articles'][0]['change_type'],'RENAMED')
    def test_law_article_flags_do_not_change_number_identity(self):
        old,new=self.versions('law')
        old['body']['articles']={'조문단위':[{'조문키':'0001001','조문내용':'제1조(목적) 종전','항':{'항내용':'① 문장'}}]}
        new['body']['articles']={'조문단위':[{'조문키':'0001021','조문내용':'제1조(목적) 개정','항':{'항내용':'① 문장'}}]}
        old['hashes']['body_hash']=digest(old['body']); new['hashes']['body_hash']=digest(new['body'])
        self.assertEqual([a['change_type'] for a in make_event(old,new,AT)['changed_articles']],['MODIFIED'])
    def test_official_law_and_administrative_pair_priority(self):
        for kind,source in (('law','LAWGO_OLD_NEW'),('admrul','LAWGO_ADMIN_OLD_NEW')):
            old,new=self.versions(kind); event=make_event(old,new,AT,official_comparison=self.official(old,new))
            self.assertEqual(event['comparison_source'],source); self.assertTrue(event['official_old_new_available']); self.assertEqual(event['comparison_scope'],'OFFICIAL_COMPARISON_EXCERPT')
            self.assertIn('① 바뀐 원문',event['changed_articles'][0]['after_text'])
    def test_wrong_pair_and_malformed_official_fail_to_snapshot(self):
        old,new=self.versions(); payload=self.official(old,new); payload['Official']['구조문_기본정보']['행정규칙일련번호']='999'
        for broken in (payload,{'Official':{}},{}):
            event=make_event(old,new,AT,official_comparison=broken)
            self.assertEqual(event['comparison_source'],'STRUCTURED_SNAPSHOT_DIFF'); self.assertFalse(event['official_old_new_available'])
    def test_body_identical_metadata_and_effective_corrections(self):
        old,new=self.versions(); new=copy.deepcopy(old); new['metadata']['issue_date']='2026-10-02'; new['hashes']['metadata_hash']=digest(new['metadata'])
        event=make_event(old,new,AT); self.assertEqual(event['change_type'],'METADATA_CORRECTED'); self.assertEqual(event['changed_articles'],[])
        new=copy.deepcopy(old); new['metadata']['effective_date']='2026-06-02'; new['hashes']['metadata_hash']=digest(new['metadata'])
        self.assertEqual(make_event(old,new,AT)['change_type'],'EFFECTIVE_DATE_CORRECTED')
    def test_appendix_added_removed_metadata_and_null_download(self):
        old,new=self.versions(); app={'sequence':'1','branch':'0','title':'공식 별표','type':'별표','url':None,'pdf_url':None}
        old['appendices']=[app]; new['appendices']=[]
        event=make_event(old,new,AT); change=event['appendix_changes'][0]
        self.assertEqual(change['change_type'],'APPENDIX_REMOVED'); self.assertEqual(change['status'],'REMOVED'); self.assertIsNone(change['after_metadata']); self.assertEqual(change['before_metadata'],app)
        validate_contract('change',{'schema_version':'1.3','event':event})
        old['appendices']=[]; new['appendices']=[app]; self.assertEqual(make_event(old,new,AT)['appendix_changes'][0]['change_type'],'APPENDIX_ADDED')
        old['appendices']=[app]; new['appendices']=[{**app,'title':'수정 제목'}]
        self.assertEqual(make_event(old,new,AT)['appendix_changes'][0]['change_type'],'APPENDIX_METADATA_CHANGED')
    def test_missing_structure_isolated_and_no_false_removal(self):
        old,new=self.versions(); new['body']['articles']={'opaque':'공식 구조를 매핑할 수 없음'}
        event=make_event(old,new,AT); self.assertEqual(event['comparison_status'],'COMPARISON_UNAVAILABLE'); self.assertEqual(event['changed_articles'],[])
        _,files=build_contract(self.collection(new),[],AT,history=[old],persistent=[event]); self.assertEqual(len(files['changes/history.json'][1]['events']),1)
    def test_missing_predecessor_is_explicit(self):
        _,new=self.versions(); e=make_event(None,new,AT)
        self.assertEqual(e['comparison_unavailable_reason'],'BEFORE_VERSION_UNAVAILABLE'); self.assertIsNone(e['before_version'])
    def test_cross_identity_blocked(self):
        old,new=self.versions(); old['canonical_id']='admrul-999'
        with self.assertRaisesRegex(ValueError,'HISTORY_IDENTITY_MISMATCH'): make_event(old,new,AT)
    def test_future_to_current_retains_event_and_event_file(self):
        old,new=self.versions(effective='2026-12-24'); e=make_event(old,new,AT); c=self.collection(old); c['future']={new['canonical_id']:[new]}
        _,f=build_contract(c,[],AT,history=[old,new],persistent=[e]); c['snapshots'][new['canonical_id']]=new; c['future']={}
        _,after=build_contract(c,[],'2026-12-25T00:00:00Z',history=[old,new],persistent=[e])
        path='changes/'+e['event_id']+'.json'; self.assertEqual(f[path],after[path]); self.assertEqual(after['changes/recent.json'][1]['events'],[e])
    def test_older_events_remain_after_window_expires(self):
        old,new=self.versions(); e=make_event(old,new,AT)
        _,files=build_contract(self.collection(new),[],'2027-04-01T00:00:00Z',history=[old],persistent=[e])
        self.assertEqual(files['changes/recent.json'][1]['events'],[]); self.assertEqual(files['changes/history.json'][1]['events'],[e])
    def test_inconsistent_version_reference_blocks_publication(self):
        old,new=self.versions(); e=make_event(old,new,AT); e['before_version']['body_hash']='0'*64
        with self.assertRaisesRegex(ValueError,'PERSISTENT_VERSION_REFERENCE_MISMATCH'): build_contract(self.collection(new),[],AT,history=[old],persistent=[e])
    def test_publish_nochange_recovery_and_immutable_bytes(self):
        old,new=self.versions(); c=self.collection(new); c['history_backfill']={'snapshots':[old],'pairs':[{'before':old,'after':new}]}
        with tempfile.TemporaryDirectory() as tmp,patch.object(sync,'ROOT',Path(tmp)):
            first=sync.sync(c); self.assertEqual(first['result'],'PUBLISHED'); before=public_fingerprint(tmp); recorded=json.loads((Path(tmp)/'data/registry/change_history.json').read_text(encoding='utf8'))
            broken=copy.deepcopy(c); broken['complete']=False
            self.assertEqual(sync.sync(broken)['result'],'BLOCKED'); self.assertEqual(public_fingerprint(tmp),before)
            self.assertEqual(sync.sync(c)['result'],'NO_CHANGE'); self.assertEqual(public_fingerprint(tmp),before)
            self.assertEqual(json.loads((Path(tmp)/'data/registry/change_history.json').read_text(encoding='utf8')),recorded)
            self.assertEqual(validate(Path(tmp)/'public/api/v1')['status'],'PASS')
    def test_unchanged_events_and_archives_preserve_mtime_on_other_change(self):
        old,new=self.versions(); e=make_event(old,new,AT); c=self.collection(new)
        with tempfile.TemporaryDirectory() as tmp:
            _,f=build_contract(c,[],AT,history=[old],persistent=[e]); publish(f,tmp)
            path=Path(tmp)/'public/api/v1/changes'/(e['event_id']+'.json'); before=(path.read_bytes(),path.stat().st_mtime_ns)
            c['registry'][0]['historical_names'].append('이전 명칭')
            _,f=build_contract(c,[],'2026-10-04T00:00:00Z',history=[old],persistent=[e]); publish(f,tmp)
            self.assertEqual((path.read_bytes(),path.stat().st_mtime_ns),before)
    def test_cached_histories_do_not_make_api_calls(self):
        old,new=self.versions(); c=self.collection(new); e=make_event(old,new,AT)
        with patch('pipeline.law_api.comparisons.LawClient') as client:
            prepare(c,{'seed_ids':[new['canonical_id']],'snapshots':{new['canonical_id']:old}},[e]); client.assert_not_called()
    def test_sync_future_transition_retains_single_comparison(self):
        old,new=self.versions(effective='2026-12-24'); c=self.collection(old); c['future']={new['canonical_id']:[new]}
        with tempfile.TemporaryDirectory() as tmp,patch.object(sync,'ROOT',Path(tmp)):
            sync.sync(c); path=Path(tmp)/'data/registry/change_history.json'
            first=json.loads(path.read_text(encoding='utf8')); self.assertEqual(len(first),1)
            transitioned=self.collection(new)
            sync.sync(transitioned); second=json.loads(path.read_text(encoding='utf8'))
            self.assertEqual(first,second); self.assertEqual(sync.sync(transitioned)['result'],'NO_CHANGE')
    def test_generated_allowlist_retains_history(self):
        from scripts.generated_commit import allowed
        self.assertTrue(allowed('data/registry/change_history.json'))
        self.assertFalse(allowed('data/raw_cache/phase1e/private.json'))
    def test_secret_checks_apply_to_event_details(self):
        old,new=self.versions(); e=make_event(old,new,AT)
        with patch.dict(os.environ,{'LAW_API_OC':'FAKE_SECRET_97141'}):
            assert_public_safe(e); e['regulation_name']='FAKE_SECRET_97141'
            with self.assertRaisesRegex(ValueError,'SECRET_LEAK'): assert_public_safe(e)
    def test_real_official_past_effective_law_and_admin(self):
        live=json.loads((ROOT/'tests/fixtures/phase1e_live_pairs.json').read_text(encoding='utf8'))
        sources=set()
        for pair in live['pairs']:
            e=make_event(pair['before'],pair['after'],live['collected_at'],official_comparison=pair['official_comparison'],comparison_evidence=pair['comparison_evidence'])
            self.assertLess(e['effective_date'],'2026-10-03'); self.assertGreater(e['changed_article_count'],0)
            self.assertTrue(e['official_old_new_available']); assert_public_safe(e)
            validate_contract('change',{'schema_version':'1.3','event':e}); sources.add(e['comparison_source'])
        self.assertEqual(sources,{'LAWGO_OLD_NEW','LAWGO_ADMIN_OLD_NEW'})

if __name__=='__main__': unittest.main()

"""Release scope/provenance/tombstone/automation gates from actual live evidence."""
import ast,copy,json,tempfile,unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch
from pipeline.normalize import digest
from pipeline.normalize.appendices import appendix_status
from pipeline.registry.approval import approved_candidates,verify_expansion
from pipeline.registry.provenance import apply_provenance
from pipeline.registry.domains import apply_domains
from pipeline.diff.history import make_event,merge,recent
from pipeline.publication import build_contract
from pipeline.publication.versions import url
from pipeline.snapshot import write_json
from pipeline.validation import validate_contract,assert_public_safe
from scripts import sync,production_sync,collect_core
from scripts.observe import public_fingerprint
from scripts.validate_workflows import validate as workflows
from test_pipeline import ROOT,AT,load,evidence_collection

def expanded():
    staged=ROOT/'data/staging/phase1f_collection.json'
    collection=load(staged) if staged.exists() else evidence_collection()
    # This regression represents the historical Phase 1F release scope even
    # after separately approved additions enter the current registry.
    approved=approved_candidates(load(ROOT/'data/reports/phase1d_api_eligibility.json'))
    ids=set(load(ROOT/'tests/fixtures/phase1f_previous_core.json')['previous_ids'])|{r['canonical_id'] for r in approved}
    collection['registry']=[r for r in collection['registry'] if r['canonical_id'] in ids]
    for field in ('snapshots','future'): collection[field]={cid:s for cid,s in collection[field].items() if cid in ids}
    collection['resolution']=[r for r in collection['resolution'] if r['canonical_id'] in ids]
    collection=apply_provenance(collection,load(ROOT/'data/registry/provenance.json'))
    return apply_domains(collection,load(ROOT/'data/registry/business_domains.json'))

class Phase1FTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.collection=expanded(); cls.approved=approved_candidates(load(ROOT/'data/reports/phase1d_api_eligibility.json'))
        cls.previous=load(ROOT/'tests/fixtures/phase1f_previous_core.json')
    def test_approved_count_and_breakdown_are_exact(self):
        self.assertEqual(len(self.approved),38)
        self.assertEqual(Counter(r['scope_class'] for r in self.approved),{'DIRECT_CORRECTIONS':15,'CROSS_DOMAIN_CORRECTIONS':23})
        bad=load(ROOT/'data/reports/phase1d_api_eligibility.json'); bad['final_recommended_additions'].pop()
        with self.assertRaisesRegex(ValueError,'DISCREPANCY_STOP'): approved_candidates(bad)
    def test_exact_106_scope_and_104_current_two_historical(self):
        rows=self.collection['registry']; self.assertEqual(len(rows),106)
        self.assertEqual({r['canonical_id'] for r in rows},set(self.previous['previous_ids'])|{r['canonical_id'] for r in self.approved})
        self.assertEqual(Counter(r['status'] for r in rows),{'CURRENT':104,'REPEALED':2})
    def test_excluded_limited_review_absent(self):
        ids=set(self.collection['snapshots']); self.assertNotIn('admrul-30248',ids)
        report=load(ROOT/'data/reports/phase1d_api_eligibility.json')
        for row in report['records']:
            if row['eligibility_result'] in ('REVIEW','API_TRACKABLE_LIMITED','API_UNAVAILABLE'): self.assertNotIn(row['canonical_id'],ids)
        self.assertNotIn('국가공무원 인사운영처리지침',[r['current_name'] for r in self.collection['registry']])
    def test_provenance_covers_all_exactly_and_never_overrides_api_title(self):
        for r in self.collection['registry']:
            p=r['provenance']; s=self.collection['snapshots'][r['canonical_id']]
            self.assertEqual(p['api_tracking_class'],'API_TRACKABLE'); self.assertEqual(p['scope_review_status'],'APPROVED')
            self.assertTrue(p['selection_basis']); self.assertTrue(p['applies_to']); self.assertEqual(p['canonical_source_url'],s['official_source_url'])
            self.assertEqual(r['current_name'],s['metadata']['name']); self.assertEqual(p['structured_body_source'],'LAWGO_JSON_XML')
            if r['canonical_id'] in {x['canonical_id'] for x in self.approved}: self.assertIsNone(p['official_seed_name']); self.assertIsNone(p['official_seed_url'])
    def test_controlled_domains_and_no_review_in_production(self):
        taxonomy=load(ROOT/'data/seed/business_domains.json')['domains']; self.assertEqual(len(taxonomy),16); self.assertIn('보고',taxonomy)
        for r in self.collection['registry']:
            self.assertEqual(r['classification_status'],'REVIEWED'); self.assertTrue(r['business_domains'])
            self.assertTrue(set(r['business_domains'])<=set(taxonomy))
        self.assertNotIn('업무 분야 검토 중',json.dumps(self.collection['registry'],ensure_ascii=False))
    def test_requested_stable_ids_report_domain(self):
        for cid in ('admrul-32484','admrul-51868'):
            r=next(r for r in self.collection['registry'] if r['canonical_id']==cid)
            self.assertIn('보고',r['business_domains']); self.assertEqual(r['primary_domain'],'보고')
    def test_old_aliases_and_canonical_ids_retained(self):
        by_id={r['canonical_id']:r for r in self.collection['registry']}
        for cid,names in self.previous['aliases'].items():
            for field in ('seed_names','historical_names'): self.assertTrue(set(names[field])<=set(by_id[cid][field]))
    def test_lineage_ids_never_merged(self):
        by_id={r['canonical_id']:r for r in self.collection['registry']}
        for cid in ('admrul-26424','admrul-26917'):
            self.assertEqual(by_id[cid]['status'],'REPEALED'); self.assertEqual(by_id[cid]['provenance']['scope_class'],'HISTORICAL_REPEALED')
        self.assertEqual(by_id['admrul-84831']['status'],'CURRENT'); self.assertNotEqual('admrul-84831','admrul-26424')
    def test_tombstones_conservative_and_original_metadata_retained(self):
        for title in ('삭제','삭제 <2026. 10. 3.>','삭제 2026-10-03','삭제 (2026.10.3.)','삭제〈2026. 10. 3.〉','삭제 &lt;2016.1.22.&gt;'):
            a={'title':title,'url':'https://www.law.go.kr/LSW/flDownload.do?flSeq=1'}; original=copy.deepcopy(a)
            self.assertEqual(appendix_status(a),'REMOVED'); self.assertEqual(a,original)
        for title in ('개인정보 삭제 절차','삭제 대상 정보 목록','삭제 <정보>','폐지 규정 비교표'):
            self.assertEqual(appendix_status({'title':title}),'AVAILABLE')
    def test_current_appendix_status_keeps_archive_and_original_links(self):
        _,files=build_contract(self.collection,[],AT)
        for row in self.collection['registry']:
            cid=row['canonical_id']; raw=self.collection['snapshots'][cid]
            visible=files['rules/'+cid+'.json'][1]['current']['appendices']
            for original,current in zip(raw['appendices'],visible):
                self.assertEqual({k:v for k,v in current.items() if k!='status'},original)
                self.assertEqual(current['status'],appendix_status(original))
            archive=files[url(raw).removeprefix('/api/v1/')][1]
            self.assertEqual(archive['schema_version'],'1.1'); self.assertEqual(archive['version']['appendices'],raw['appendices'])
    def test_deleted_metadata_creates_explicit_removed_history(self):
        old=copy.deepcopy(next(iter(self.collection['snapshots'].values()))); new=copy.deepcopy(old); new['version_id']='999999'
        a={'title':'별표 시험','sequence':'1','branch':'0','type':'별표','url':None,'pdf_url':None}
        old['appendices']=[a]; new['appendices']=[{**a,'title':'삭제 <2026. 10. 3.>'}]
        e=make_event(old,new,AT); self.assertEqual(e['appendix_changes'][0]['status'],'REMOVED'); self.assertEqual(e['appendix_changes'][0]['after_metadata']['title'],'삭제 <2026. 10. 3.>')
        validate_contract('change',{'schema_version':'1.4','event':e})
    def test_schema_14_all_generated_files(self):
        _,files=build_contract(self.collection,[],AT)
        self.assertEqual(files['manifest.json'][1]['schema_version'],'1.5')
        for rel,(name,value) in files.items(): validate_contract(name,value)
    def test_low_confidence_has_other_and_internal_report(self):
        report=load(ROOT/'data/reports/phase1f_domain_review.json'); self.assertTrue(report['low_confidence'])
        for row in report['low_confidence']: self.assertEqual(row['primary_domain'],'기타')
    def test_future_body_drift_uses_safe_domain_fallback_without_periodic_human_gate(self):
        c=copy.deepcopy(self.collection); cid=next(iter(c['snapshots'])); c['snapshots'][cid]['hashes']['body_hash']='0'*64
        updated=apply_domains(c,load(ROOT/'data/registry/business_domains.json')); row=next(r for r in updated['registry'] if r['canonical_id']==cid)
        self.assertEqual(row['business_domains'],['기타']); self.assertEqual(row['classification_status'],'REVIEWED'); self.assertEqual(row['domain_assignment_status'],'FALLBACK')
    def test_unapproved_scope_or_api_class_rejected(self):
        c=copy.deepcopy(self.collection); c['registry'][0]['provenance']['api_tracking_class']='API_TRACKABLE_LIMITED'
        with self.assertRaisesRegex(ValueError,'INELIGIBLE'): apply_provenance(c)
    def test_approval_cannot_be_reused_for_later_scope(self):
        c=copy.deepcopy(self.collection); c['approved_expansion']='PHASE1F'
        with self.assertRaisesRegex(ValueError,'SCOPE_APPROVAL_MISMATCH'): verify_expansion(ROOT,{'seed_ids':list(c['snapshots'])},c)
    def test_one_disappearing_api_record_preserves_all_106(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(sync,'ROOT',Path(tmp)):
            sync.sync(self.collection); good=public_fingerprint(tmp)
            bad=copy.deepcopy(self.collection); cid=bad['registry'][-1]['canonical_id']; bad['registry'].pop(); bad['snapshots'].pop(cid)
            bad['resolution'][-1].update({'status':'REVIEW','review_reason':'API_TEMPORARILY_MISSING'})
            self.assertEqual(sync.sync(bad)['result'],'BLOCKED'); self.assertEqual(public_fingerprint(tmp),good)
            self.assertEqual(sync.sync(self.collection)['result'],'NO_CHANGE')
    def test_missing_stable_id_is_not_successful_repeal(self):
        row=next(r for r in self.collection['registry'] if r['source_kind']=='admrul' and r['status']=='CURRENT'); cid=row['canonical_id']; sn=self.collection['snapshots'][cid]
        with tempfile.TemporaryDirectory() as tmp,patch.object(collect_core,'ROOT',Path(tmp)),patch.object(collect_core,'LawClient') as client,patch.object(collect_core,'search',return_value=([],[])):
            write_json(Path(tmp)/'data/registry/state.json',{'seed_ids':[cid],'snapshots':{cid:sn}}); write_json(Path(tmp)/'data/registry/rules.json',[row])
            client.return_value.fetch.return_value=({'Empty':None},{})
            c=collect_core.run(); self.assertEqual(c['registry'],[]); self.assertEqual(c['resolution'][0]['review_reason'],'MISSING_CURRENT_REQUIRES_REVIEW')
    def test_admin_future_lid_requires_exact_structured_current_predecessor(self):
        row=copy.deepcopy(next(r for r in self.collection['registry'] if r['source_kind']=='admrul' and r['status']=='CURRENT')); cid=row['canonical_id']
        current=copy.deepcopy(self.collection['snapshots'][cid]); current['metadata']['official_state']='N'
        future=copy.deepcopy(current); future['version_id']=str(int(current['version_id'])+1); future['metadata']['official_state']='Y'; future['metadata']['effective_date']='2070-01-01'
        raw={'R':{'행정규칙기본정보':{'행정규칙일련번호':future['version_id']}}}
        item={'행정규칙ID':current['stable_identifier'],'행정규칙일련번호':current['version_id'],'시행일자':current['metadata']['effective_date'].replace('-',''),'발령일자':current['metadata']['issue_date'].replace('-','')}
        with tempfile.TemporaryDirectory() as tmp,patch.object(collect_core,'ROOT',Path(tmp)),patch.object(collect_core,'LawClient') as client,patch.object(collect_core,'snapshot',side_effect=[future,current]),patch.object(collect_core,'save_snapshot'),patch.object(collect_core,'search',return_value=([item],[])):
            client.return_value.fetch.return_value=(raw,{})
            c=collect_core.run(state={'seed_ids':[cid],'snapshots':{cid:current}},trusted=[row])
            self.assertEqual(c['snapshots'][cid]['version_id'],current['version_id']); self.assertEqual(c['future'][cid][0]['version_id'],future['version_id']); self.assertEqual(c['resolution'][0]['status'],'RESOLVED')
    def test_page_monitor_failure_independent_of_tracking(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(sync,'ROOT',Path(tmp)),patch.object(production_sync,'ROOT',Path(tmp)),patch.object(production_sync,'discover',side_effect=ValueError('MONITOR_FAILED')),patch.object(production_sync,'collect_core',return_value=self.collection):
            r=production_sync.run(discovery=True); self.assertEqual(r['result'],'PUBLISHED'); self.assertEqual(r['discovery_monitor_error'],'DISCOVERY_MONITOR_UNAVAILABLE')
    def test_production_paths_introduce_no_html_or_document_parser_imports(self):
        forbidden=('scripts.collect','pipeline.corrections_seed','bs4','BeautifulSoup','playwright','selenium','pypdf','pdfplumber','pytesseract')
        paths=['scripts/production_sync.py','scripts/collect_core.py','scripts/discovery_scan.py','scripts/observe.py','scripts/sync.py','scripts/prepare_expansion.py','scripts/backfill_history.py','pipeline/law_api/revalidation.py']
        for path in paths:
            tree=ast.parse((ROOT/path).read_text(encoding='utf8'))
            imports=[n.module or '' for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]+[a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]
            self.assertFalse(any(i==f or i.startswith(f+'.') for i in imports for f in forbidden),path)
    def test_existing_schedule_dispatch_concurrency_and_heartbeat_preserved(self):
        self.assertEqual(workflows()['status'],'PASS')
        from scripts.scheduled_sync import policy
        from datetime import date
        self.assertEqual(policy('37 23 * * *',day=date(2026,10,4)),{'discovery':True,'full_audit':True})
        self.assertEqual(policy('37 11 * * *',day=date(2026,10,4)),{'discovery':False,'full_audit':False})
    def test_persistent_old_history_payloads_match_original_hashes(self):
        recorded=load(ROOT/'data/registry/change_history.json'); by_id={e['event_id']:e for e in recorded}
        for eid,hash_value in self.previous['persistent_event_hashes'].items(): self.assertEqual(digest(by_id[eid]),hash_value)
    def test_live_backfill_new_ids_and_recent_comparisons_where_available(self):
        path=ROOT/'data/staging/phase1f_backfill.json'
        if path.exists():
            b=load(path); self.assertEqual(len(b['records']),38); self.assertTrue(all(r['status']=='PASS' for r in b['records']))
            events=[make_event(p['before'],p['after'],b['started_at'],official_comparison=p['official_comparison'],comparison_evidence=p['comparison_evidence']) for p in b['pairs']]; events=merge([],events)
        else:
            events=[e for e in load(ROOT/'data/registry/change_history.json') if e['canonical_id'] in {r['canonical_id'] for r in self.approved}]
        self.assertEqual({e['canonical_id'] for e in events},{r['canonical_id'] for r in self.approved}); self.assertTrue(recent(events,'2026-10-03'))
        self.assertTrue(any(e['comparison_source']=='LAWGO_ADMIN_OLD_NEW' for e in events))
        for e in events: assert_public_safe(e)

if __name__=='__main__': unittest.main()

"""Audit-only gates and isolated expanded publication rehearsals."""
import ast
import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from urllib.parse import quote,quote_plus
from unittest.mock import patch
from pipeline.normalize import digest
from pipeline.diff import compare
from pipeline.snapshot import write_json
from pipeline.publication import build_contract
from scripts import sync
from scripts.audit_api_eligibility import assess,fingerprint,OUT

ROOT=Path(__file__).resolve().parents[1]

def load(path): return json.loads(Path(path).read_text(encoding='utf-8'))

def eligible_records():
    return [r for r in load(OUT/'records.json') if r['group'] in ('CURRENT_68','NEW_39') and r['production_eligible']]

def expanded_collection():
    records=eligible_records(); original={r['canonical_id']:r for r in load(ROOT/'data/registry/rules.json')}
    rows=[]; snapshots={}; future={}; resolution=[]
    for r in records:
        cid=r['canonical_id']; s=r['snapshot']; meta=s['metadata']
        row=copy.deepcopy(original.get(cid,{'canonical_id':cid,'source_kind':s['source_kind'],'seed_names':[],'historical_names':[],'corrections_category':meta['rule_type'],'business_domains':[],'classification_status':'REVIEW','status':r['current_status'],'law_or_rule_identifier':s['stable_identifier'],'last_verified_at':'2026-10-03T00:00:00+00:00'}))
        row.update({'current_name':meta['name'],'version_id':s['version_id'],'current_effective_date':meta['effective_date'],'official_source':s['official_source_url']})
        rows.append(row); snapshots[cid]=s; future[cid]=r['future_effective_capability']['future_versions']
        resolution.append({'canonical_id':cid,'status':'RESOLVED'})
    from pipeline.registry.provenance import apply_provenance
    from pipeline.registry.domains import apply_domains
    collection={'complete':True,'registry':rows,'snapshots':snapshots,'future':future,'resolution':resolution}
    collection=apply_provenance(collection,load(ROOT/'data/registry/provenance.json'))
    return apply_domains(collection,load(ROOT/'data/registry/business_domains.json'))

def public_fingerprint(root):
    return {str(p.relative_to(root)):[digest(p.read_text(encoding='utf-8')),p.stat().st_mtime_ns] for p in (Path(root)/'public/api/v1').rglob('*.json')}

def proposed_13_validate(name,value):
    # In-memory compatibility rehearsal only: the frozen 1.2 files are never
    # edited. Provenance approval/data migration remain explicit release work.
    from jsonschema import Draft202012Validator,FormatChecker
    from pipeline.validation import assert_public_safe
    schema=load(ROOT/'schemas'/f'{name}.schema.json')
    def extend(node):
        if isinstance(node,dict):
            if 'schema_version' in node and isinstance(node['schema_version'],dict) and node['schema_version'].get('const')=='1.2': node['schema_version']['const']='1.3'
            if 'corrections_category' in node and isinstance(node['corrections_category'],dict):
                enum=node['corrections_category'].get('enum')
                if enum is not None and '지침' not in enum: enum.append('지침')
            for v in node.values(): extend(v)
        elif isinstance(node,list):
            for v in node: extend(v)
    extend(schema)
    Draft202012Validator(schema,format_checker=FormatChecker()).validate(value)
    assert_public_safe(value)

class Phase1DAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records=load(OUT/'records.json')
        if len([r for r in cls.records if r['group']=='CURRENT_68'])!=68 or len([r for r in cls.records if r['group']=='NEW_39'])!=39: raise ValueError('LIVE_AUDIT_INCOMPLETE')

    def test_every_trackable_has_identity_metadata_body_date_and_status(self):
        for r in self.records:
            if r.get('api_capability_class',r['eligibility_result'])!='API_TRACKABLE': continue
            with self.subTest(cid=r['canonical_id']):
                s=r['snapshot']; self.assertEqual(s['canonical_id'],s['source_kind']+'-'+s['stable_identifier'])
                self.assertTrue(s['stable_identifier'].isdigit()); self.assertTrue(r['current_metadata'])
                self.assertTrue(s['body']['articles']); self.assertTrue(s['metadata']['effective_date']); self.assertTrue(s['metadata']['issue_date'])
                self.assertIn(r['current_status'],('CURRENT','REPEALED','FUTURE_EFFECTIVE'))
                self.assertTrue(r['repeat_deterministic']); self.assertEqual(s['hashes'],r['repeat_snapshot']['hashes'])
                self.assertTrue(all(ev['http_status']==200 and ev['request']['type'] in ('JSON','XML') for ev in r['api_evidence']))

    def test_limited_unavailable_and_scope_review_never_eligible(self):
        for r in self.records:
            if r['eligibility_result']!='API_TRACKABLE' or not r['scope_pass']: self.assertFalse(r['production_eligible'])
        limited=next(r for r in self.records if r['canonical_id']=='admrul-30248')
        self.assertIn(limited['eligibility_result'],('API_TRACKABLE_LIMITED','API_UNAVAILABLE'))
        self.assertFalse(limited['production_eligible'])

    def test_metadata_only_response_is_limited(self):
        first={'payload':{'행정규칙':{'행정규칙기본정보':{'행정규칙ID':'999','행정규칙일련번호':'888','행정규칙명':'시험','시행일자':'20261001','발령일자':'20261001'},'조문내용':''}},'serial':'888','status':'CURRENT','resolution_method':'AUDIT_TEST_STABLE_LID','evidence':{'request':{'type':'JSON'},'endpoint':'https://www.law.go.kr/DRF/lawService.do'},'resolution_evidence':[],'future':[]}
        result=assess(first,copy.deepcopy(first),'admrul','admrul-999')
        self.assertEqual(result['eligibility_result'],'API_TRACKABLE_LIMITED'); self.assertFalse(result['production_eligible'])

    def test_unavailable_detail_cannot_enter_production(self):
        from scripts.audit_api_eligibility import audit
        with patch('scripts.audit_api_eligibility.one',side_effect=ValueError('MISSING_CURRENT_AND_HISTORY')):
            result=audit(None,{'canonical_id':'admrul-999','name':'시험','scope_class_candidate':'DIRECT_CORRECTIONS'},'NEW_39')
        self.assertEqual(result['eligibility_result'],'API_UNAVAILABLE'); self.assertFalse(result['production_eligible'])

    def test_no_html_or_document_parsers_introduced(self):
        paths=[ROOT/'scripts/audit_api_eligibility.py',ROOT/'scripts/report_phase1d.py',ROOT/'scripts/verify_phase1d.py',ROOT/'tests/test_phase1d.py']
        forbidden=('bs4','BeautifulSoup','playwright','selenium','pypdf','pdfplumber','hwp','pytesseract','scripts.collect','scripts.audit_scope')
        for path in paths:
            tree=ast.parse(path.read_text(encoding='utf-8'))
            imports=[]
            for node in ast.walk(tree):
                if isinstance(node,ast.Import): imports.extend(alias.name for alias in node.names)
                elif isinstance(node,ast.ImportFrom): imports.append(node.module or '')
            self.assertFalse(any(any(name==f or name.startswith(f+'.') for f in forbidden) for name in imports),str(path))

    def test_no_credentials_in_evidence_or_reports(self):
        secret=os.environ.get('LAW_API_OC','').strip(); self.assertTrue(secret)
        tokens={secret,quote(secret,safe=''),quote_plus(secret)}
        files=list(OUT.rglob('*.json'))+list((ROOT/'data/reports').glob('phase1d*.*'))+list((ROOT/'data/raw_cache/phase1d').glob('*'))
        for p in files:
            if p.is_file(): self.assertFalse(any(t in p.read_text(encoding='utf-8') for t in tokens),p.name)

    def test_repeat_query_has_no_diff_events_for_expanded_set(self):
        for r in eligible_records():
            self.assertEqual(compare(r['snapshot'],r['repeat_snapshot'],'2026-10-03T01:00:00+00:00',repeal_evidence=r.get('repeal_evidence')),[],r['canonical_id'])

    def test_future_amendment_detects_body_name_dates_and_appendix_metadata(self):
        base=copy.deepcopy(next(r['snapshot'] for r in eligible_records() if r['group']=='NEW_39'))
        revised=copy.deepcopy(base); revised['version_id']=str(int(base['version_id'])+1)
        revised['metadata'].update({'name':base['metadata']['name']+' (감사 모의 개정)','issue_date':'2026-10-04','effective_date':'2026-10-05'})
        revised['body']['articles']={'조문내용':'감사 전용 모의 개정; 실제 법령이 아님'}
        revised['appendices']=[{'title':'감사 모의 별표','type':'별표','sequence':'1','branch':'0','url':None,'pdf_url':None}]
        revised['hashes']['metadata_hash']=digest(revised['metadata']); revised['hashes']['body_hash']=digest(revised['body']); revised['hashes']['appendix_hash']=digest(revised['appendices'])
        types={e['change_type'] for e in compare(base,revised,'2026-10-05T00:00:00+00:00')}
        self.assertTrue({'RULE_AMENDED','RULE_RENAMED','EFFECTIVE_DATE_CHANGED','ARTICLE_CHANGED','APPENDIX_CHANGED'}<=types)
        self.assertNotEqual(base['hashes']['metadata_hash'],revised['hashes']['metadata_hash'])

    def test_expanded_success_failure_no_change_recovery(self):
        collection=expanded_collection(); before_production=fingerprint()
        OUT.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='rehearsal-',dir=OUT) as tmp,patch.object(sync,'ROOT',Path(tmp)),patch('pipeline.publication.SCHEMA_VERSION','1.5'),patch('pipeline.publication.validate_contract',side_effect=proposed_13_validate):
            first=sync.sync(collection); self.assertEqual(first['result'],'PUBLISHED')
            good=public_fingerprint(Path(tmp)); state=load(Path(tmp)/'data/registry/state.json'); health=load(Path(tmp)/'data/ops/health.json')
            broken=copy.deepcopy(collection); bad=next(r['canonical_id'] for r in eligible_records() if r['group']=='NEW_39')
            for row in broken['resolution']:
                if row['canonical_id']==bad: row.update({'status':'REVIEW','review_reason':'SIMULATED_API_TIMEOUT'})
            broken['registry']=[r for r in broken['registry'] if r['canonical_id']!=bad]; broken['snapshots'].pop(bad)
            self.assertEqual(len(broken['registry']),len(collection['registry'])-1)
            self.assertEqual(sync.sync(broken)['result'],'BLOCKED'); self.assertEqual(public_fingerprint(Path(tmp)),good)
            self.assertEqual(load(Path(tmp)/'data/registry/state.json'),state)
            degraded=load(Path(tmp)/'data/ops/health.json'); self.assertEqual(degraded['last_dataset_version'],health['last_dataset_version']); self.assertEqual(degraded['last_successful_sync'],health['last_successful_sync'])
            second=sync.sync(collection); third=sync.sync(collection)
            self.assertEqual(second['result'],'NO_CHANGE'); self.assertEqual(third['result'],'NO_CHANGE')
            self.assertEqual(second['new_events'],0); self.assertEqual(third['new_events'],0)
            self.assertEqual(public_fingerprint(Path(tmp)),good)
            report_name='phase1g_legacy_rehearsal.json' if len(load(ROOT/'data/registry/rules.json'))==107 else 'phase1f_legacy_rehearsal.json'
            write_json(ROOT/'data/reports'/report_name,{'record_count':len(collection['registry']),'transitions':[first['result'],'BLOCKED',second['result'],third['result']],'one_rule_failure_isolated':True,'last_good_preserved':True,'public_bytes_and_mtimes_preserved':True,'events_after_repeats':len(load(Path(tmp)/'data/registry/events.json')),'mode':'ISOLATED_TEMP_DIRECTORY; ACTIVE_1.5_CONTRACT; NO PRODUCTION PUBLICATION','dataset_version':first['dataset_version']})
        self.assertEqual(before_production,fingerprint())

    def test_frozen_13_rejects_expanded_rule_kind_fail_closed(self):
        from jsonschema import Draft202012Validator
        from jsonschema.exceptions import ValidationError
        _,files=build_contract(expanded_collection(),[],'2026-10-03T00:00:00+00:00')
        value=copy.deepcopy(files['rules/admrul-2036599.json'][1]); value['schema_version']='1.3'
        value['rule'].pop('provenance'); value['rule'].pop('domain_assignment_status')
        for s in [value['current']]+value['upcoming']:
            for a in s['appendices']: a.pop('status',None)
        schema=load(ROOT/'tests/fixtures/phase1e_rule.schema.json')
        with self.assertRaises(ValidationError): Draft202012Validator(schema).validate(value)

    def test_metadata_only_changes_change_dataset_identity(self):
        collection=expanded_collection(); original,_=build_contract(collection,[],'2026-10-03T00:00:00+00:00')
        altered=copy.deepcopy(collection); cid=next(iter(altered['snapshots'])); value=altered['snapshots'][cid]
        value['metadata']['issue_date']='2026-10-04'; value['hashes']['metadata_hash']=digest(value['metadata'])
        changed,_=build_contract(altered,[],'2026-10-03T00:00:00+00:00')
        self.assertNotEqual(original,changed)

    def test_lineage_classifications_are_deterministic_and_evidence_bound(self):
        from scripts.report_phase1d import lineage
        first=lineage(self.records); second=lineage(copy.deepcopy(self.records)); self.assertEqual(first,second)
        for r in first['repealed_two']:
            self.assertTrue(r['old']['repeal_evidence']); self.assertIn(r['relationship'],('SAME_LINEAGE_NEW_ID','RENAMED_SUCCESSOR','SUPERSEDED_BY','TRULY_REPEALED_NO_SUCCESSOR','UNRELATED','UNKNOWN_REVIEW'))
            if r['relationship']!='UNKNOWN_REVIEW' and r.get('successor'): self.assertTrue(r['relationship_evidence'])

    def test_proposed_schema_rejects_ineligible_public_provenance(self):
        from jsonschema import Draft202012Validator
        schema=load(ROOT/'data/reports/phase1d_schema13_provenance_candidate.json')
        example={'scope_class':'DIRECT_CORRECTIONS','selection_basis':'공식 API 적용범위 확인','applies_to':['교정기관'],'official_seed_name':None,'official_seed_url':None,'canonical_source_url':'https://www.law.go.kr/LSW/admRulLsInfoP.do?admRulSeq=1','discovery_source':['LAW_API_KEYWORD'],'scope_review_status':'APPROVED','api_tracking_class':'API_TRACKABLE'}
        Draft202012Validator(schema).validate(example)
        example['api_tracking_class']='API_TRACKABLE_LIMITED'
        self.assertFalse(Draft202012Validator(schema).is_valid(example))

if __name__=='__main__': unittest.main()

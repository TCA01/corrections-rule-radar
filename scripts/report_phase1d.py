"""API-only eligibility, evidence-bound lineage and unpublished 1.3 proposal."""
import json
import sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.snapshot import write_json
from pipeline.normalize import digest
from pipeline.registry import detail_url
from scripts.audit_api_eligibility import OUT,fingerprint

CLASSES=('API_TRACKABLE','API_TRACKABLE_LIMITED','API_UNAVAILABLE','NOT_CORRECTIONS','REVIEW')

def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))

def texts(value):
    if isinstance(value,str): yield value
    elif isinstance(value,dict):
        for v in value.values(): yield from texts(v)
    elif isinstance(value,list):
        for v in value: yield from texts(v)

def lineage(records):
    by_id={r['canonical_id']:r for r in records}
    searches=read(OUT/'lineage_searches.json'); details=read(OUT/'lineage_details.json')
    old_rows=[]
    for cid in ('admrul-26424','admrul-26917'):
        r=by_id[cid]; meta=r['snapshot']['metadata']
        old={'canonical_id':cid,'title':meta['name'],'rule_type':meta['rule_type'],'issue_number':meta['issue_number'],'issue_date':meta['issue_date'],'effective_date':meta['effective_date'],'status':r['current_status'],'repeal_evidence':r['repeal_evidence'],'official_api_query':r['detail_query'],'official_url':r['snapshot']['official_source_url'],'reason_production_marked_repealed':'안정 ID 현행 LID 응답 없음 + 동일 ID 연혁 최신 항목의 폐지 표시 + 폐지 일련번호 상세 본문의 폐지·시행일 확인. 빈 응답만으로 폐지 추정하지 않음.'}
        operative=[i for i in r['history_availability']['items'] if i.get('제개정구분명') not in ('폐지','타법폐지')]
        old['last_operative_version']=max(operative,key=lambda i:(i['발령일자'],i['행정규칙일련번호'])) if operative else None
        old['tracked_version_role']='폐지 최종 버전. last_operative_version에 마지막 유효 버전의 발령번호·시행일을 별도 보존.'
        candidate=by_id.get('admrul-84831') if cid=='admrul-26424' else None
        successor=None
        if candidate:
            m=candidate['snapshot']['metadata']
            successor={'canonical_id':candidate['canonical_id'],'current_title':m['name'],'issue_number':m['issue_number'],'effective_date':m['effective_date'],'status':candidate['current_status'],'official_url':candidate['snapshot']['official_source_url'],'confirmed_successor':False}
        relevant={k:v for k,v in searches.items() if ('교정직제 영어 명칭' in k if candidate else ('교정공무원 예절' in k or '교정공무원 행동' in k))}
        related_details={k:v for k,v in details.items() if v['canonical_id'] in (cid,'admrul-84831')}
        # Neither shared vocabulary nor an overlapping purpose proves a legal
        # successor relationship. No ID merge without explicit API text.
        old_rows.append({'old':old,'successor':successor,'relationship':'UNKNOWN_REVIEW','relationship_evidence':{'structured_searches':relevant,'structured_detail_versions':related_details},'finding':'폐지는 공식 API로 확정. 새 영어명칭 규정은 다른 ID의 2023년 제정 규정이며 기능상 후보다. 조회한 공식 본문·부칙·개정이유에 기존 ID의 자동 승계·대체를 확정하는 명시 근거가 없어 연결 보류.' if candidate else '2023-10-19 폐지 확정. 정확 명칭과 교정공무원 예절·행동 현행/연혁 검색에서 확정 후속 규정을 찾지 못함. 유사한 공무원 행동강령을 후계자로 추정하지 않으며 후속 부재의 보편적 증명 대신 UNKNOWN_REVIEW 유지.'})
    extra=read(OUT/'lineage_supplement.json') if (OUT/'lineage_supplement.json').exists() else None
    if extra:
        for row in extra['records']:
            root=next(iter(row['payload'].values())); m=root.get('행정규칙기본정보',{})
            if m.get('현행여부')!='Y': continue
            terminal=details[by_id['admrul-26424']['snapshot']['version_id']]['payload']
            explicit_reason=' '.join(texts(next(iter(terminal.values())).get('제개정이유',{})))
            # The official repeal rationale explicitly cites rule 40 as making
            # the correction-specific rule unnecessary. This proves functional
            # supersession, not legal ID identity or automatic event merging.
            if '정부조직 영어명칭에 관한 규칙' in explicit_reason:
                old_rows[0]['related_2023_candidate']=old_rows[0]['successor']
                old_rows[0]['successor']={'canonical_id':row['canonical_id'],'current_title':m['행정규칙명'],'issue_number':m['발령번호'],'effective_date':m['시행일자'],'status':'CURRENT','official_url':detail_url('admrul',str(m['행정규칙일련번호'])),'confirmed_successor':True,'relationship_scope':'폐지이유가 명시한 공통 영어명칭 기준의 기능 대체; 동일 법적 안정 ID 아님'}
                old_rows[0]['relationship']='SUPERSEDED_BY'
                old_rows[0]['relationship_evidence']['explicit_repeal_reference']=extra
                old_rows[0]['finding']='폐지이유는 정부조직 영어명칭 규칙(행안부 예규 40호)의 존재로 법무부 개별 예규 관리 필요성이 낮아 폐지한다고 명시한다. 해당 공통 규칙의 과거 40호와 현행 390호는 동일 안정 ID 49753이며 현재 명칭은 정부조직 약칭과 영어 명칭에 관한 규칙이다. 따라서 기능상 SUPERSEDED_BY로 연결하되 26424와 49753은 ID를 합치지 않는다. 2023년 별도 제정 84831을 자동 동일계보 후계자로 추정하지 않는다.'
    repeal_terminal=details[by_id['admrul-26917']['snapshot']['version_id']]['payload']
    repeal_reason=' '.join(texts(next(iter(repeal_terminal.values())).get('제개정이유',{})))
    current_etiquette=searches['교정공무원 예절/1']['items']
    if '사문화' in repeal_reason and '폐지' in repeal_reason and not current_etiquette:
        old_rows[1]['relationship']='TRULY_REPEALED_NO_SUCCESSOR'
        old_rows[1]['relationship_evidence']['explicit_simple_repeal_reason']=repeal_reason
        old_rows[1]['finding']='공식 폐지이유는 강제적 예절의 악용 우려·경직된 문화·현장 사문화를 이유로 자율성을 위해 규정을 없앤다고 명시한다. 대체·재제정 조항이 없고 조회한 현행 교정공무원 예절·행동 규정에도 후계가 없어 명시적 단순 폐지로 분류한다. NO_SUCCESSOR는 이 규정의 공식 연혁·폐지이유·검색 범위에서 확인된 결과이며 모든 유사 업무 규정의 부존재를 보장하는 표현은 아니다.'
    duty=by_id['admrul-30248']; history=duty['history_availability']['items']
    stable_ids={str(i['행정규칙ID']) for i in history}; versions={str(i['행정규칙일련번호']) for i in history}
    exact=searches['국가공무원 복무·징계 관련 예규/1']['items']
    current=[i for i in exact if str(i['행정규칙ID'])=='30248']
    continuity={'name':'국가공무원 복무·징계 관련 예규','scope_class':'CROSS_DOMAIN_CORRECTIONS','canonical_id':'admrul-30248','current_api_metadata':duty['current_metadata'],'eligibility_result':duty['eligibility_result'],'failure_reason':duty['failure_reason'],'stable_history_identity_verified':stable_ids=={'30248'} and len(versions)>1 and len(current)==1,'history_version_count':len(versions),'old_and_current_same_canonical_id':True,'relationship_to_actual_repealed_two':'UNRELATED','older_production_record_incorrectly_marked_repealed':False,'finding':'구·현행 API 연혁은 동일 안정 ID 30248의 서로 다른 버전이다. 현재 68개에 이 규정의 구·현행 레코드가 없고 실제 폐지 2건과 무관하다. 추적한다면 안정 ID 30248을 사용해야 하지만 현행 operative 본문은 HWPX/PDF 첨부만 제공되고 조문내용이 비어 API-only core 편입 불가. 메타데이터·제개정이유를 전체 본문으로 취급하지 않음.','evidence':{'current_list':current,'history':duty['history_availability'],'details':{k:v for k,v in details.items() if v['canonical_id']=='admrul-30248'},'repeat_api':duty['api_evidence']}}
    personnel_title='국가공무원 인사운영처리지침'
    exact_current=[i for i in searches[personnel_title+'/1']['items'] if i['행정규칙명'].replace(' ','')==personnel_title]
    exact_old=[i for i in searches[personnel_title+'/2']['items'] if i['행정규칙명'].replace(' ','')==personnel_title]
    personnel={'name':personnel_title,'exact_current_count':len(exact_current),'exact_history_count':len(exact_old),'canonical_id':None,'eligibility_result':'REVIEW','scope_class':'REVIEW','production_historical_record_exists':False,'finding':'현행·연혁 정확 명칭에 해당 항목을 확인하지 못했고 실제 운영 68개에도 해당 과거 레코드가 없다. 안정 ID가 없으므로 명칭 변경·승계·API 추적 여부 확정 불가. 유사 제목으로 대체하지 않음.','recommended_action':'원 공식 명칭 또는 안정 ID 확인 전 DISCOVERY_SCOPE_REVIEW로 보류','evidence':{k:v for k,v in searches.items() if '인사운영' in k}}
    return {'repealed_two':old_rows,'national_duty_discipline':continuity,'national_personnel_guideline':personnel,'policy':'명시적인 공식 API 승계 근거 없으면 UNKNOWN_REVIEW. 폐지이유가 다른 규정을 관리 불필요 사유로 직접 지목하면 기능상 SUPERSEDED_BY로 기록하며 ID 병합은 하지 않음. 단순 폐지 NO_SUCCESSOR는 공식 폐지이유 및 조회 범위 내 판정. 같은 안정 ID의 버전 변화와 다른 안정 ID의 승계를 구분.'}

def schema13():
    props={'scope_class':{'enum':['OFFICIAL_CORRECTIONS_LIST','DIRECT_CORRECTIONS','CROSS_DOMAIN_CORRECTIONS','HISTORICAL_REPEALED']},'selection_basis':{'type':'string','minLength':1},'applies_to':{'type':'array','minItems':1,'uniqueItems':True,'items':{'type':'string','minLength':1}},'official_seed_name':{'type':['string','null']},'official_seed_url':{'anyOf':[{'type':'string','format':'uri','pattern':'^https://www\\.corrections\\.go\\.kr/'},{'type':'null'}]},'canonical_source_url':{'type':'string','format':'uri','pattern':'^https://(www\\.)?law\\.go\\.kr/LSW/'},'discovery_source':{'type':'array','minItems':1,'uniqueItems':True,'items':{'enum':['CORRECTIONS_PAGE','LAW_API_KEYWORD','LAW_API_MINISTRY','CORE_SYSTEM_MAP','MANUAL_OFFICIAL_REVIEW']}},'scope_review_status':{'const':'APPROVED'},'api_tracking_class':{'const':'API_TRACKABLE'},'first_seen_at':{'type':['string','null'],'format':'date-time'},'last_seen_on_corrections_page':{'type':['string','null'],'format':'date-time'}}
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:corrections-rule-radar:unpublished:1.3:production-provenance','title':'UNPUBLISHED schema 1.3 proposed production provenance','type':'object','additionalProperties':False,'required':list(props)[:9],'properties':props,'description':'정식 API 스키마나 freeze lock에 적용하지 않은 검토용 하위 계약. 내부 discovery 계약의 API class는 5개 전체 enum을 허용하되 공개 추적 규정 provenance는 API_TRACKABLE만 허용.'}

def counts(records,group):
    counter=Counter(r['eligibility_result'] for r in records if r['group']==group)
    return {k:counter.get(k,0) for k in CLASSES}

def main():
    records=read(OUT/'records.json'); integrity=read(OUT/'integrity.json'); lin=lineage(records)
    from pipeline.law_api.client import parse_payload
    from pipeline.registry import unwrap
    for r in records:
        proof=r.get('api_evidence',[])
        if proof:
            ev=proof[0]; raw=Path('data/raw_cache/phase1d')/(ev['cache_key']+'.'+ev['request']['type'].lower())
            root=unwrap(parse_payload(raw.read_bytes(),ev['request']['type']))
            r['structured_appendix_metadata']=root.get('별표')
            r['structured_attachment_metadata']=root.get('첨부파일')
            r['http_result_success']=ev['http_status']==200
            r['api_result_code']=root.get('resultCode','NOT_PROVIDED_IN_DETAIL_RESPONSE')
        r['current_name']=r.get('snapshot',{}).get('metadata',{}).get('name') or r.get('current_metadata',{}).get('행정규칙명') or r['candidate_name']
        if r.get('snapshot'):
            r['rule_type']=r['snapshot']['metadata']['rule_type']
            r['source_ministry']=r['snapshot']['metadata']['ministry']
        r['selected_for_proposed_expansion']=r['group']=='NEW_39' and r['production_eligible']
        r['inclusion_approval']='EXISTING_REGISTRY' if r['group']=='CURRENT_68' else 'HUMAN_REVIEW_PENDING; NOT_IN_PRODUCTION'
        r['current_metadata_available']=bool(r.get('current_metadata'))
        r['current_body_available']=bool(r.get('body_available'))
        r['effective_date_available']=bool(r.get('effective_date'))
        r['status_available']=r.get('current_status') in ('CURRENT','FUTURE_EFFECTIVE','REPEALED')
        r['json_xml_availability']=r.get('response_format_tested',[])
        r['tracking_mode']='HISTORICAL_TERMINAL_REPEAL' if r.get('current_status')=='REPEALED' else 'CURRENT_API' if r.get('production_eligible') else 'DISCOVERY_ONLY'
        r['body_role']='폐지 최종 버전의 구조화 텍스트/이력; 현재 유효한 업무 기준 본문이 아님' if r.get('current_status')=='REPEALED' else '정형 API 본문; 첨부파일 의미는 읽지 않음'
        r['change_detection_fields']={'name':'metadata_hash + RULE_RENAMED','status':'현행 API 여부 + 명시적 폐지 history/detail proof; 빈 결과는 REVIEW','effective_date':'metadata_hash + EFFECTIVE_DATE_CHANGED','issue_date':'metadata_hash; 정상 새 버전은 RULE_AMENDED; 동일 일련번호 정정 이벤트 보완 필요','body_articles':'body_hash + ARTICLE_CHANGED','appendix_metadata':'appendix_hash','attachment_metadata_links':'attachment_link_hash; 현재 배열 표현 오류 보완 필요'}
    current=counts(records,'CURRENT_68'); new=counts(records,'NEW_39')
    eligible=[r for r in records if r['group'] in ('CURRENT_68','NEW_39') and r['production_eligible']]
    added=[r for r in eligible if r['group']=='NEW_39']; final_ids=[r['canonical_id'] for r in eligible]
    discovery_only=[r for r in records if r['group']!='CURRENT_68' and r['canonical_id'] not in final_ids]
    for r in discovery_only:
        r['discovery_status']='DISCOVERY_API_LIMITED' if r['eligibility_result']=='API_TRACKABLE_LIMITED' else 'DISCOVERY_API_UNAVAILABLE' if r['eligibility_result']=='API_UNAVAILABLE' else 'DISCOVERY_SCOPE_REVIEW'
    dry=read(OUT/'expanded_rehearsal.json') if (OUT/'expanded_rehearsal.json').exists() else None
    verification=read('data/reports/phase1d_verification.json') if Path('data/reports/phase1d_verification.json').exists() else None
    expected_calls=90+len(added)
    performance={'estimate_only':True,'baseline_calls':90,'baseline_duration_seconds':99.031,'additional_current_admin_calls':len(added),'expected_calls_per_run':expected_calls,'expected_runtime_seconds':round(expected_calls/90*99.031,1),'twice_daily_api_calls':expected_calls*2,'audit_overhead_excluded':'반복 검증·전수 연혁·승계 검색은 일상 sync마다 재실행하지 않음. 신규 현행 행정규칙은 안정 LID 상세 1회, 폐지·실패 시 공식 history fallback 추가 호출.','sustainability':'PASS','basis':'현재 순차 간격 1.1초와 Phase1B 90회/99.031초 실제 측정에 선형 추정. 오류·재시도·새 시행예정 법령 수에 따라 증가 가능. API 제공자 quota 보장 아님.','optimization':'JSON/XML 응답 내 안정 ID와 상태 검증을 유지. 실행 내 동일 ID 요청은 공유 가능; 법무부 목록 batch는 discovery에만 사용하고 상세 본문 검증을 대체하지 않음.'}
    metadata_probe=[]
    from pipeline.diff import compare
    import copy
    for r in eligible:
        s=r['snapshot']; n=copy.deepcopy(s); n['metadata']['issue_date']='2099-01-01'; n['hashes']['metadata_hash']=digest(n['metadata'])
        events=compare(s,n,'2099-01-01T00:00:00+00:00',repeal_evidence=r.get('repeal_evidence'))
        metadata_probe.append({'canonical_id':r['canonical_id'],'metadata_hash_detects_change':s['hashes']['metadata_hash']!=n['hashes']['metadata_hash'],'same_serial_issue_date_change_has_event':bool(events)})
    malformed_attachments=[r['canonical_id'] for r in eligible if any("['" in a.get('url','') for a in r['snapshot']['attachments'])]
    migration={'proposed_schema':'1.3','published':False,'current_schema_kept':'1.2','production_registry_changed':False,'provenance_location':'rule.provenance + list summary.provenance; API version remains /v1 only with explicit schema_version 1.3 and client acceptance','required_fields':list(schema13()['required']),'mandatory_approval':'각 추가 항목의 범위 및 업무분야 검토, 1.3 클라이언트 수용 확인 후 원자적 전환. 기존 불변 archive 1.1 URL/내용 보존.','api_only_collector':'운영 core는 안정 ID 구조화 API만 사용. HTML 기반 seed/outgoing 탐색은 core 자동 추적의 필수 의존성에서 제거하며 별도 내부 발견으로만 분리. Phase1D는 기존 daily HTML discovery 설정을 변경하지 않았으므로 향후 운영 설정 조정 필요.','first_seen_policy':'입증된 최초 관측 UTC만 사용; 발령일을 관측일로 가장하지 않음. 내부 last_seen 갱신이 공개 NO_CHANGE hash를 바꾸지 않도록 분리.','future_admin_policy':'전용 미래 버전 API 지원으로 표현 금지. 응답 시행일이 미래라면 마지막 현행과 API 연혁으로 연결하여 current/future 분리; 확인 불가하면 fail-closed.','attachment_array_gap':{'affected_eligible_ids':malformed_attachments,'finding':'현재 normalizer가 API의 첨부파일명/링크 배열을 하나의 문자열·URL로 합치는 사례 발견. 원 공식 배열은 API로 충분히 제공되어 API 자격은 유지되나 공개 링크 표현은 정정 필요. 문서 파싱 없이 배열 원소별 메타데이터 정규화로 해결해야 함. 감사는 production normalizer를 수정하지 않음.'},'metadata_only_event_gap':{'affected_count':sum(not p['same_serial_issue_date_change_has_event'] for p in metadata_probe),'finding':'동일 버전 ID에서 발령일만 정정되면 metadata hash와 dataset identity는 바뀌지만 현재 compare는 독립 이벤트를 만들지 않음. 확장 전 metadata-only 정정 이벤트 정책 보완 필요. 새 일련번호의 정상 개정은 RULE_AMENDED 등으로 감지.'}}
    migration['rule_kind_contract_gap']={'canonical_id':'admrul-2036599','official_rule_type':'지침','existing_12_contract':'REJECTED / FAIL_CLOSED','required_13_change':'공식 API 종류 지침을 허용하는 category 계약 확장. 공식 목록 category와 API rule_type를 혼동하지 않음. 고시·공고·기타는 추후 개별 승인 전 자동 core 포함 금지.','evidence_report':'data/reports/phase1d_evidence/contract_validation_gaps.json'}
    migration['rehearsal_limits']='실제 sync/publish/validation 경로를 격리 디렉터리에서 실행하되 in-memory 1.3 버전·지침 enum 호환 validator를 사용함. 실제 1.2는 확장을 차단. 전체 provenance 필수 필드 적용·승인·클라이언트 전환은 아직 검증/발행하지 않음.'
    all_unchanged=read(OUT/'production_before.json')==fingerprint()
    report={'phase':'PHASE 1D API-ONLY ELIGIBILITY & LINEAGE AUDIT','core_principle':'API-ONLY PRODUCTION TRACKING','current_68':current,'current_68_api_eligible':sum(r['production_eligible'] for r in records if r['group']=='CURRENT_68'),'current_68_ineligible':[r for r in records if r['group']=='CURRENT_68' and not r['production_eligible']],'new_39':new,'optional_31':counts(records,'OTHER_DISCOVERY'),'records':records,'new_trackable_direct':[r['canonical_id'] for r in added if r['scope_class']=='DIRECT_CORRECTIONS'],'new_trackable_cross_domain':[r['canonical_id'] for r in added if r['scope_class']=='CROSS_DOMAIN_CORRECTIONS'],'lineage':lin,'final_recommended_production_core_count':len(eligible),'active_current_count':sum(r['current_status']=='CURRENT' for r in eligible),'historical_repealed_count':sum(r['current_status']=='REPEALED' for r in eligible),'final_recommended_additions':[{k:r[k] for k in ('canonical_id','candidate_name','scope_class','eligibility_result','production_eligible')} for r in added],'discovery_only_count':len(discovery_only),'discovery_only':discovery_only,'unresolved_title_discovery_extra':lin['national_personnel_guideline'],'performance':performance,'fail_closed_expanded':'PASS' if dry and dry['last_good_preserved'] else 'FAIL','no_change_expanded':'PASS' if dry and dry['public_bytes_and_mtimes_preserved'] else 'FAIL','isolated_rehearsal':dry,'audit_verification':verification,'metadata_only_change_probe':metadata_probe,'schema13_migration':migration,'live_integrity':integrity,'production_modified':not all_unchanged,'frontend_modified_by_audit':False,'deployed':False,'secret_leak':0 if verification and verification['result']=='PASS' else 'UNVERIFIED','go_no_go':'GO_API_ELIGIBILITY / NO_GO_IMMEDIATE_PRODUCTION_EXPANSION','reason':'API-only 자격을 통과한 추가 후보만 권고. 사람 승인·업무분야 검토·1.3 전환·첨부 메타데이터 배열/metadata-only 정정 이벤트 보완 전 실제 운영 확장·발행은 보류. 첨부형 본문 규정은 예외 없이 제외.'}
    write_json('data/reports/phase1d_api_eligibility.json',report)
    write_json('data/reports/phase1d_schema13_provenance_candidate.json',schema13())
    lines=['# PHASE 1D API-ONLY ELIGIBILITY & LINEAGE AUDIT','','CORE PRINCIPLE: API-ONLY PRODUCTION TRACKING','',f"기존 68: {current}",f"추가 39: {new}",f"선택 감사 나머지 31: {report['optional_31']}",'',f"권고 추적 core {len(eligible)}개 = 기존 API 자격 통과 {report['current_68_api_eligible']} + 추가 {len(added)}. 현행 {report['active_current_count']}, 폐지 이력 {report['historical_repealed_count']}. 폐지 2개는 살아 있는 규정으로 표시하지 않음.",'',f"추가 직접 {len(report['new_trackable_direct'])}, 공통 {len(report['new_trackable_cross_domain'])}. 발견만 유지 {len(discovery_only)}개(별도 정확 명칭 미확인 인사 지침 1건은 안정 ID가 없어 수에 합산하지 않음).",'','## 전수 API 증거','','| 그룹 | 안정 ID | 현재 명칭 | 범위 | API class | 상태/시행일 | 정형 본문 | 반복 일치 | 결정·실패 사유 |','|---|---|---|---|---|---|---|---|---|']
    for r in records:
        lines.append(f"| {r['group']} | {r['canonical_id']} | {r['candidate_name']} | {r['scope_class']} | {r['eligibility_result']} | {r.get('current_status')} / {r.get('effective_date')} | {r.get('body_available',False)} | {r.get('repeat_deterministic',False)} | {r['production_decision']}: {r.get('failure_reason') or ''} |")
    lines += ['', '각 API endpoint·target·식별자·HTTP status·실제 JSON/XML 형식·현재 metadata·snapshot·정규화 hash·반복 증거·연혁·별표 및 첨부 상태는 JSON records에 보존했습니다. 인증값은 보존하지 않습니다.','', '## 권고 추가 목록','']
    lines += [f"- {r['canonical_id']} — {r['candidate_name']} ({r['scope_class']}) [공식 원문]({r['snapshot']['official_source_url']})" for r in added]
    lines += ['', '## 추가 금지·발견만 보존','']
    lines += [f"- {r['canonical_id']} — {r['candidate_name']}: {r['discovery_status']} / {r['eligibility_result']}; {r.get('failure_reason') or '범위 승인 미완료 또는 이번 추가 39개 밖의 후보'}" for r in discovery_only]
    lines += ['', '국가공무원 복무·징계 관련 예규는 관련성 KEEP이지만 API_TRACKABLE_LIMITED입니다. 조문내용이 빈 값이고 operative 본문은 공식 HWPX/PDF 첨부만 제공합니다. 제개정이유와 metadata를 본문으로 대체하지 않습니다. PDF/HWPX 파싱 없이 core에서 제외합니다.','', '## 미래 시행·변경 탐지','', '법령은 eflaw 안정 LID, nw=2,3 목록에서 현행·시행예정을 구분하여 실제 future body도 조회했습니다. 행정규칙은 시행일 metadata 비교를 지원하지만 전용 미래 버전 목록 지원은 주장하지 않습니다. 정형 본문과 별표·첨부 metadata hash를 비교하며 첨부 의미는 분석하지 않습니다.','', '## 확장 리허설·성능','',f"격리 디렉터리 실제 publish/sync 검증: {dry}",f"검증 결과: {verification}",f"fail-closed: {report['fail_closed_expanded']}; NO_CHANGE: {report['no_change_expanded']}",f"예상 API {expected_calls}회/실행, {performance['expected_runtime_seconds']}초/실행, 하루 {expected_calls*2}회. 기존 실측에서의 추정이며 API quota 승인·장기 SLA의 증명은 아닙니다.",'', '## 미발행 1.3 계약 및 전환 영향','',json.dumps(migration,ensure_ascii=False,indent=2),'', '## 최종 판단','',report['go_no_go'],report['reason'],f"운영 registry·public API·스냅샷·schemas·frontend·배포설정 내용/수정시각 보존: {'PASS' if all_unchanged else 'FAIL'}."]
    Path('data/reports/phase1d_api_eligibility.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    ll=['# PHASE 1D LINEAGE AUDIT','','공식 구조화 API 현행·연혁·상세 본문으로만 조사했습니다. 유사 제목만으로 stable ID를 합치지 않습니다.','']
    for index,r in enumerate(lin['repealed_two'],1):
        old=r['old']; active=old['last_operative_version']; ll += [f"## 폐지 {index}: {old['title']}",'',f"Old tracked terminal: {old['canonical_id']} / {old['rule_type']} {old['issue_number']}호 / 폐지 시행 {old['effective_date']}",f"Last operative version: {active['발령번호']}호 / 시행 {active['시행일자']} / 버전 {active['행정규칙일련번호']}" if active else 'Last operative version: 확인 필요',f"Status: {old['status']}",old['reason_production_marked_repealed'],f"Successor candidate: {r['successor']}",f"Relationship: {r['relationship']}",r['finding'],f"[공식 폐지 버전]({old['official_url']})",'']
    ll += ['## 국가공무원 복무·징계 관련 예규','',lin['national_duty_discipline']['finding'],f"Canonical ID: admrul-30248; 현행 {lin['national_duty_discipline']['current_api_metadata'].get('시행일자')}; API class: {lin['national_duty_discipline']['eligibility_result']}; 안정 ID 연혁 일치: {lin['national_duty_discipline']['stable_history_identity_verified']}",'', '## 국가공무원 인사운영처리지침','',lin['national_personnel_guideline']['finding'],lin['national_personnel_guideline']['recommended_action'],'', '기능 대체 관계는 canonical ID 병합이나 법적 동일 규정 판정을 뜻하지 않습니다. NO_SUCCESSOR는 공식 폐지이유·연혁·조회 범위 내 결과입니다. 모든 검색·상세 증거는 eligibility JSON의 lineage와 phase1d_evidence에 있습니다.']
    Path('data/reports/phase1d_lineage_audit.md').write_text('\n'.join(ll)+'\n',encoding='utf-8')
    if not all_unchanged: raise ValueError('PRODUCTION_MODIFIED')
    print(json.dumps({'current':current,'new':new,'proposed_core':len(eligible),'new_additions':len(added),'discovery_only':len(discovery_only),'production_unchanged':all_unchanged}))

if __name__=='__main__': main()

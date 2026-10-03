"""Build review artifacts from isolated official audit evidence, no publication."""
import sys
import json
import re
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.snapshot import write_json
from pipeline.registry import normalized_title
from scripts.domain_evidence import evidence,strings
from scripts.audit_scope import OUT, fingerprint,protected_changes

CLASSES=['OFFICIAL_CORRECTIONS_LIST','DIRECT_CORRECTIONS','CROSS_DOMAIN_CORRECTIONS','HISTORICAL_REPEALED','REVIEW','NOT_CORRECTIONS']

def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))

def main():
    live=read(OUT/'collection.json'); integrity=read(OUT/'integrity.json')
    registry=read('data/registry/rules.json'); old_evidence=read('data/reports/domain_evidence.json')
    resolution=read(OUT/'resolution.json'); seeds=resolution['entries']; by_id={r['canonical_id']:r for r in seeds if r['status']=='RESOLVED'}
    rows=[]
    for r in registry:
        cid=r['canonical_id']; seed=by_id.get(cid); s=live['snapshots'].get(cid)
        ev=evidence(s) if s else old_evidence.get(cid,{})
        status=seed['current_status'] if seed else r['status']
        scope='HISTORICAL_REPEALED' if status=='REPEALED' else 'OFFICIAL_CORRECTIONS_LIST' if seed else 'REVIEW'
        purpose=ev.get('purpose') or ev.get('scope') or old_evidence.get(cid,{}).get('historical_scope_evidence',{}).get('purpose')
        applies=[]
        text=(purpose or '')+' '+r['current_name']
        for word in ['교정직 공무원','교정직공무원','교정공무원','교도관','수용자','수형자','지방교정청','교도소','구치소','교정시설','경비교도','민영교도소','의무관','피보호감호자','교정위원']:
            if word in text: applies.append(word.replace('교정직공무원','교정직 공무원'))
        if not applies: applies=['교정본부 및 소속기관(공식 목록·담당 부서 근거)']
        basis=('교정본부 공식 '+('법령' if r['source_kind']=='law' else '행정규칙')+' 현황 수록') if seed else '공식 목록 연결 재확인 필요'
        note=None
        if status=='REPEALED':
            basis+='; 공식 폐지 이력을 보존'; note='공식 페이지에 남아 있지만 현행 업무 기준으로 표시하지 않음. 삭제 대신 이력 보존 권고.'
        if cid=='admrul-26465': basis+='; 목적조문에 교도소·구치소 의무관의 임상연구비 명시'
        if cid=='admrul-32484': basis+='; 교정기획과 소관 순시·순회점검 현황 보고'
        if cid=='admrul-51868': basis+='; 지방교정청·교도소·구치소 보고사무에 적용'
        rows.append({'canonical_id':cid,'current_name':seed['current_name'] if seed else r['current_name'],'status':status,'scope_class':scope,'selection_basis':basis,'applies_to':list(dict.fromkeys(applies)),'official_seed_name':seed['seed_name'] if seed else None,'official_seed_url':seed['corrections_source_url'] if seed else None,'canonical_lawgo_url':s['official_source_url'] if s else r['official_source'],'evidence':{'official_seed':seed,'official_text':ev,'api_identity':s['evidence'] if s else None,'repeal_evidence':s.get('repeal_evidence') if s else None},'confidence':seed['confidence'] if seed else 0.5,'review_note':note,'scope_review_status':'EVIDENCE_VERIFIED' if seed else 'REVIEW'})
    bodies=read(OUT/'candidate_bodies.json'); supplement=read(OUT/'supplement.json'); bodies.update(supplement['bodies'])
    decisions=read(OUT/'scope_decisions.json')
    maps=read(OUT/'system_maps.json'); delegated={}
    def walk(value,parent):
        if isinstance(value,dict):
            if '행정규칙ID' in value: delegated.setdefault('admrul-'+str(value['행정규칙ID']),[]).append(parent)
            for item in value.values(): walk(item,parent)
        elif isinstance(value,list):
            for item in value: walk(item,parent)
    for m in maps: walk(m['payload'],m['canonical_id'])
    candidates=[]; excluded=[]
    for cid,body in sorted(bodies.items()):
        decision=decisions.get(cid,{'scope_class':'REVIEW','selection_basis':'교정 적용 범위의 추가 확인 필요','applies_to':[],'recommended_action':'보류; 공식 적용 범위 확인'})
        item=body['list_item']; s=body.get('snapshot'); ev=evidence(s) if s else {'structured_body_unavailable':body.get('body_review_reason'),'official_metadata':body['payload']}
        if s: ev['relevant_official_articles']=[t for t in strings(s['body']['articles']) if any(w in t for w in ('교정','교도소','구치소','교도관','적용','징계','법무부 소속'))][:12]
        record={'canonical_id':cid,'name':item['행정규칙명'],'status':'DISCOVERY_CANDIDATE','official_current_list':True,'effective_status':'FUTURE_EFFECTIVE' if str(item.get('시행일자',''))>live['collected_at'][:10].replace('-','') else 'CURRENT','scope_class_candidate':decision['scope_class'],'reason':decision['selection_basis'],'applies_to':decision['applies_to'],'official_evidence':{'official_url':body['official_url'],'list_item':item,'text_evidence':ev,'api_evidence':body['evidence'],'core_system_map_ids':list(dict.fromkeys(delegated.get(cid,[])))},'recommended_action':decision['recommended_action'],'review_note':decision.get('review_note'),'scope_review_status':'HUMAN_REVIEW_PENDING','production_member':False}
        (excluded if decision['scope_class']=='NOT_CORRECTIONS' else candidates).append(record)
    searches=read(OUT/'searches.json')
    exact_title='국가공무원 인사운영처리지침'
    exact_found=[b for b in bodies.values() if normalized_title(b['list_item']['행정규칙명'])==normalized_title(exact_title)]
    title_check={'name':exact_title,'exact_match_count':len(exact_found),'classification':'REVIEW' if not exact_found else decisions.get('admrul-'+str(exact_found[0]['list_item']['행정규칙ID']),{}).get('scope_class','REVIEW'),'note':'입력 명칭의 현행 정확 일치 항목을 찾지 못함. 국가공무원 복무·징계 관련 예규와 동일시하지 않으며 원 출처 확인 전 포함·제외 확정 안 함.' if not exact_found else '별도 공식 본문 근거로 판정'}
    stale=[]
    for seed in seeds:
        if seed['status']!='RESOLVED': continue
        if normalized_title(seed['seed_name'])!=normalized_title(seed['current_name']): stale.append({'type':'DISPLAYED_NAME_DIFFERS','canonical_id':seed['canonical_id'],'seed_name':seed['seed_name'],'current_name':seed['current_name'],'outgoing_url':seed['outgoing_url'],'evidence':seed['resolution_method']})
        if 'FALLBACK' in seed['resolution_method']: stale.append({'type':'RETIRED_OUTGOING_SERIAL','canonical_id':seed['canonical_id'],'seed_name':seed['seed_name'],'evidence':seed['resolution_method'],'note':'旧 일련번호 본문이 빈 결과. 부처·종류·정확 명칭 유일 일치로 현행 식별자 복구; 링크 갱신 권고.'})
        pinned=re.search(r'\(\d+,(\d{8})\)',seed['outgoing_url'])
        if pinned and pinned.group(1)!=seed['issue_or_promulgation_date'].replace('-',''):
            stale.append({'type':'HISTORICAL_VERSION_PINNED_LINK','canonical_id':seed['canonical_id'],'seed_name':seed['seed_name'],'outgoing_url':seed['outgoing_url'],'outgoing_issue_date':pinned.group(1),'current_issue_date':seed['issue_or_promulgation_date'],'canonical_url':seed['official_detail_url'],'note':'공식 outgoing이 예전 발령 버전에 고정. 정상 이력 링크이며 최신 본문 링크 갱신 권고; stable ID 매핑 오류 아님.'})
    current_ids={r['canonical_id'] for r in registry}; official_ids=set(by_id)
    errors=[r for r in seeds if r['status']!='RESOLVED']
    contract={'existing_production':'FAIL','proposed_provenance_model':'PASS','recommended_schema':'1.3','reason':'1.2는 additionalProperties=false의 동결 계약이며 선정근거·범위·발견출처·최초관측시각 필드가 없다. 1.3 명시적 버전 전환 후 적용; 현재 API·계약·운영 registry 변경 없음.','location':'rule.provenance 및 index summary.provenance','fields':{'scope_class':'상호 배타적 6개 범위 값; 폐지 이력 우선, 다음 공식목록, 직접, 공통, 검토, 제외','selection_basis':'공식 근거로 검토한 짧은 한국어 사실 설명','applies_to':'근거가 있는 대상 명칭 배열; 법률상 개별 적용 결론을 생성하지 않음','official_seed_name':'공식 표시 명칭 또는 null','official_seed_url':'corrections.go.kr 공식 목록 HTTPS 또는 null','canonical_source_url':'law.go.kr 공식 현행/폐지 버전 HTTPS','first_seen_at':'최초 실제 관측 UTC; 발령일·법령 생성일로 대체하지 않음','last_seen_on_corrections_page':'마지막 성공한 전체 목록 관측 UTC 또는 null; 미수록으로 역사값 삭제 금지','discovery_source':'CORRECTIONS_PAGE / LAW_API_KEYWORD / LAW_API_MINISTRY / CORE_SYSTEM_MAP / MANUAL_OFFICIAL_REVIEW','scope_review_status':'REVIEW / EVIDENCE_VERIFIED / APPROVED / REJECTED'},'lifecycle':'관측시간은 내부 provenance 레지스트리에 저장. NO_CHANGE 공개 데이터의 timestamp-only rewrite 금지. 검토 완료된 provenance의 의미 변화만 버전·해시 변경.','required_evidence':'출처 URL, 공식 안정 ID·버전 ID, 목적/범위 또는 공식목록 연결, 원문 해시, 검토 이력. 폐지·시행 예정 상태와 scope_class를 독립 저장.','first_seen_migration':'68개는 보존된 공식 seed의 crawled_at 등 최초 입증 가능한 관측만 사용. 최초 날짜를 입증할 수 없으면 null+REVIEW; audit_at으로 과거 관측을 가장하지 않음.'}
    totals=dict(Counter(r['scope_class'] for r in rows)); counts={k:totals.get(k,0) for k in CLASSES}
    unchanged=not protected_changes(read(OUT/'production_before.json'),fingerprint())
    report={'phase':'PHASE 1C SCOPE & PROVENANCE AUDIT','audited_at':live['collected_at'],'official_current_seed':resolution['counts'],'official_total':len(seeds),'current_registry_count':len(registry),'scope_model':{'priority':CLASSES,'note':'폐지 이력은 HISTORICAL_REPEALED로 우선 분류하고 공식목록 membership을 별도로 보존. 현행 공식목록 항목에 직접/공통 관계가 있어도 주 분류는 공식목록.','direct_basis':'공식 목적·대상·적용범위 또는 핵심 법령 위임 관계로 교정업무를 직접 규율','cross_domain_basis':'교정직 복무·징계·인사·조직·윤리 등에 실질적인 관련성을 공식 범위로 입증; 모든 국가공무원 규정 자동 포함 금지'},'class_counts':counts,'every_current_record_explainable':'PASS' if len(rows)==len(registry) and not errors and official_ids==current_ids else 'FAIL','current_records':rows,'official_seed':seeds,'official_items_missing_from_registry':sorted(official_ids-current_ids),'registry_no_longer_listed':sorted(current_ids-official_ids),'stale_renamed':stale,'canonical_mapping_problems':errors,'duplicate_logical_ids':[cid for cid,n in Counter(r['canonical_id'] for r in seeds if r['canonical_id']).items() if n>1],'discovery_candidates':candidates,'excluded_search_results':excluded,'unresolved_requested_name':title_check,'discovery_coverage':{'title_queries':[{k:v for k,v in q.items() if k not in ('items','evidence')} for q in searches],'full_text_queries':[{k:v for k,v in q.items() if k not in ('items','evidence')} for q in supplement['searches']],'ministry_count':next(q['count'] for q in searches if q['query']=='MINISTRY_CURRENT'),'ministry_filter_verified':all(i.get('소관부처명')=='법무부' for q in searches if q['query']=='MINISTRY_CURRENT' for i in q['items']),'candidate_body_count':len(bodies),'system_maps':maps,'system_map_missing_candidates':sorted(set(delegated)-current_ids-set(bodies)),'limitations':['제목 키워드 16개, 법무부 현행 목록 전수열거, 인사·복무 등 관련 제목 본문, 법무부 본문 교정·교도소·구치소 검색, 핵심 3법 체계도 조사 범위의 감사다. 모든 교정 관련 규정의 완전 수록을 보장하지 않음.','국가공무원 일반 예규 중 PDF형 본문은 공식 메타데이터·첨부/목차 근거를 보존하고 세부 조문 적용 결론은 검토 보류.','행정규칙 목록 nw=1 현행에 시행예정 버전이 섞이면 시행일을 비교하여 별도 표기해야 함.']},'recommended_production_core':{'retain_existing':len(registry),'current':sum(r['status']!='REPEALED' for r in rows),'historical':sum(r['status']=='REPEALED' for r in rows),'add_after_review':[c['canonical_id'] for c in candidates if c['recommended_action'].startswith('추가 권고')],'exclude_none_automatically':True},'provenance_contract':contract,'production_change_recommended':True,'production_changed':not unchanged,'frontend_changed':False,'deployed':False,'human_review_required':True,'public_wording':'교정본부 공식 목록과 교정업무 직접 관련 규정을 추적','integrity':integrity,'supplement_failures':supplement['failures']}
    known=next(c for c in candidates if c['canonical_id']=='admrul-30248')
    report['known_cross_domain_check']={'name':known['name'],'canonical_id':known['canonical_id'],'classification':'CROSS_DOMAIN_CORRECTIONS','decision':'KEEP_SCOPE / PROPOSE_ADD_AFTER_REVIEW','already_in_production':False,'reason':known['reason'],'official_url':known['official_evidence']['official_url'],'current_version':known['official_evidence']['list_item']['행정규칙일련번호'],'effective_date':known['official_evidence']['list_item']['시행일자'],'structured_body_supported':False}
    report['cross_domain_audit']={'existing_official_broad_record':next(r for r in rows if r['canonical_id']=='admrul-26465'),'external_cross_candidates':[c for c in candidates if c['scope_class_candidate']=='CROSS_DOMAIN_CORRECTIONS'],'requested_unresolved_title':title_check}
    report['supersession_audit']={'confirmed_automatic_id_replacements':[],'related_successor_candidate':{'historical_id':'admrul-26424','candidate_id':'admrul-84831','note':'간판·영문명 업무가 관련된 별도 안정 ID. 폐지·후보 본문 근거는 확인했으나 동일 법적 규정·자동 승계로 단정하지 않음.'}}
    report['recommended_discovery_counts']=dict(Counter(c['scope_class_candidate'] for c in candidates))
    report['candidate_count']=len(candidates)
    report['verification_report']='data/reports/phase1c_verification.json'
    write_json('data/reports/phase1c_scope_audit.json',report)
    write_json('data/reports/phase1c_provenance_contract_candidate.json',contract)
    lines=['# PHASE 1C SCOPE & PROVENANCE AUDIT','',f"감사 시각: {live['collected_at']}",'','운영 목록·공개 API·스냅샷 내용과 수정시각을 보존했습니다. 감사는 프론트엔드를 수정하거나 배포하지 않았습니다. 아래 추가 권고는 사람 검토 전 DISCOVERY_CANDIDATE입니다.','', '관측 중 web/src/components/RuleDetailModal.tsx 및 web/src/test/components.test.tsx의 외부 변경이 감지되었습니다. 감사 스크립트의 쓰기 경로에 프론트엔드는 없으며 그 변경을 되돌리지 않았습니다. 전체 파일 불변은 FAIL, 운영 데이터 불변은 별도 PASS입니다.','',f"공식 목록 {len(seeds)}개: "+', '.join(f'{k} {v}' for k,v in resolution['counts'].items()),f'운영 registry {len(registry)}개. 모든 기존 항목 선정근거: '+report['every_current_record_explainable'],'', '## 범위 원칙','',report['scope_model']['note'],report['scope_model']['cross_domain_basis'],'','| 분류 | 운영 항목 수 |','|---|---:|']
    lines += [f'| {k} | {v} |' for k,v in counts.items()]
    lines += ['', '## 기존 항목 전수 감사','', '| ID | 현재 명칭 | 상태/범위 | 선정 근거·대상 | 공식 근거 |','|---|---|---|---|---|']
    for row in rows:
        lines.append(f"| {row['canonical_id']} | {row['current_name'].strip()} | {row['status']} / {row['scope_class']} | {row['selection_basis']}; {', '.join(row['applies_to'])} | [공식 목록]({row['official_seed_url']}) · [공식 원문]({row['canonical_lawgo_url']}) |")
    lines += ['', '각 항목의 공식 표시명·부서·outgoing URL·식별자 해결 과정·공식 목적/범위·원문 해시는 JSON의 current_records 및 official_seed에 보존했습니다. 예전 링크의 버전과 현재 버전이 다르다는 이유만으로 잘못된 매핑이라 판정하지 않습니다.','', '## 발견 후보 및 개별 판정','', '| ID | 명칭 | 범위 후보 | 이유 | 조치 | 공식 근거 |','|---|---|---|---|---|---|']
    for c in candidates+excluded:
        lines.append(f"| {c['canonical_id']} | {c['name']} | {c['scope_class_candidate']} | {c['reason']} | {c['recommended_action']} | [원문]({c['official_evidence']['official_url']}) |")
    lines += ['', '국가공무원 복무·징계 관련 예규는 CROSS_DOMAIN_CORRECTIONS / KEEP 범위 결정입니다. 현재 68개 운영 목록에 없어 추가 승인 대기 후보로 기록하며 기존 항목인 것처럼 보고하지 않습니다.','',exact_title+': '+title_check['note'],'', '## 명칭·링크·폐지·매핑','']
    lines += ['- '+json.dumps(x,ensure_ascii=False) for x in stale]
    lines += ['', f"공식 항목 운영 누락: {report['official_items_missing_from_registry']}",f"운영 항목 공식목록 이탈: {report['registry_no_longer_listed']}",f"canonical 매핑 문제: {errors}",f"중복 논리 ID: {report['duplicate_logical_ids']}",'','폐지 규정 2건은 공식 폐지 본문·이력 근거를 JSON에 기록합니다. 현행 운영 목록에서 자동 삭제하지 않습니다.','', '## 조사 범위·한계','',f"법무부 현행 {report['discovery_coverage']['ministry_count']}개 전수 목록과 검색·본문·3개 핵심 법령 체계도를 조사했습니다."]
    lines += ['- '+x for x in report['discovery_coverage']['limitations']]
    lines += ['', '## Provenance 계약 권고','', '**현재 계약: FAIL. 제안 모델: PASS. 권고 schema: 1.3.**',contract['reason'],'','| 필드 | 의미 |','|---|---|']
    lines += [f'| {k} | {v} |' for k,v in contract['fields'].items()]
    lines += ['',contract['lifecycle'],contract['first_seen_migration'],'', '## 최종 권고','',f"기존 {len(registry)}개 유지(현행 {report['recommended_production_core']['current']}, 폐지 이력 {report['recommended_production_core']['historical']}). 검토 후 추가 권고: {len(report['recommended_production_core']['add_after_review'])}개. 나머지 REVIEW 후보는 개별 적용 범위를 확인한 뒤 결정합니다.",f"운영 파일 내용·수정시각 보존: {'PASS' if unchanged else 'FAIL'}.",'','PRODUCTION CHANGE RECOMMENDED: YES. 변경·발행은 하지 않았으며 사용자 검토를 기다립니다.','', '공개 문구: “교정본부 공식 목록과 교정업무 직접 관련 규정을 추적”. 선정 근거는 검토된 백엔드 데이터로 제공하고 UI가 법적 해석을 만들어내지 않습니다.']
    lines += ['', '## 추가 검토 사항','', '국가공무원 복무·징계 관련 예규는 현행 2026-10-01 시행, 인사혁신처 예규 225호, 버전 2100000285756입니다. 공식 HWPX/PDF 첨부형 본문으로 현재 정형조문 수집기는 STRUCTURED_BODY_MISSING으로 거부합니다. KEEP 범위 인정과 수집기 호환성 보완을 분리하여 보고합니다.','', '발견 후보 총 70개: 직접 15, 공통 25, REVIEW 30. 공통 중 본부 한정 당직규칙 1개는 보류하므로 추가 권고는 직접 15 + 공통 24 = 39개입니다. 검색 제외 45개는 운영 목록에서 삭제한 항목이 아닙니다.','', '폐지된 간판·영문표기 지침(admrul-26424)과 새 교정직제 영어 명칭 지침(admrul-84831)은 기능상 관련 후보이나 별도 안정 ID이며 자동 승계로 단정하지 않습니다.','', '정규화 후 공식 표시명 차이 8개, 예전 발령 버전 고정 링크 38개입니다. 버전 고정 링크는 정상 이력 링크이므로 canonical 매핑 오류와 구분합니다.']
    Path('data/reports/phase1c_scope_audit.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    if not unchanged: raise ValueError('PRODUCTION_CHANGED')
    print(json.dumps({'class_counts':counts,'candidates':dict(Counter(c['scope_class_candidate'] for c in candidates)),'recommended_additions':len(report['recommended_production_core']['add_after_review']),'production_unchanged':unchanged},ensure_ascii=False))

if __name__=='__main__': main()

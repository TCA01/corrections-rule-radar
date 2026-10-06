"""Render the independently collected audit; no API calls or publication."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'data/reports/phase1k_comparison_audit.json').read_text(encoding='utf8'))
lines=['# 형사소송법 시행상태 / 공포단위 비교 감사','',
       '공식 구조화 API를 새로 조회한 독립 비교와 기존 운영 비교기가 일치했다. 생산 법령 비교 로직은 변경하지 않았다.',
       '','| 상태 | 시행일 | MST | 본문 조문 수 | 공식 원문 |','|---|---|---|---|---|']
for label,s in zip('ABCD',r['states']):
    d=s['metadata']['effective_date']; m=s['version_id']
    lines.append(f'| {label} | {d} | {m} | {s["article_count"]} | [원문](https://www.law.go.kr/LSW/lsInfoP.do?efYd={d.replace("-", "")}&lsiSeq={m}) |')
lines+=['','| 전환 | 직전 상태 대비 | 현재 대비 누적 | 변경 조문 |','|---|---|---|---|']
for t in r['transitions']:
    lines.append(f'| {t["before_date"]} → {t["after_date"]} | {len(t["independent_changes"])} | {len(t["cumulative"])} | '+', '.join(a['article_number'] for a in t['independent_changes'])+' |')
lines+=['','## A → B 전체 조문 비교','',
        '617개 조문 키 전체를 대조했다. 제목과 구조화 항·호·목 본문을 정규화하여 비교했으며, 변경 플래그나 표의 생략 표시를 법령 본문으로 사용하지 않았다.',
        '해시는 조문 키·제목·전체 텍스트의 정렬된 UTF-8 JSON에 대한 SHA-256이다.',
        '','| 조문 키 | 종류 | Before SHA-256 | After SHA-256 |','|---|---|---|---|']
for a in r['transitions'][0]['independent_changes']:
    lines.append(f'| {a["article_key"]} | {a["reason"]} | {a["before_hash"]} | {a["after_hash"]} |')
lines+=['','## 공식 공포단위 비교: 본문 97개 조문','',
        '공식 웹 화면의 “신구법 비교는 공포단위 서비스입니다” 안내를 직접 확인했다. 화면은 이전 법률 제21241호(MST 281865)와 법률 제21857호(MST 288579)를 비교한다. API oldAndNew의 기본정보도 같은 쌍이다. 두 공포단위 전체 구조화 본문을 별도로 조회하여 비교한 97개 조문과 공식 비교표의 조문 번호 집합이 완전히 일치했다.',
        '','집계 단위는 형사소송법 본문 조문 번호이며, 부칙에서 개정하는 다른 법률의 조문은 포함하지 않는다.',
        '','| 공식 비교표 조문 | 시행 전환 분류 |','|---|---|']
labels={'ALREADY_BY_2026-10-02':'2026-10-02까지 반영','2027-02-05':'2027-02-05 새 변경','2027-08-05':'2027-08-05 새 변경','LATER_OR_OTHER_STAGED_DATE':'기관별 단계 시행 (본문 변화와 별개)'}
for row in r['promulgation']['articles']: lines.append(f'| {row["article_number"]} | {labels[row["transition"]]} |')
lines+=['','91개는 A에서 이미 이전 공포단위와 달라져 있다. 제245조의12 제6항은 이후 제22009호의 추가 정정까지 반영된 상태이므로 현재 기준은 반드시 290189를 사용한다.',
        '','제199조의2는 네 API 본문에 이미 같은 텍스트로 들어 있지만, 부칙은 기관에 따라 공포 후 1년 / 3년 이내 대통령령 지정일로 구분한다. 본문 변경 수는 이러한 기관별 법적 적용시점을 모두 뜻하지 않는다. 이를 임의로 8월 변경 수에 더하지 않았다.',
        '','2월 3개는 제197조의4·제260조·제261조, 8월 2개는 제220조의2·제244조의6이다. 12월 제59조의3은 별도 법률 제21241호의 시행 전환이다.',
        '','동일 MST 288579의 2월/8월 상태는 efYd와 원문 해시가 다르다. B는 617개 조문, C는 619개 조문이며 두 신설 조문의 존재가 다르다. MST 하나로 상태를 합치지 않는다.',
        '','재현 자료: `tests/fixtures/phase1k/`, 기존 불변 공개 버전 아카이브, `phase1k_comparison_audit.json`의 요청 파라미터·응답 해시·97개 비교표 행·각 변경 해시.',
        '','## 공식 구조화 부칙의 시행일 근거','',r['promulgation']['commencement_clause'],
        '','## 동기화 중 새로 확인된 실제 변경','',
        '2026-10-06 확인에서 admrul-29857, admrul-35611의 공식 새 버전을 발견했다. 첫 실행은 PUBLISHED이며 실제 지속 이력 2개가 추가됐다. 이어진 실행은 NO_CHANGE: 법령 바이트·수정시각·스냅샷 집합·상태·이력이 모두 보존됐고 운영 확인 파일만 갱신됐다. 마지막 법령 데이터 갱신은 이제 2026-10-06 18:59 KST다.']
(ROOT/'data/reports/phase1k_comparison_audit.md').write_text('\n'.join(lines)+'\n',encoding='utf8')

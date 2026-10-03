# PHASE 1D LINEAGE AUDIT

공식 구조화 API 현행·연혁·상세 본문으로만 조사했습니다. 유사 제목만으로 stable ID를 합치지 않습니다.

## 폐지 1: 교정기관 간판게시 및 교정직제 영문표기에 관한 지침

Old tracked terminal: admrul-26424 / 예규 1256호 / 폐지 시행 2020-06-08
Last operative version: 869호 / 시행 20090821 / 버전 2000000008540
Status: REPEALED
안정 ID 현행 LID 응답 없음 + 동일 ID 연혁 최신 항목의 폐지 표시 + 폐지 일련번호 상세 본문의 폐지·시행일 확인. 빈 응답만으로 폐지 추정하지 않음.
Successor candidate: {'canonical_id': 'admrul-49753', 'current_title': '정부조직 약칭과 영어 명칭에 관한 규칙', 'issue_number': '390', 'effective_date': '20261002', 'status': 'CURRENT', 'official_url': 'https://www.law.go.kr/LSW/admRulLsInfoP.do?admRulSeq=2100000285900', 'confirmed_successor': True, 'relationship_scope': '폐지이유가 명시한 공통 영어명칭 기준의 기능 대체; 동일 법적 안정 ID 아님'}
Relationship: SUPERSEDED_BY
폐지이유는 정부조직 영어명칭 규칙(행안부 예규 40호)의 존재로 법무부 개별 예규 관리 필요성이 낮아 폐지한다고 명시한다. 해당 공통 규칙의 과거 40호와 현행 390호는 동일 안정 ID 49753이며 현재 명칭은 정부조직 약칭과 영어 명칭에 관한 규칙이다. 따라서 기능상 SUPERSEDED_BY로 연결하되 26424와 49753은 ID를 합치지 않는다. 2023년 별도 제정 84831을 자동 동일계보 후계자로 추정하지 않는다.
[공식 폐지 버전](https://www.law.go.kr/LSW/admRulLsInfoP.do?admRulSeq=2100000189927)

## 폐지 2: 교정공무원 예절 규정

Old tracked terminal: admrul-26917 / 훈령 1494호 / 폐지 시행 2023-10-19
Last operative version: 1372호 / 시행 20210812 / 버전 2100000203696
Status: REPEALED
안정 ID 현행 LID 응답 없음 + 동일 ID 연혁 최신 항목의 폐지 표시 + 폐지 일련번호 상세 본문의 폐지·시행일 확인. 빈 응답만으로 폐지 추정하지 않음.
Successor candidate: None
Relationship: TRULY_REPEALED_NO_SUCCESSOR
공식 폐지이유는 강제적 예절의 악용 우려·경직된 문화·현장 사문화를 이유로 자율성을 위해 규정을 없앤다고 명시한다. 대체·재제정 조항이 없고 조회한 현행 교정공무원 예절·행동 규정에도 후계가 없어 명시적 단순 폐지로 분류한다. NO_SUCCESSOR는 이 규정의 공식 연혁·폐지이유·검색 범위에서 확인된 결과이며 모든 유사 업무 규정의 부존재를 보장하는 표현은 아니다.
[공식 폐지 버전](https://www.law.go.kr/LSW/admRulLsInfoP.do?admRulSeq=2100000230588)

## 국가공무원 복무·징계 관련 예규

구·현행 API 연혁은 동일 안정 ID 30248의 서로 다른 버전이다. 현재 68개에 이 규정의 구·현행 레코드가 없고 실제 폐지 2건과 무관하다. 추적한다면 안정 ID 30248을 사용해야 하지만 현행 operative 본문은 HWPX/PDF 첨부만 제공되고 조문내용이 비어 API-only core 편입 불가. 메타데이터·제개정이유를 전체 본문으로 취급하지 않음.
Canonical ID: admrul-30248; 현행 20261001; API class: API_TRACKABLE_LIMITED; 안정 ID 연혁 일치: True

## 국가공무원 인사운영처리지침

현행·연혁 정확 명칭에 해당 항목을 확인하지 못했고 실제 운영 68개에도 해당 과거 레코드가 없다. 안정 ID가 없으므로 명칭 변경·승계·API 추적 여부 확정 불가. 유사 제목으로 대체하지 않음.
원 공식 명칭 또는 안정 ID 확인 전 DISCOVERY_SCOPE_REVIEW로 보류

기능 대체 관계는 canonical ID 병합이나 법적 동일 규정 판정을 뜻하지 않습니다. NO_SUCCESSOR는 공식 폐지이유·연혁·조회 범위 내 결과입니다. 모든 검색·상세 증거는 eligibility JSON의 lineage와 phase1d_evidence에 있습니다.

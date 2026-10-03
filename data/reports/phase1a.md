# PHASE 1A STABILITY & DOMAIN REVIEW

OBSERVATION RUNS:

| Run | Seconds | API / pages | Success / review / failure | Change | Publication |
|---|---:|---:|---:|---:|---|
| 20261003T024150-dbeb0ae7 | 2.235 | 0 / 1 | 0 / 0 / 68 | 0 | BLOCKED |
| 20261003T024153-17a3bb9d | 2.203 | 0 / 1 | 0 / 0 / 68 | 0 | BLOCKED |
| 20261003T024155-74250a10 | 2.203 | 0 / 1 | 0 / 0 / 68 | 0 | BLOCKED |
| 20261003T024219-a3f03815 | 200.125 | 159 / 70 | 68 / 0 / 0 | 0 | NO_CHANGE |
| 20261003T024540-a503cf90 | 200.547 | 159 / 70 | 68 / 0 / 0 | 0 | NO_CHANGE |
| 20261003T024900-1c3a1b0f | 198.406 | 159 / 70 | 68 / 0 / 0 | 0 | NO_CHANGE |
| 20261003T025601-7cea8b01 | 198.25 | 159 / 70 | 68 / 0 / 0 | 0 | NO_CHANGE |

LIVE FAILURES: 3 restricted-execution page failures; 0 API calls in those attempts. Successful permitted runs: 4; transport/API errors: 0.
NO_CHANGE CONSISTENCY: PASS
HASH STABILITY: PASS
FAIL-CLOSED RECOVERY: PASS
API CALLS PER RUN: [159, 159, 159, 159]; official page calls: [70, 70, 70, 70]
AVERAGE RUN TIME: 199.332 seconds
AVERAGE API RESPONSE TIME: 0.473351 seconds; retries: 0
TWICE DAILY: 318 API requests / 458 total HTTP requests. Measured wall time approximately 398.7 seconds/day; not an official quota guarantee.
CORE RULES: 68
DOMAIN CLASSIFICATION: {'classified': 66, 'multi_domain': 21, 'review': 2}

DOMAIN DISTRIBUTION:

| 관련 업무 분야 | 주 분야 규정 수 | 주·보조 포함 규정 수 |
|---|---:|---:|
| 수용·보안 | 6 | 12 |
| 접견·외부교통 | 0 | 4 |
| 보관금품 | 1 | 5 |
| 분류·가석방 | 7 | 10 |
| 교육·교화 | 3 | 8 |
| 작업·직업훈련 | 7 | 12 |
| 급식·복지 | 12 | 17 |
| 의료 | 2 | 6 |
| 심리치료 | 1 | 2 |
| 인권·청원 | 2 | 6 |
| 민원 | 1 | 1 |
| 인사·조직 | 14 | 19 |
| 정보화 | 1 | 1 |
| 민영교도소 | 4 | 4 |
| 기타 | 5 | 5 |

API V1 CANDIDATE: YES
WEB READY: YES
ANDROID CONTRACT READY: YES
TESTS: 53 / PASS; public schemas: 142 files; secret leaks: 0

The explicit schema 1.0 → 1.1/domain migration published one dataset with zero new legal events. All live observations themselves were NO_CHANGE. Version references and evidence classifications are frozen before client development.

RISKS:

- Same-session observations only; no multi-day soak or official quota guarantee.
- Two broad reporting classifications await business-owner review; reviewed mappings are evidence review, not agency approval.
- Future client compilation, hosting atomic release and separate live operational health remain untested.

NEXT STEP: Review two pending domain mappings and arrange multi-day observation. Frontend implementation requires a subsequent request; no UI or Firebase deployment in Phase 1A.

Details: phase1a.json; summary_preview.md; observation/*.json; observation_recovery.json; docs/api_v1_candidate.md.

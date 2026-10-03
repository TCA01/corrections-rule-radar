# PHASE 1E PERSISTENT CHANGE HISTORY

SCHEMA: 1.3

CURRENT CORE: 68

PERSISTENT CHANGE EVENTS: 79

RECENT 90-DAY EVENTS: 10

EVENTS WITH ARTICLE COMPARISON: 71

EVENTS WITHOUT ARTICLE COMPARISON: 8 (six unavailable; two no article changes)

| Check | Result |
|---|---|
| LAW OLD/NEW | PASS — 17 live events |
| ADMIN OLD/NEW | PASS — 45 live events |
| SNAPSHOT DIFF FALLBACK | PASS — 11 events |
| PAST-EFFECTIVE COMPARISON | PASS — actual official API responses, including 2026-10-01 교도작업운영지침 |
| UPCOMING → CURRENT RETENTION | PASS — transition tests retain identical event and text |
| 90-DAY FILTER | PASS — future, today, yesterday, weeks, day 89/day 90 boundaries |
| HISTORY BEYOND 90 DAYS | PASS — 68 events retained |
| APPENDIX REMOVAL HISTORY | PASS — 24 retained removed metadata entries, plus null-download tests |
| EVENT ID STABILITY | PASS — deterministic IDs and unchanged live history |
| SECOND RUN | NO_CHANGE |
| API CALLS BEFORE | 90 |
| API CALLS AFTER | 90, 90; frozen history has no additional requests |
| RUNTIME | before 99.031s; after 100.829s, 99.829s |
| BACKEND TESTS | 106 PASS |
| PUBLIC JSON VALIDATION | 324 files PASS |
| SECRET LEAK | 0 |
| PRODUCTION CORE EXPANDED | NO |
| READY FOR WEB W3 | YES |

No frontend changes, deployment, HTML scraping or document parsing. Protected archive/frontend/Phase 1D discovery bytes and modification times: PASS.

## Known limitations

- Official old/new comparison excerpts may contain omission markers; comparison_scope discloses this.
- Exact-pair mismatches use structured snapshot fallback; no HTML/document parsing.
- Six earlier historical baselines have no structured predecessor; explicitly COMPARISON_UNAVAILABLE. Recent 90-day events have no unavailable comparisons.
- Initial backfill covers recent 90 days and a preceding historical change per rule, not every amendment since creation.
- Legacy latest/upcoming feeds retain their pre-1.3 event model; Web W3 should consume recent/history and persistent event details.
- No attachment contents or legal interpretation. Future provenance/scope expansion is reserved for schema 1.4.

NEXT STEP: Web W3 consume schema 1.3.

[Contract](../../docs/phase1e_contract.md) · [Structured report](phase1e.json)
[Official administrative old/new API documentation](https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=admrulOldAndNewInfoGuide)

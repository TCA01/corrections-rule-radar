# PHASE 1I MOBILE + DIFF SEMANTICS

Firebase deployed and verified: https://corrections-rule-radar.web.app. Code commit `ad9a7ec`; deployment acknowledgment `47bd239`.

| Check | Result |
|---|---|
| ISSUE 1 ENTITY DISPLAY | PASS |
| ISSUE 2 DELETED APPENDIX OVERLAP | PASS |
| ISSUE 3 DOWNLOAD BUTTON OVERLAP | PASS |
| ISSUE 4 생략 → 현행과 같음 | COMPARISON PLACEHOLDER |
| Literal legal change from 생략 to 현행과 같음 | NO |
| PLACEHOLDER FALSE-DIFF FIXED | PASS |
| ACTUAL SUBSTANTIVE DIFF PRESERVED | PASS |
| 360PX | PASS |
| 390PX | PASS |
| 412PX | PASS |
| Desktop 1280px | PASS |
| BACKEND TESTS | 149 PASS (local and GitHub) |
| FRONTEND TESTS | 90 PASS (local and GitHub) |
| PUBLIC JSON | 538 PASS, 107 rules, schema 1.5 |
| BUILD | PASS |
| Hosting artifact | 541 files PASS, secret leaks 0 |
| GITHUB NORMAL RUN | PASS / NO_CHANGE |
| LIVE VERIFY | PASS; 15 browser cases |
| READY | YES |

STRUCTURED BEFORE: item 4 = 심리치료프로그램 대상자 중 집중인성교육 기본교육 수료 기준시간 이상의 교육을 이수한 자; item 5 = 삭제; paragraph 3 = 기본교육과 형기주기별 재교육.

STRUCTURED AFTER: item 4 = 삭제; item 5 = 삭제; paragraph 3 = 기본교육과 재교육.

Official old-side placeholders: `1. ∼ 3. (생  략)`, `5. ∼ 7. (생  략)`, `② (생  략)`. Official new-side counterparts: `(현행과 같음)`. Exact A/B/C/D texts and raw-cache SHA-256 proof are in `phase1i_audit.md` and `phase1i_audit.json`.

The source adapter uses exact archived before/after references, checks their identity/effective date/body hash, selects official comparison article numbers and supplies full structured text to rendering. Unchanged full articles 26 and 27 are excluded from the visual change set (21), while the official event count (23), excerpts and IDs are preserved. Snapshot failure produces explicit unavailability, not a shorthand diff.

Normal GitHub run: https://github.com/TCA01/corrections-rule-radar/actions/runs/37271367013. Daily discovery was enabled; force_deploy=false and full_audit=false. Sync 322.804197 seconds, 139 API requests + 2 page requests = 141 total HTTP requests. Two recovered NETWORK_ERROR retries; 107 successes, 0 final failures, 0 review, 0 new events. Public content, mtimes, snapshot hashes and event IDs remained identical. Conditional build/commit/deploy steps correctly skipped on NO_CHANGE; the candidate had already passed local build/artifact checks and been deployed/verified manually.

Phase 1H live regression: August 2027 still compares to February 2027 (2 articles); cumulative mode compares to October 2026 (5 articles). Original history and archives remain unchanged.

Evidence: `phase1i_mobile_local.json`, `phase1i_mobile_live.json`, `phase1i_ci_tests.json`, `phase1i_normal_sync.json`, `phase1i_public_stability.json`, `phase1i_github_run.json`. Screenshot artifacts: phase1i-live-deleted-360.jpg, phase1i-live-long-360.jpg, phase1i-live-article14-360.jpg.

No schema migration or data rewrite. Earlier unrelated audit reports remain untracked and were not included in this release.

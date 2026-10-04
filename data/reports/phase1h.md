# PHASE 1H UPCOMING COMPARISON SEMANTICS

DEFAULT UPCOMING MODE: PREVIOUS_EFFECTIVE_STATE — 직전 시행상태 대비
OPTIONAL CUMULATIVE MODE: CURRENT_BASELINE — 현재 기준 누적 비교
FIRST FUTURE BEFORE VERSION: 290189 / 2026-10-02

| Target | After version | Incremental baseline | Incremental count | Cumulative count | Event type |
|---|---|---|---:|---:|---|
| 2027-02-05 | 288579 | 2026-10-02 / 290189 | 3 | 3 | RULE_AMENDED |
| 2027-08-05 | 288579 | 2027-02-05 / 288579 | 2 | 5 | STAGED_EFFECTIVE_DATE |
| 2027-12-31 | 281865 | 2027-08-05 / 288579 | 1 | 6 | RULE_AMENDED |

All cumulative baselines are the current 290189 / 2026-10-02 state.

2027-08-05 ARTICLES: 제220조의2, 제244조의6
SAME MST STAGED EFFECTIVE SUPPORT: PASS
EVENT CLASSIFICATION: STAGED_EFFECTIVE_DATE for the same-MST August transition; genuine corrections retain EFFECTIVE_DATE_CORRECTED.
HISTORY/UI DEFAULT CONSISTENCY: PASS
SCHEMA VERSION: 1.5 (intentional coordinated Web/contract migration)
BACKEND TESTS: 147 PASS locally and on GitHub
FRONTEND TESTS: 75 PASS locally and on GitHub
PUBLIC JSON: 538 PASS
BUILD / ARTIFACT: PASS / 541 files
SECRET LEAK: 0
FIRST RUN: CHANGED (pipeline result PUBLISHED)
SECOND RUN: NO_CHANGE
GITHUB NORMAL RUN: PASS — https://github.com/TCA01/corrections-rule-radar/actions/runs/37173755470
LIVE VERIFY: PASS — https://corrections-rule-radar.web.app
READY: YES

## Operational evidence

First live: 135 API requests, 197.984 seconds, 1 recovered network retry. 107 successes, zero review/failure records.
Second live: 133 API requests, 149.579 seconds, zero retries. Public bytes/mtimes, snapshot hashes and legacy event IDs identical; zero new persistent or legacy events.
GitHub normal core + discovery: 137 API requests plus 2 discovery-page requests, 407.102297 seconds. 107 successes, zero reviews/failures/retries, NO_CHANGE; byte/mtime/hash/ID stability PASS. No build, state commit or redeploy was needed.

Two active future event IDs are explicitly replaced (February baseline and August classification); the mapping is in phase1h_history_migration.json. 150 existing event objects are unchanged: 149 outside the target future chain (including all 148 past events) plus December’s retained future event. Every previously frozen event/version file remains byte-identical; retired event URLs remain available but are excluded from active feeds. Recent 90-day history, 107-rule scope, appendices, aliases, domains and provenance remain intact. Fail-closed recovery and future-to-current persistence regressions pass.

The live manifest, criminal procedure rule detail and full history match the tested local JSON byte-for-byte. Live browser tests verify both modes for all three dates and direct timeline selection of August 5.

Dataset: ds-c21de361c699692df5cd9e366a51f0bbd31ade59516e8ba4185f2577b1e5a286
Code/publication commit: ff50f80; verified deployment acknowledgment: d42dc5b.
GitHub force_deploy=false, full_audit=false. The uploaded artifact report is retained from the validated local release; the GitHub artifact/build/deploy steps were correctly skipped on NO_CHANGE.

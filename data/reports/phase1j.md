PHASE 1J UNATTENDED OPERATION HARDENING

HUNG RUN ROOT CAUSE:
Run 37254965747 was cancelled in core sync after 30m01s. A socket timeout and three request attempts already existed, but no wall deadline bounded DNS plus the full read, and no application sync deadline existed. The old logs cannot identify the exact request or network phase; that wire cause remains unproven. See phase1j_hung_run.json.

REQUEST TIMEOUT: 30 seconds across the complete transport, including open/DNS/connect/TLS/body wait; late results cannot write caches or legal data.
REQUEST RETRIES: Maximum three attempts; 1/2-second backoff for timeout/network/reset, HTTP429/5xx. Deterministic 4xx/authentication/payload errors are not retried.
WHOLE SYNC DEADLINE: 720 seconds shared by both attempts, with up to 60 seconds reserved for validation/promotion. Isolated worker processes are killed on expiry.
GITHUB TIMEOUT: Sync step 15 minutes; job 25 minutes including setup, tests and possible changed-data release.
WHOLE-SYNC RETRY: One fresh transient retry after 5 seconds within the same deadline; no retry for deterministic failure or exhausted budget.

FAIL-CLOSED: PASS
LAST-GOOD: PASS
PARTIAL PUBLISH PREVENTED: PASS
NO_CHANGE IDEMPOTENCY: PASS

VERIFY.PY DIRECT EXIT CODE: 0; final local and CI backend suites both 165 PASS.
VERIFY.PY ISSUE: OTHER. Retained evidence does not conclusively diagnose the earlier piped invocation. Direct execution is clean; no verifier code was altered. A passed test flag alone is not its exit condition: public validation and verified secret scan must also pass.

HEALTH TIMESTAMP SEMANTICS: Public last_successful_sync equals manifest.published_at (2026-10-04T03:06:53.544812+00:00). Private operational success advances on NO_CHANGE. Public bytes and timestamp stay unchanged.
UI LABEL CHANGED: YES; 마지막 데이터 갱신. One intentional UI wording release; no release triggered by any unchanged sync.

UNTRACKED REPORTS: COMMITTED (feature commit 7773b24).
reason: Four historical Criminal Procedure Act source/article audit reports retained; absolute machine links changed to repository-relative links, no personal machine references or credential values, marked historical before Phase 1H. They are not runtime inputs. The pre-existing unrelated phase1g_legacy_rehearsal.json working change was preserved exactly and excluded from this task's commits.

BACKEND TESTS: 165 PASS locally and in GitHub, including 16 new adversarial/recovery tests.
FRONTEND TESTS: 90 PASS locally and in GitHub.
PUBLIC JSON: 538 PASS; 107 rules; schema 1.5 unchanged.
BUILD: PASS; Vite/TypeScript and exact 541-file artifact validated locally. GitHub build/artifact steps correctly skipped on NO_CHANGE.
SECRET SCAN: PASS; 0 leaks in direct verifier, CI and hosting artifact checks. Historical reports also checked for encoded credential variants and machine paths.

REAL GITHUB RUN: PASS — https://github.com/TCA01/corrections-rule-radar/actions/runs/37304696750
NORMAL RUNTIME: Local repeats 167.312s and 166.828s (average 167.070s), both 133 API calls and NO_CHANGE. GitHub sync 538.266975s (8m58s); whole job 11m23s. API140 + public pages2 = 142 HTTP attempts; average API attempt 3.602429s; three genuine TIMEOUT errors recovered by three request retries, no whole-sync retry. 107 successes, 0 final failures/review/new/persistent events. Commit/build/deploy/ack skipped. The 12-minute sync ceiling is conservative at this observed 8m58s runtime; failed attempts consume the same budget, not another 12 minutes.
LIVE SITE: PASS; manifest, health, rule index, permanent history, recent history and Criminal Procedure Act detail match local last-good bytes after the real run. Dataset ds-c21de361c699692df5cd9e366a51f0bbd31ade59516e8ba4185f2577b1e5a286 remains live.
READY FOR UNATTENDED OPERATION: YES

Failure proof: a real isolated test subprocess blocked in the API opener, exhausted three request attempts, exited nonzero, repeated once in a fresh candidate and ended BLOCKED after six timeouts. Public data/mtimes, state, events/history and retained snapshots stayed intact. Separate worker-deadline and promotion-rollback tests pass; next successful run restores private operational health. No real 30-minute wait or production fault injection was needed.

Initial observation found one unpublished normalized snapshot variation from volatile official attachment download URLs while public/body hashes were unchanged. It was not a legal change. That newly generated candidate was withdrawn; NO_CHANGE now promotes no new legal snapshots and rejects private state drift. Both final repetitions retain the exact full immutable snapshot set. See phase1j_initial_observation.json and phase1j_live_runs.json.

Evidence: phase1j_failure_simulation.json, phase1j_verify_direct.json, phase1j_live_runs.json, phase1j_ci_tests.json, phase1j_normal_sync.json, phase1j_ci_ops_health.json, phase1j_github_run.json, phase1j_github_retry_evidence.txt, phase1j_live_last_good.json. Screenshot: phase1j-live-header.jpg.

No scope, schema, comparison, domain, history, schedule or mobile design change. Continue the existing twice-daily schedule; final failure remains a failed workflow with last-good hosting intact.

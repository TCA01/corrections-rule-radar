# PHASE 1B PRODUCTION HARDENING

BACKEND CHANGE DERIVATION: PASS
TIMEZONE CONTRACT: PASS
SYNC CRON: KST 08:37 / 20:37; UTC 37 23 * * * / 37 11 * * *
API CALLS BEFORE: 159 API + 70 official pages; average 199.332 seconds
API CALLS AFTER: 90 API + 0 pages for core; daily discovery adds 2 pages. 43.40% API reduction.
SEED DISCOVERY FREQUENCY: daily tables, immediate full resolution on table changes, Sunday full outgoing-link audit. Weekly figures are baseline estimates, not newly measured full-audit runs.
LAST-GOOD: PASS
NO_CHANGE: PASS; 2 final stable live runs
GITHUB ACTIONS: PASS (static validation; gated, not activated)
30-DAY HEARTBEAT: PASS; only data/ops/heartbeat.json on idle NO_CHANGE runs
FIREBASE ARTIFACT: PASS; 184 files, including 181 validated API JSON files
FIREBASE CACHE POLICY: PASS
SECRET LEAK: 0
ANDROID CONTRACT: PASS
BACKEND TESTS: 71 / PASS
FRONTEND TESTS: 39/39 PASS
BUILD: PASS
READY FOR FIREBASE DEPLOYMENT: NO — code/artifact ready; external target, GitHub credentials/push policy and cloud execution not verified.

## Measured live runs

| Started UTC | Mode | API / pages | Seconds | Result | New legal events |
|---|---|---:|---:|---|---:|
| 2026-10-03T03:56:45.721216+00:00 | CORE_WITH_DAILY_DISCOVERY | 90 / 2 | 102.875 | PUBLISHED | 0 |
| 2026-10-03T04:01:44.976391+00:00 | CORE_STABLE_IDS | 90 / 0 | 100.407 | PUBLISHED | 0 |
| 2026-10-03T04:11:16.184515+00:00 | CORE_WITH_DAILY_DISCOVERY | 90 / 2 | 100.704 | NO_CHANGE | 0 |
| 2026-10-03T04:21:40.143723+00:00 | CORE_STABLE_IDS | 90 / 0 | 99.031 | NO_CHANGE | 0 |

Development PUBLISHED runs reflect explicit 1.2 comparison-format refinements, with zero new legal events. Final unchanged runs preserve bytes/mtimes, hashes and IDs. Prior archive format 1.1 remains byte-identical.
Archive preservation: PASS; 69 original archive files compared.

## Remaining activation work

- Configure/push a default-branch GitHub repository and permit allowlisted bot commits.
- Set LAW_API_OC and FIREBASE_SERVICE_ACCOUNT GitHub secrets.
- Set intended FIREBASE_PROJECT_ID and verify Hosting service account permissions/default site.
- Enable PRODUCTION_PIPELINE_ENABLED only after target/credentials review; hosted Actions/deployment are untested.

No Firebase deployment, remote push or frontend redesign was performed. Same-session stability only; multi-day observation and real hosted IAM/cache checks remain outstanding. Fixed historical fixtures prevent effective-date rollover from breaking unattended CI. Public health remains published-dataset health; private last_attempt/last_successful_sync and request metrics reflect each attempt.

Details: phase1b.json, production/*.json, frontend_phase1b.json, workflows.json, firebase_artifact.json, docs/phase1b_operations.md and docs/phase1b_contract.md.

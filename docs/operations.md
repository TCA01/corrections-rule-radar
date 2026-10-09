# Last-good operations

Internal health: last_attempt, last_successful_sync, api_status, core_registry_total,
success_count, review_count, failure_count, publication_status, last_dataset_version.
Public health includes only safe dataset status/counts and last successful published
verification. On a no-change run internal success advances, legal public data stays byte
identical. The UI labels this **마지막 법령 데이터 반영**. The legacy v1 field name
`last_successful_sync` is the published dataset timestamp, not the latest poll.
Phase 1K publishes successful scan completion through separate `ops-status.json`.
It may generate an operational commit and Hosting release without a legal change.
The header displays **최근 자동 확인** only for actual schedule events. Manual
checks display **최근 시스템 확인 · 수동 실행**, retaining the last verified
scheduled completion separately. The cron is 08:37/20:37 KST; actual GitHub
schedule delivery may be delayed. See `phase1m_contract.md`.

One-item errors remain isolated in the resolution report and do not erase retained
snapshots. This Phase 0 uses strict whole-dataset publication blocking for any
unresolved seed. A future policy may publish other changes only by carrying forward
verified last-good rows and clearly surfacing degradation; that policy is not enabled.
Total outages and incomplete pagination cannot publish. An absent rule is REVIEW;
verified seed removal is a distinct event. All historical evidence is retained.

Treat source tables as complete only after structural/count/duplicate validation.
The sync blocks any membership change pending review; a self-consistent but
unexpectedly reduced official table cannot silently retire trusted identities.

Rollback copies remain under ignored `data/staging/backup-*`. Recovery must verify
the old manifest and full schema set before restoring. Do not delete these during
failure investigations. Firebase release rollback is separate and future-only.

## Unattended execution (Phase 1J)

Run `python scripts/production_sync.py` (or the scheduled entry point). The
supervisor gives all attempts a shared 720-second budget, including preparation
and validation, reserving up to 60 seconds for validation and local promotion.
Each complete attempt runs in a separate disposable process and candidate tree.
An expired worker is killed and waited for; it never writes the live legal state.
Only a completed, validated PUBLISHED/NO_CHANGE candidate can be promoted. State
and new immutable snapshots are backed up/rolled back on promotion failure.

The official API client bounds the entire transport (DNS, connect/TLS, body
read) at 30 seconds with a daemon transport thread. A late response cannot write
a cache or legal data. Maximum three attempts, with 1 and 2 seconds backoff,
apply to timeout/network/reset errors, HTTP 429 and HTTP 5xx. Deterministic 4xx,
authentication, redirects and invalid payloads are not request-retried. An
exhausted transient core request stops the candidate immediately. One fresh
whole-sync retry after 5 seconds is allowed inside the same 720-second budget;
authentication, review/schema failures and budget exhaustion are not retried.

GitHub's sync step has a 15-minute safety limit; the job's 25-minute limit also
covers setup, verification and a possible changed-data release. Both failed
attempts produce a nonzero exit, so state commit/build/deploy steps do not run.
Reports upload even on failure. NO_CHANGE leaves every legal public byte and mtime
untouched; it does not create change events. The separate successful scan status
does trigger a Hosting release. Existing
restart-safe pending-release, explicitly forced release and 30-day heartbeat
policies remain in effect.

Private `production_sync.json` includes the deadline, attempt results and retry
count. Sanitized attempt evidence remains under
`data/reports/production_attempts/` and is uploaded as an operational artifact.
API failure diagnostics include endpoint, target, supplied ID/MST, attempt,
error code and HTTP status, never a credentialed URL. Publication timestamps
stay stable on NO_CHANGE; public ops status and private health record successful polls.
See `phase1k_contract.md` for the separate ops hash and release acknowledgment.

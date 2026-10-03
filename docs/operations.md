# Last-good operations

Internal health: last_attempt, last_successful_sync, api_status, core_registry_total,
success_count, review_count, failure_count, publication_status, last_dataset_version.
Public health includes only safe dataset status/counts and last successful published
verification. On a no-change run internal success advances, public data stays byte
identical. The future UI should label it **마지막 정상 동기화**, never just 마지막 실행.
For fresher live operational status, a separately deployed status endpoint is future
work and must not create daily dataset commits.

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

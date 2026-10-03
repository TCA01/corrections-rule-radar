# Future GitHub Actions design — no workflow deployed

Phase 1B prepares .github/workflows/production.yml and validation.yml. No remote
job is enabled here. phase1b_operations.md supersedes this Phase 0 design where
different (daily tables/weekly full audit, pending deployment recovery, heartbeat).

Regulation checks run twice daily at **08:37 and 20:37 Asia/Seoul**. Corresponding
UTC cron is `37 23,11 * * *` (23:37 UTC is next day's 08:37 KST). Non-round minutes
reduce busy scheduler slots; GitHub scheduled execution is best effort, not an SLA.
Also offer `workflow_dispatch`. Do not check regulations only once every 30 days.

One concurrency group per sync/deploy environment, with `cancel-in-progress: false`.
Run on default branch, pin/review action versions, install locked Python dependencies,
provide `LAW_API_OC` to Python only, and use minimum permissions. Separate Firebase
authentication from API authentication. No credentials, remotes or Actions secrets
are created during Phase 0.

When trusted data changes: validate the entire dataset → commit only allowlisted
generated state (`data/registry`, verified snapshots, reviewed seed metadata,
approved public JSON) → deploy Hosting → verify live health and manifest digest.
Never `git add .`. Raw caches/staging/reports and volatile attempts stay out of
scheduled commits. Avoid registry `last_verified_at` churn on no-change runs;
public timestamps describe the published validated dataset, while internal health
tracks every success. Do not expose an attempted execution as a successful sync.

When data does not change: no public rewrite, no meaningless daily commit, no
unnecessary Firebase deployment. Record operational success privately.

## Separate 30-day heartbeat

Public scheduled workflows can be automatically disabled after prolonged repository
inactivity (GitHub documents 60 days). At >=30 days since the most recent repository
activity commit (meaningful data/code change **or previous heartbeat**), update only
`data/ops/heartbeat.json` with `last_heartbeat` and `last_successful_sync`.
This tiny operational commit resets the heartbeat timer without fabricating a
regulation event or touching public JSON. Use UTC ISO timestamps and explicitly
allowlist the heartbeat path. Preserve distinction between meaningful data change
and operational activity in reporting. A failed sync must preserve last successful
sync rather than advancing it. The heartbeat is a design in Phase 0, not a remote job.

Manual reruns still obey full validation, deduplication and concurrency. If scheduled
workflows are already disabled, a heartbeat cannot run itself; a maintainer must
re-enable scheduling. Monitor that condition separately.

Official scheduler documentation:
https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule

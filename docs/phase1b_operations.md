# Production operations prepared, not deployed

## Execution policy

GitHub Actions production.yml checks core rules at 08:37 and 20:37 KST:
UTC `37 23 * * *` (previous UTC calendar date) and `37 11 * * *`.
workflow_dispatch supports full_audit. Scheduled jobs are best effort, can be
delayed, and run from the default branch. Concurrency group
production-state-and-hosting with cancel-in-progress false serializes writers.

Canonical IDs are trusted only from reviewed last-good state. Normal core sync
fetches each administrative current version by LID; explicitly repealed entries
are checked against official history and fetched by proven serial. Laws use LID
listing to identify current/future versions, then fetch structured bodies. Every
version remains fetched/normalized; body-less metadata responses are rejected.

Daily morning discovery fetches both official Corrections tables, validating
declared counts/duplicates and comparing title, outgoing URL, type and department.
An observed table change triggers full official identity resolution. Each Sunday
morning also performs full outgoing-link resolution even if table text is identical,
to detect hidden link-target drift. Such target drift has a maximum intended
weekly detection interval rather than daily. API timing or scheduler outages can
increase this interval; this is explicit, not a discovery correctness guarantee.
New/removed core IDs block publication for review and do not auto-add/remove rules.

Local commands:

```powershell
python scripts/production_sync.py
python scripts/production_sync.py --discovery
python scripts/production_sync.py --full-audit
python scripts/verify.py
python scripts/validate_workflows.py
npm test --prefix web
npm run build --prefix web
python scripts/verify_artifact.py
```

Run from repository root, one writer at a time. Reports include duration, API/page
request counts, retries, response averages, success/review/failure, last-good
version, publication result and byte/mtime/hash/event comparisons. RUNNING reports
survive interruption and never qualify as verified success. No raw response,
authenticated URL, credential or traceback belongs in these safe reports.

## Last-good and deployment recovery

Fetch → normalize → diff → build → schema/leak validation in staging → rollback-safe
local directory switch. Missing core, partial body, auth errors, timeout/500,
invalid schema or failed directory switch preserve last-good public data.
No-change updates private ops only; no public timestamp rewrite.

Workflow checks all backend/frontend tests before staging allowlisted generated
state. It builds and safety-checks the exact combined artifact before committing
trusted changed state. Generated allowlist: public/api/v1 JSON; registry
state/rules/events; normalized snapshots; reviewed collected seed; deployment
marker. Raw caches, staging, code, secrets and volatile ops/reports are excluded.

The changed-state commit includes a pending dataset deployment marker. Successful
Hosting deployment plus public manifest/health/rules verification clears it in
an acknowledgment commit. Failure leaves pending intact: the next NO_CHANGE run
rebuilds/retries deployment. A failed acknowledgment push also causes a harmless
retry. Distributed Git/Hosting actions are not one transaction. No local or cloud
publication occurs for an invalid candidate. Probe failures are not automatic
cloud rollback: the pending candidate is retried; maintainers can restore a
previous Firebase release during an incident. Clients retain their verified
last-good cache on mixed versions or fetch failure.

When no repository commit has occurred for >=30 elapsed days, update and stage
only data/ops/heartbeat.json. Last activity includes code/data/deployment commits
and the prior heartbeat. Never touch regulation data or create legal events for
a heartbeat. Failed sync jobs stop before commit/heartbeat. If scheduling is
already disabled, a maintainer must re-enable it; heartbeat cannot run itself.

## Hosting and activation prerequisites

firebase.json points to web/dist: React index/assets plus copied api/v1. No SPA
fallback is configured, so missing API paths cannot return index.html. index/root
use no-cache; API JSON uses max-age=60, must-revalidate; hashed assets use one year
immutable. Safety checks reject non-allowlisted files, maps, symlinks, credentials,
local paths, raw-cache paths and tracebacks; all API JSON and references validate.

No Firebase project, deployment, repository push or secret setup is performed.
Before enabling the prepared job, configure:

1. A GitHub default-branch repository containing source and trusted generated
   baseline. Verify contents-write bot push policy/branch protection.
2. Secrets LAW_API_OC and FIREBASE_SERVICE_ACCOUNT (Hosting deployment service
   account JSON, scoped per Firebase guidance).
3. Repository variable FIREBASE_PROJECT_ID for the intended default Hosting site.
   Post-deploy probe assumes its default project-id.web.app hostname.
4. Set PRODUCTION_PIPELINE_ENABLED=true only after reviewing target and credentials.
   Both scheduled and manual production jobs remain gated until then.

Offline validation.yml runs without the real Law API secret, using an ephemeral
unlogged dummy value for leak/test validation. Production LAW_API_OC is scoped
only to Python sync/verification steps, not npm builds. Safe reports are retained
as Actions artifacts for 30 days. The workflows were validated statically locally;
hosted Actions/IAM/push and actual cloud deployment remain untested.

Official references: [GitHub scheduling](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule),
[Firebase headers](https://firebase.google.com/docs/hosting/full-config#headers),
[Firebase GitHub deployment](https://firebase.google.com/docs/hosting/github-integration),
[deployment service account](https://github.com/FirebaseExtended/action-hosting-deploy/blob/main/docs/service-account.md).

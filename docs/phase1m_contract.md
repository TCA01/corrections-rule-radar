# Phase 1M — successful scan provenance

Schema 1.5 remains in use. Legal schemas, identifiers, comparisons and event
semantics are unchanged. The ops-status schema adds optional fields only:

- `trigger`: SCHEDULE only for the actual GitHub `schedule` event; otherwise
  MANUAL. An explicit manual schedule-policy rehearsal stays MANUAL.
- `github_run_id`: actual Actions run ID when available.
- `schedule_cron`: actual scheduled event's cron, never the manual test mode.
- `last_scheduled_scan`: last completed successful scheduled production scan,
  independently preserved across manual runs and blocked collections. Contains
  UTC start/completion, actual result, dataset version, cron and run ID. Null
  means no verified scheduled record is available, not a fabricated success.

Existing required fields and old documents remain valid. Clients should label
legacy documents without a trigger as a system check, not automatic. Legal
publication time still comes from health/manifest; ops updates cannot alter
legal dataset identity or create legal change events.

The legacy October 7 02:32 record is annotated using the completed successful
schedule run 37503211648 and its uploaded report. Its timestamps are unchanged.

The exact 107-ID tracking scope is fixed by approval. Current/repealed counts
are observations of official structured states, not permanent release constants.
Repeal requires exact-ID official history plus matching structured body and an
effective date already reached. Empty API responses still fail closed.

The cron remains 08:37 / 20:37 KST. GitHub's schedule delivery is best effort;
the audit observed delays before run creation. This change cannot guarantee
execution at the configured minute or eliminate GitHub-side dispatch delays.

Repeated fresh Actions checkouts compare the generated legal version against
the published manifest. Private operational health is deliberately excluded
from generated-state commits and cannot determine whether legal publication
changed. Repeal-search wording and scan timestamps do not republish unchanged
legal data. A real repetition exposed and verified this separate defect.

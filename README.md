# 교정관련 규정 추적기 — Phase 1H

Python Law.go.kr pipeline and React Web, hosted in the existing Firebase project.
No Android app, OCR, attachment downloads or legal interpretations are included.

Current: 107 API-trackable rules, 105 current and 2 historical/repealed.
Schema 1.5 explicitly changes upcoming comparisons to the previous effective
state, with optional current-baseline cumulative comparisons. The Web labels
both modes and displays their exact before/after dates. Same MST + different
efYd states remain distinct; proven staged enforcement is classified separately
from corrections. Two incorrect future events are replaced with an audit trail;
all unaffected event IDs and immutable artifacts are preserved. See
docs/phase1h_contract.md and data/reports/phase1h_history_migration.json.
The Phase 1G scope/creator credit and earlier evidence remain unchanged.

Phase 1A: `python scripts/observe.py --runs 3` observes normal live syncs;
`python scripts/verify.py` verifies recovery, contracts and secrets;
`python scripts/freeze_contract.py` checks the frozen API v1 candidate.
See docs/observation.md, docs/business_domain_review.md, docs/api_v1_candidate.md
and data/reports/phase1a.md for the historical pre-frontend observation phase.

## Run locally

Python 3.11+. Set `LAW_API_OC` in the calling process environment; `.env` files are
not automatically read. Never pass the value on the command line.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python scripts/create_schemas.py
.venv\Scripts\python scripts/production_sync.py
.venv\Scripts\python scripts/production_sync.py
.venv\Scripts\python -m unittest discover -s tests -v
```

One-time history backfill: `python scripts/backfill_history.py`, then
`python scripts/migrate_history.py` for an isolated rehearsal. After passing
the backend checks, `python scripts/migrate_history.py --publish` explicitly
generates the local schema 1.3 dataset. These commands do not deploy.

Phase 1F release preparation: `python scripts/prepare_expansion.py` resolves the
exact approved additions live and backfills their bounded history;
`python scripts/configure_expansion.py` applies evidence-based domains and
provenance; `python scripts/rehearse_expansion.py` validates the actual publication
and recovery logic in isolation. After tests pass, the one-time
`python scripts/production_sync.py --approved-expansion` performs the explicit
approved 68 → 106 transition. Normal subsequent runs use
`python scripts/production_sync.py`. The approval cannot be reused for later
scope expansion. No command in this sequence deploys Firebase.

Missing authentication stops with `WAITING_FOR_LAW_API_OC`. Networking must be
permitted. Failures print only classified errors, never authenticated URLs or
tracebacks. `scripts/sync.py --from-collected` is an **offline publication test**,
not a live second run. See `data/reports/phase0.md` for measured results and limits.

## Evidence and state

- `data/seed/corrections.json`: live official tables, outgoing URLs, rowspans/counts.
- `data/reports/resolution.json`: every seed, including unresolved REVIEW entries.
- `data/raw_cache/`: ignored official response bytes with credential echoes redacted.
- `data/snapshots/`: immutable normalized versions with separate semantic hashes.
- `data/registry/`: trusted last-good registry, baseline state and deduplicated events.
- `data/staging/`: ignored candidate collection and validated publication staging.
- `data/ops/`: attempts/successes, degradation, dataset identity; operational only.
- `schemas/`: strict versioned public contracts, shared by Web and Android.

Public output is blocked when any seed identity/current metadata cannot be proved.
An official missing result is REVIEW, never proof of repeal. Cached snapshots
are retained for failed items; incomplete collection never replaces last-good data.

## Design documents

See `docs/api_evidence.md`, `docs/data_contract.md`, `docs/architecture.md`,
`docs/github_actions_design.md`, `docs/firebase_architecture.md`,
`docs/android_architecture.md` and `docs/operations.md`.

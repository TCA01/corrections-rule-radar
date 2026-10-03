# 교정업무 변경 레이더 — Phase 1E

Python Law.go.kr pipeline and React Web W1. No Android app, Firebase deployment,
OCR, attachment downloads or legal interpretations are implemented here.

Current: production core remains 68. Phase 1E adds persistent exact-version
change history and a recent 90-day feed. Main schema 1.3; immutable archives
remain 1.1. No frontend edits or deployment are included. Web W3 can consume
schema 1.3 separately. Future provenance/scope expansion requires 1.4.
See docs/phase1e_contract.md and data/reports/phase1e.md.

Phase 1A: `python scripts/observe.py --runs 3` observes normal live syncs;
`python scripts/verify.py` verifies recovery, contracts and secrets;
`python scripts/freeze_contract.py` checks the frozen API v1 candidate.
See docs/observation.md, docs/business_domain_review.md, docs/api_v1_candidate.md
and data/reports/phase1a.md. UI/Firebase remain unbuilt and undeployed.

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

# Phase 1I visual comparison source, API v1 schema 1.5

The public contract remains unchanged. Persistent events with
`OFFICIAL_COMPARISON_EXCERPT` or `LAWGO_OLD_NEW` / `LAWGO_ADMIN_OLD_NEW`
contain official comparative excerpts. They can include presentation shorthand
such as `(생  략)` and `(현행과 같음)`. These excerpts and their article counts
are retained as immutable evidence, not passed directly to a substantive word
diff. A count of officially selected articles can differ from the full-text
visual change count if the full bodies are equal.

The data/source adapter (`web/src/services/comparison.ts` and `api.ts`) fetches
the event's explicit `before_version.snapshot_url` and
`after_version.snapshot_url`. It validates canonical ID, identifier, effective
date and the declared body hash against the event references, then groups
structured articles using the same text-field order and article-number rules
as the pipeline. Official metadata selects the article numbers; the matching
full bodies supply display text. Equal bodies are suppressed, and literal
legal words including `생략` and `삭제` are preserved without string stripping.
Both unified and split views use that resolved text. Failure, ambiguous
structure, missing references or mismatched versions yields an explicit
unavailable state; the UI does not fall back to highlighting shorthand.

`STRUCTURED_SNAPSHOT_DIFF` events and Phase 1H upcoming incremental/cumulative
comparisons retain their existing authoritative arrays and pairings. The
adapter never infers a predecessor from the current rule or dates, never
rewrites an event and never fetches third-party law endpoints in the browser.
Android clients can use the same already-published archive references and
source-selection rule without a contract migration.

The exact article 14 audit, raw payload digest, before/after references and
complete legal text are in `data/reports/phase1i_audit.md` and its JSON evidence.
The tested case is a fixture, with no rule-specific production logic.

Browser layout regressions are in `tests/browser/phase1i.cua.mjs`. In cua_repl,
import that module and call `verifyPhase1IMobile(tab, viewport)` with a homepage
tab and the documented viewport capability. It exercises 360, 390, 412 and
1280px. Reset the temporary viewport override after verification. Local and
live rectangle/overflow evidence is saved under `data/reports/phase1i_mobile_*`.

# API v1 schema 1.5 — upcoming effective states

This is an intentional semantic/contract change from 1.4. Endpoint URLs and
canonical IDs remain stable. Clients must require schema 1.5 for the new
upcoming comparison semantics; do not silently accept 1.4 as incremental.

Each `rule.upcoming[]` is ordered by ascending effective date and carries:

- `comparison_mode = PREVIOUS_EFFECTIVE_STATE`: `articles_compared_to` and
  `changed_articles` compare the immediately preceding effective state.
- `cumulative_comparison_mode = CURRENT_BASELINE`:
  `cumulative_articles_compared_to` and `cumulative_changed_articles` compare
  the actual canonical current snapshot with that future state.
- Both comparison sources are `STRUCTURED_SNAPSHOT_DIFF`: full normalized
  article text from official Law.go.kr structured snapshots, not an excerpt.

Upcoming article keys use canonical article numbers (`article-220의2`) like
persistent history, so amendment flags in raw API 조문키 cannot create duplicates.
Recorded comparison arrays/references survive their transition to current.

The first preceding state is always `collection.snapshots[canonical_id]`.
A historical version with the same effective date cannot replace it. Identity
includes canonical ID, MST/version, effective date and content hashes. Same MST
with different efYd is supported. Conflicting future states on one date fail
closed instead of choosing an arbitrary version.

`STAGED_EFFECTIVE_DATE` is added to persistent event types. Classification
requires same promulgated MST, an increasing effective date, changed normalized
articles and structured addendum commencement evidence matching the issue
number. `staged_effective_evidence` exposes that evidence. A date change alone
remains `EFFECTIVE_DATE_CORRECTED`.

Only incorrect active future pairings/classifications are replaced. The
migration report records retired/replacement IDs and reasons. Unaffected past
events and their original detection times/IDs/immutable files remain unchanged.
Retired event detail URLs remain available as historical evidence but are not
listed in active history or recent feeds. Archived version format remains 1.1;
unchanged immutable event files retain their original 1.3/1.4 envelopes.

Web defaults to **직전 시행상태 대비**. **현재 기준 누적 비교** is explicit and
optional. Both modes display the backend-provided before/after dates and
article counts. Kotlin/Compose can use the same references and arrays without
reconstructing legal pairings. No LLM, legal interpretation or scope expansion
is involved.

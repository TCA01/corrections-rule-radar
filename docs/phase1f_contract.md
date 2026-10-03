# Phase 1F: schema 1.4 approved production scope

The release is exactly the previous 68 stable identities plus the 38 explicitly
approved Phase 1D API_TRACKABLE candidates: 15 DIRECT_CORRECTIONS and 23
CROSS_DOMAIN_CORRECTIONS. Approval is bound to the Phase 1D report hash and exact
ID sets. A count mismatch, removal or extra candidate blocks publication.
API_TRACKABLE_LIMITED, API_UNAVAILABLE and REVIEW cannot enter production.

Main manifests, rule details/lists, history/recent/legacy change feeds and health
are schema 1.4 at their existing URLs. Version snapshots remain immutable schema
1.1. Existing persistent event details retain their schema 1.3 envelopes and
bytes; new event details use 1.4. The change schema explicitly accepts both
immutable envelope versions, whose event payload semantics are unchanged.
Existing event IDs, detection times, comparisons, aliases and archive URLs stay
available. Scope expansion and taxonomy corrections are provenance changes,
not fabricated legal amendments. The 90-day effective-date window retains
all earlier recorded events in history.

Every rule summary/detail has `rule.provenance`:

- scope_class: OFFICIAL_CORRECTIONS_LIST, DIRECT_CORRECTIONS,
  CROSS_DOMAIN_CORRECTIONS or HISTORICAL_REPEALED
- selection_basis: factual Korean text from reviewed official scope evidence
- applies_to: reviewed relevant targets, with no claim of blanket applicability
- official_seed_name / official_seed_url: null for independently discovered rules
- canonical_source_url: current official reader URL, checked against the rule URL
- discovery_source: audited discovery channel(s)
- scope_review_status: APPROVED
- api_tracking_class: API_TRACKABLE
- structured_body_source / history_source / appendix_metadata_source:
  explicit Law.go.kr structured source types

Scope approval is persistent by stable ID. A newly renamed rule keeps aliases;
no title-only joining or successor-ID merging is allowed. Repealed records are
retained under HISTORICAL_REPEALED and never counted as current. Phase 1D's
lineage evidence remains unchanged; 26424 is not merged with 84831 or 49753.

The controlled domain registry adds 보고. Product-owner decisions apply to IDs
admrul-32484 and admrul-51868. The actual current API titles are 현황작성 및
보고요령 지침 and 교정본부 보고사무지침, respectively; the different titles
quoted in the request are not used to rename or re-key official data.

New domain assignments cite official title, department, purpose/scope/body and
their exact content hashes in the authoritative registry. Multiple domains are
allowed. Facility construction/location topics use 기타 because the controlled
taxonomy has no separate facility/construction domain; these lower-confidence
assignments are reported separately. If an approved classification's evidence
changes, publication safely uses 기타 with domain_assignment_status=FALLBACK and
an internal domain_fallback report. This policy avoids periodic human maintenance
as a prerequisite for approved-rule updates. Frontend wording is 관련 업무 분야
and 선정 근거; it must not create legal interpretations or provenance.

Current/upcoming appendices add status=AVAILABLE or REMOVED, conservatively
derived from exact 삭제/date tombstone titles. Original titles, links and raw
metadata remain unchanged; archive hashes are not recomputed for this derived
flag. Other titles containing 삭제 are not automatically tombstoned. Persistent
appendix removals retain original metadata and explicit REMOVED status; clients
must suppress downloads. No document contents are read.

Tracking and all current/history/future revalidation use official JSON/XML APIs.
There are no HTML/BeautifulSoup/document parsers on the production import path.
The requested daily Corrections-page check fingerprints opaque bytes only. A
page change can trigger an API-only discovery queue, never production admission.
That monitor is independent: its outage does not prevent approved API updates.
Sunday full ID revalidation independently cross-checks API lists with detail
identity, serial and effective date for every approved record. Administrative
future versions are detected where the official stable-ID response exposes them;
an exact-ID historical predecessor must resolve before publication. There is no
claim of complete enumeration of unpublished administrative future versions.

The existing single workflow, 08:37/20:37 KST schedule, workflow_dispatch,
opaque-page fingerprint/pending-review cache (only two credential-free files),
concurrency protection and 30-day GitHub heartbeat remain. No deployment or
frontend modification is included. Web W4 must consume and validate 1.4 before
any deployment. Generation validates schemas, scope, provenance, reference
resolution and event/detail consistency before the local atomic dataset switch.
One unresolved approved record blocks the complete candidate and retains the
last-good dataset. New scope always requires API audit, scope review and a new
explicit human approval; the Phase 1F approval cannot authorize a later delta.

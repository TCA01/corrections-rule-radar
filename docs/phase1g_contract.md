# Phase 1G: one approved law, existing schema 1.4

The product owner explicitly approved only 형사소송법, as
CROSS_DOMAIN_CORRECTIONS. Its stable identity is resolved through the live
structured API and checked against current version/body and history list.
No external report supplies its identifier. The release adds exactly one ID to
106: 107 total, 105 current, two historical/repealed. No other law is admitted.
Approval is bound to the live eligibility report hash and exact previous IDs in
data/registry/scope_approvals/phase1g.json; it cannot be reused.

Main schema, schema hashes and URLs remain 1.4. Existing immutable archives and
event details are preserved. Provenance uses existing source values
MANUAL_OFFICIAL_REVIEW (the owner's one-time scope decision) and LAW_API_KEYWORD
(structured exact-identity resolution). No manual legal text or recurring
maintenance is introduced. The official API remains the legal-data authority.

The primary domain is the existing 수용·보안. Selection basis and applies_to
record the approved 수용기록·구속·영장·석방 search context. No new domain or
legal interpretation is introduced. Missing official department data stays null.

History preparation is a one-time bounded version audit, independent of normal
sync. It lists all versions, selects up to 32 latest version/effective-date pairs
and fetches their exact predecessor. This fixed request budget spans years rather
than restricting history to 90 days. The report records the available, selected,
excluded counts and date range. Official old/new excerpts are used only when
their identities match; otherwise complete structured snapshots are compared.
Missing comparisons stay explicit. Events persist; the recent feed is derived
from the 90-day Seoul effective-date window.

Normal/scheduled collectors automatically include the new stable ID and its
current/future versions and comparisons. They do not repeat the history crawl.
A temporary failure blocks the whole candidate and preserves last-good data.

The API exposes multiple future effective dates for the same MST. Frontend
comparison selection therefore identifies a target by MST plus effective date,
matching the existing backend model. Counts and search remain data-driven.

The footer displays only the approved creator identity and exact personal-project
disclaimer, retaining source attribution and the official-original notice. No
other personal information is added. Release gates cover live eligibility,
second NO_CHANGE, recovery, backend/frontend tests, JSON validation, build,
hosting artifact and secrets. The existing repository/Firebase project receive
the verified release; a real normal workflow and public probes verify operation.

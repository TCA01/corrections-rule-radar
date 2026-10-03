# Phase 0 architecture

Law.go.kr HTTPS → sequential Python client → Corrections seed + stable registry
→ raw evidence + semantic snapshots → validation + deterministic diff
→ staged static `/api/v1/` JSON → future Firebase Hosting → React / Android.

Trusted enrollment starts with complete official Corrections tables, not a fixed
68-item business rule. Declared table counts must match parsed rows; changes from
the initial approximate baseline are reported. Empty, duplicate or malformed
tables abort collection. After a baseline exists, any changed seed membership
blocks publication pending review. New identities generate discovery candidates;
removals generate pending seed-removal events and preserve all last-good rows.

Identity priority: official outgoing version identifier → body stable ID → exact
unique title restricted by ministry/type. Titles are aliases, never primary keys.
Fuzzy title matches may only create REVIEW candidates. Law IDs and administrative
IDs are separate namespaces. Version numbers are not logical IDs. A historical
link returning no body may use an explicit exact-title fallback; it is reported
with lower confidence. This limitation matters for stale links after future renames.

Laws use `eflaw` with stable `LID` and `nw=2,3`, distinguishing current and future.
Bodies use `MST` + `efYd` for exact versions. Administrative bodies use `ID` for
version serial and `LID` for stable identity. Only an official current `Y` body is
accepted. Administrative historical enumeration is verified separately in Phase 0;
broader future admin version discovery remains a production-hardening task.

The first current dataset establishes a baseline; upcoming versions get explicit
future events. Later events use identity, versions, content hashes and evidence,
excluding detection timestamps from event identity. No interpretation of duties.
Metadata, body, appendix metadata and attachment links have separate SHA-256 hashes.
Law article structures and addenda come directly from structured API fields.
Appendix content returned incidentally by the API is retained only in evidence;
normalization excludes that content and tracks metadata/links only. No attachment
internals are downloaded or parsed.

Discovery sources are new Corrections entries, Ministry of Justice administrative
list results and related stable IDs in system-map data. All discoveries outside
the reviewed core remain `DISCOVERY_CANDIDATE`, with no trusted registry mutation.
Phase 0 implements a candidate contract; unattended discovery crawling/enrollment
is future work.

All output is schema-validated and checked for secret/path/username leakage before
the local directory switch. A previous directory is kept for rollback. The switch
is locally transactional for handled errors, not a durable database transaction:
power loss between directory renames requires recovery from the preserved backup.
Future deployment happens only after full candidate and contract verification.

# Schema 1.3: persistent change history

Schema 1.3 reserves persistent history semantics for the existing 68 records.
Phase 1D's unpublished provenance proposal is superseded: provenance/scope
expansion requires **1.4**. No deployment or frontend migration is included.

`manifest.json` links `changes/history.json`, `changes/recent.json` and
`changes/{event_id}.json`. History retains every recorded event indefinitely,
including upcoming events; recent includes effective dates today through
89 days earlier, inclusive, using Asia/Seoul civil dates. Future events remain
in history and the separate upcoming view. Consumers may filter all history
for 30 days, one year or any other range. A rolling-window membership change
is a view change, never deletion of historical evidence.

Legacy latest/upcoming event envelopes remain available. New history event IDs
are version-pair identities and are a distinct namespace of semantics: clients
must not combine the two feeds and assume one row per amendment. Use history
or recent for the new product. Placement/status transitions do not alter history
IDs or text. First detection timestamps are retained. New amendments and
same-version metadata corrections have separate identities.

`before_version` and `after_version` include exact serial, effective date,
body hash, immutable snapshot reference and official URL. Event details have
schema_version but no global dataset version, so their content remains identical
when another event is published. Existing immutable version files stay schema
1.1 at their original content-addressed URLs. They are not regenerated under 1.3.

Comparison sources are LAWGO_OLD_NEW, LAWGO_ADMIN_OLD_NEW and
STRUCTURED_SNAPSHOT_DIFF. Official API source is used only after checking both
stable IDs, serials and effective dates against the actual pair. Official old/new
texts are excerpts, often with omission markers; `comparison_scope` discloses
OFFICIAL_COMPARISON_EXCERPT. Full-body fallback uses canonical article numbers
and includes administrative paragraph continuation text. Neither source offers
legal interpretation. Missing structure is COMPARISON_UNAVAILABLE with a reason.
Null source is only used when no article comparison was possible.

APPENDIX_REMOVED retains prior official metadata, sets status REMOVED and
after_metadata null. Consumers hide download controls for removed entries;
no currently functioning download URL is required. No attachment contents are
parsed. Body-identical corrections never create article-change rows.

Future UI wording: **관련 업무 분야**. This service detects and organizes official
changes; it does not determine how an official must perform their duties.

Backfill enumerates official JSON/XML histories for all 68 stable identities,
resolves the predecessor of each recent effective version, and retains one older
change per rule where available as an initial historical baseline. It is not a
claim that every amendment since a rule's creation has been backfilled. Earlier
recorded events are never purged. Normal sync fetches an official comparison only
for new version pairs; frozen histories are reused locally. Detailed coverage
and API limitations are recorded in the Phase 1E reports.

# API v1 freeze candidate — schema 1.1

Historical Phase 1A candidate. Phase 1B deliberately migrates the active main
contract to 1.2; immutable archives retain 1.1. See phase1b_contract.md.

API_V1_CANDIDATE = true. This is a data contract candidate for React Web and
Kotlin/Compose, not a deployed service or implemented client. Phase 1A explicitly
migrates the pre-client schema from 1.0 to 1.1 at `/api/v1`. Classification and
references change dataset identity but create no legal amendment event.

| Requirement | Reviewed contract |
|---|---|
| Stable IDs | Opaque canonical IDs, official stable identifiers and aliases; preserve leading zeros |
| Related work | Nullable primary_domain, secondary_domains, business_domains, classification_status; REVIEW renders unclassified |
| Current/future/repealed | Rule status, separate current/upcoming arrays, version_status, ISO effective dates |
| Changes | Stable event IDs; latest/upcoming lists; baseline does not invent historical changes |
| Old/new references | Nullable baseline old_reference, required new_reference, immutable snapshot URL plus official URL |
| Dates | ISO dates/timestamps; nullable absent official metadata |
| Appendices | Official appendix/attachment descriptors and URLs; no download/OCR |
| Official URLs | Sanitized source URLs; no credential-bearing request URLs |
| Health | PUBLISHED_DATASET scope, published success date, identity and classification reviews separated |
| Consistency | Dataset version on manifest/list/detail/changes; clients compare versions and retry mixed reads |

Immutable version files use ARCHIVE status. Read CURRENT/FUTURE placement from
rule detail. Official article/addenda trees retain variable JSON structure;
TypeScript can use JSON values and Kotlin serialization JsonElement there, with
typed core metadata. No legal instruction text is generated.

`schemas/api_v1_candidate.lock.json` freezes schema bytes. Publication and
verification reject drift. Run `python scripts/freeze_contract.py` to check.
Refreshing the lock requires explicit documented contract review and migration;
`--record-reviewed-candidate` is not a routine sync step. After consumers ship,
breaking types, field meanings, required fields or enums require v2. Document
compatible additions and coordinate client/schema tests before changing v1.

Public health describes the retained published dataset, and remains unchanged on
failed/no-change attempts. Fresh attempts/outages are private in data/ops/health.json.
A future hosted service needs separate operational health for immediate outage
visibility. Local rollback-safe directory switching is not a CDN transaction;
hosting requires version-consistent release and client version checks.

Limitations: no client has been compiled; appendices remain descriptors; two broad
reporting rules await business-owner classification. All 68 rules can be rendered.

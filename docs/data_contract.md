# Shared public API v1

Active main schema: 1.4. Immutable version artifacts retain archive format 1.1;
existing persistent event detail envelopes retain 1.3. The approved 106-record
scope, provenance and appendix tombstones are in phase1f_contract.md.
Persistent history semantics are in phase1e_contract.md. Legacy article/detail
fields remain documented in phase1b_contract.md.

UTF-8 JSON; string IDs; ISO-8601 dates/timestamps; explicit nullable metadata;
no HTML needed for core display; root-relative `/api/v1/` paths. JSON Schema
Draft 2020-12 contracts are self-contained in `schemas/`.

| URL | Schema | Purpose |
|---|---|---|
| `/api/v1/manifest.json` | manifest | Dataset identity and shared URLs |
| `/api/v1/rules.json` | rules | Registry summaries, aliases, related domains |
| `/api/v1/rules/{canonical_id}.json` | rule | Current/upcoming structured versions |
| `/api/v1/rules/{canonical_id}/versions/{version-key}.json` | version | Immutable event version references |
| `/api/v1/changes/latest.json` | changes | Observed current/historical events |
| `/api/v1/changes/upcoming.json` | changes | Events for pending effective versions |
| `/api/v1/changes/recent.json` | recent | Persistent events effective in the last 90 Seoul civil days |
| `/api/v1/changes/history.json` | history | All persisted changes, retained indefinitely |
| `/api/v1/changes/{event_id}.json` | change | Exact-version comparison, independent of dataset timestamps |
| `/api/v1/health.json` | health | Last verified published dataset and counts |

ID namespaces: `law-{official-stable-ID}`, `admrul-{official-stable-ID}`.
Keep leading zeros where provided. Clients must treat IDs as opaque strings.
Event IDs hash identity, versions, semantic hashes and evidence; never timestamps.
Dataset identity hashes semantic public content, excluding run timestamps.
Immediate identical reruns keep public bytes and modification times untouched.

Event enums: NEW_RULE, RULE_RENAMED, RULE_AMENDED, FUTURE_EFFECTIVE_VERSION,
EFFECTIVE_DATE_CHANGED, ARTICLE_CHANGED, APPENDIX_CHANGED, ATTACHMENT_CHANGED,
RULE_REPEALED, RULE_REMOVED_FROM_CORRECTIONS_SEED, NEW_CORRECTIONS_SEED,
DISCOVERY_CANDIDATE. Discovery records are internal pending review.

Rule status: CURRENT / REPEALED / REVIEW. Classification: REVIEW / REVIEWED.
No title-based permanent keys, local paths, request URLs containing credentials,
raw authentication messages or tracebacks are allowed. API article/addenda trees
are JSON values with source variation, so generated clients should use JsonElement
or a JSON tree for those fields until a later typed article contract is approved.
Their main rule cards can use entirely typed metadata.

Possible future tooling: generate TypeScript interfaces with json-schema-to-typescript;
generate Kotlin serialization models using a reviewed JSON Schema generator or
explicit mapped DTOs. Validate generators with the same fixture corpus and retain
nullable date/string fields. No generator or mobile SDK is required in Phase 0.

Related-domain vocabulary is in `data/seed/business_domains.json`. Unreviewed
classifications remain empty and flagged REVIEW. Display wording: **관련 업무 분야**.
Do not derive legal instructions or conclusions from categories or change events.

Phase 1A candidate schema 1.1 adds primary/secondary domains, version status,
resolvable old/new event references and published-health scope. See
docs/api_v1_candidate.md for the review and schema freeze policy.

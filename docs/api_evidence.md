# Official API evidence and security

Official guides: https://open.law.go.kr/LSO/openApi/guideList.do
Individual guide IDs and safe request parameters are in capability reports.

| Concept | Official list field | Body request | Official public detail |
|---|---|---|---|
| Logical law | 법령ID | `ID`, or `LID` on eflaw list | Not a version serial |
| Law version | 법령일련번호 | `MST` (+ `efYd` for eflaw) | `lsiSeq` |
| Logical admin rule | 행정규칙ID | `LID` | Not `admRulSeq` |
| Admin version | 행정규칙일련번호 | `ID` | `admRulSeq` |

List result `id` is merely a result ordinal. It is never canonical identity.
The client prefers JSON, supports XML fallback for malformed JSON, uses HTTPS,
30-second timeouts, retries transient failures twice with exponential delays and
at least 1.1 seconds between requests within each client. Automated production
runs use one collector at a time. Permission/auth failures are not retried.

Important live finding: Law.go.kr embeds the supplied OC credential in API detail
links. It must not be stored verbatim, even in ignored caches. The client replaces
credential occurrences before serialization or caching. The evidence index keeps
the original response SHA-256 and the stored redacted response SHA-256 separately.
This is credential-redacted raw evidence, not byte-exact original evidence; legal
metadata/body content is otherwise kept separately from normalization. Public
links are constructed from official serials, and any `OC` parameter is removed.

Never log exception objects from urllib; those may contain authenticated URLs.
Routine scripts suppress raw tracebacks. Public schemas exclude internal evidence,
filesystem paths and requests. `LAW_API_OC` is read only from the environment;
it is never included in browser or future Android code.

Deletion API documentation is internally inconsistent: URL/examples say `delHst`,
while one parameter table says `datDel`. Phase 0 verifies `delHst` live and records
the actual response. **API data deletion is not necessarily legal repeal.** Explicit
official repeal history associated with the same logical identity/version is
required for `RULE_REPEALED`; missing searches, deleted serials or list removals
are REVIEW or seed-removal events, never inferred repeal.

A PASS for deletion endpoint availability does not prove a repeal for any tracked
core item. Capability results identify which evidence was actually returned.

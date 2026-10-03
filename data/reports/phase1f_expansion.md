# PHASE 1F PRODUCTION EXPANSION

READY FOR WEB W4: YES

| Item | Result |
|---|---|
| schema | 1.4 |
| previous_core | 68 |
| approved_additions | 38 |
| final_tracked | 106 |
| current | 104 |
| historical_repealed | 2 |
| direct_corrections_added | 15 |
| cross_domain_added | 23 |
| api_trackable_production | 106 |
| api_limited_production | 0 |
| review_production | 0 |
| provenance_coverage | 106 |
| selection_basis_coverage | 106 |
| business_domain_coverage | 106 |
| domain_review_pending | 0 |
| lower_confidence_other | 7 |
| persistent_change_events | 120 |
| recent_90_day_events | 14 |
| events_with_comparison | 100 |
| events_with_changed_articles | 98 |
| comparison_unavailable | 20 |
| upcoming_events | 1 |
| first_run | CHANGED |
| second_run | NO_CHANGE |
| fail_closed | PASS |
| last_good | PASS |

## Report domain

- admrul-32484: 현황작성 및 보고요령 지침 → 보고
- admrul-51868: 교정본부 보고사무지침 → 보고

## Measured operation

| Run | API calls | Seconds | Retries | Result |
|---|---:|---:|---:|---|
| Expanded first | 128 | 154.625 | 0 | PUBLISHED |
| Unchanged second | 128 | 141.281 | 0 | NO_CHANGE |
| Local scheduled full audit | 238 | 262.656 | 0 | NO_CHANGE |

One-time new-38 backfill: 108 API calls, 124.812 seconds, 41 events, 29 predecessor pairs and 12 initial enactments.

Local scheduled entrypoint: full identity audit 106/106 PASS; independent page monitor error: NONE. This is not a hosted GitHub Actions execution.

Second run preserved all public bytes, mtimes, snapshot hashes and event IDs. Protected files: {"phase1d_evidence": 11, "old_event_details": 79, "archives": 170, "frontend": 23}; discrepancies: 0.

Backend tests: 130 PASS. Public JSON: 470 PASS. Secret leaks: 0. Removed appendices: 73.

Frontend modification: NO. Firebase deployed: NO. Existing immutable event envelopes remain 1.3; immutable archived snapshots remain 1.1.

Discovery cache stores only credential-free opaque page fingerprints and the pending approval queue in the existing workflow; see [official cache documentation](https://github.com/actions/cache).

## Primary domain distribution

- 인사·조직: 42
- 분류·가석방: 7
- 보고: 3
- 의료: 3
- 기타: 7
- 정보화: 1
- 인권·청원: 3
- 급식·복지: 12
- 작업·직업훈련: 7
- 수용·보안: 9
- 교육·교화: 4
- 보관금품: 1
- 민영교도소: 4
- 심리치료: 2
- 민원: 1

## Known limitations

- 20 events have no available predecessor/comparison; official omissions are preserved, with no fabricated differences.
- Backfill covers the recent 90-day window and current predecessor, not every historical revision.
- Administrative future versions are detected where the official stable-ID API exposes them; unpublished future versions cannot be exhaustively enumerated.
- 7 primary 기타 assignments have lower domain confidence; scope approval and API eligibility remain approved.
- Requested report-domain IDs have different official current titles; stable IDs and official titles are preserved.
- Opaque page hashes may change for non-regulation content, causing extra API discovery queries. No candidate is automatically admitted.
- Hosted GitHub Actions, Firebase deployment, Web W4 consumption and final unattended E2E have not been executed in this phase.

NEXT STEP: Web W4 schema 1.4 integration and final unattended-operation E2E.

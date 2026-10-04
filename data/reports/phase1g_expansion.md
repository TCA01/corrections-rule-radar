# PHASE 1G CRIMINAL PROCEDURE ACT EXPANSION

| Item | Result |
|---|---|
| schema | 1.4 |
| api_eligibility | PASS |
| official_title | 형사소송법 |
| canonical_id | law-001671 |
| current_mst | 290189 |
| current_effective_date | 2026-10-02 |
| promulgation_number | 22009 |
| promulgation_date | 2026-09-29 |
| scope_class | CROSS_DOMAIN_CORRECTIONS |
| selection_basis | 수용기록 업무에서 구속·영장·석방 등 형사절차 관련 사항 확인에 직접 활용되는 기본법 |
| business_domains | ['수용·보안'] |
| previous_tracked | 106 |
| added | 1 |
| final_tracked | 107 |
| current | 105 |
| historical | 2 |
| history_events_added | 32 |
| recent_events_added | 2 |
| old_new_comparison | PASS |
| first_run | CHANGED |
| second_run | NO_CHANGE |
| footer_old_copy | ABSENT |
| creator_credit | PASS |
| public_disclaimer | PASS |
| ready_for_unattended_operation | False |

## Operation

Before: 128 API calls, 141.281 seconds (Phase 1F unchanged run). After: 133 calls, 148.734 seconds, 0 retries. First successful expansion: 174.813 seconds.

Backend: 138 tests, pass=True; frontend: {'passed': 69, 'total': 69, 'success': True}; JSON: {'failed_files': [], 'status': 'PASS', 'validated_file_count': 536}; artifact: PASS; secret leaks: 0.

History: {'available_version_count': 58, 'max_pairs': 32, 'mode': 'ONE_TIME_BOUNDED_VERSION_HISTORY', 'older_versions_not_fetched': 25, 'selected_from': '2014-05-14', 'selected_to': '2027-12-31', 'selected_version_count': 32}. Sources: {'STRUCTURED_SNAPSHOT_DIFF': 22, 'LAWGO_OLD_NEW': 10}. Recent examples: [{"event_id": "evt-cc8e838fe28801579af71610df39e8edb49cfe8418196ac4f4eeb83307658b3b", "effective_date": "2026-10-02", "changed_article_count": 0, "comparison_source": "STRUCTURED_SNAPSHOT_DIFF", "official_source_url": "https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq=288579"}, {"event_id": "evt-014fc0c274f4110b3d823d51b98f1d6618b6a36f1e2cf460cf6cdb8b3c0a73c8", "effective_date": "2026-10-02", "changed_article_count": 93, "comparison_source": "STRUCTURED_SNAPSHOT_DIFF", "official_source_url": "https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq=290189"}].

All original 106 stable IDs and existing immutable events/archives are covered by regression fixtures. Second run has identical public bytes/mtimes, snapshot hashes and event IDs.

## Hosted operation

GitHub: {}

Live: {}

## Known issues

- One-time history backfill selects 32 of 58 listed versions plus their predecessor (25 earlier versions not fetched); normal sync does not crawl history.
- Official old/new pair/text unavailable for 22 selected events; full structured snapshot comparison is explicitly identified.
- Official department metadata is absent and remains null. No department or legal interpretation is invented.

Resolved initial validation failure: Initial publication rejected new discovery-source enum values; replaced with existing schema 1.4 values. Last-good remained intact.

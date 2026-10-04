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
| ready_for_unattended_operation | True |
| API CALLS | 128 → 133 (core sync); hosted normal run: 138 |
| RUNTIME | 141.281 → 148.734 seconds; first: 174.813; retries: 0 |
| BACKEND TESTS | 138 PASS |
| FRONTEND TESTS | 69 PASS |
| PUBLIC JSON | {'failed_files': [], 'status': 'PASS', 'validated_file_count': 536} |
| BUILD | PASS |
| SECRET LEAK | 0 |
| GITHUB NORMAL RUN | success |
| LIVE SCHEMA | 1.4 |
| LIVE RULE COUNT | 107 |
| LIVE 형사소송법 | PASS |
| LIVE HISTORY | PASS |
| LIVE FOOTER | PASS |

## Operation

Before: 128 API calls, 141.281 seconds (Phase 1F unchanged run). After: 133 calls, 148.734 seconds, 0 retries. First successful expansion: 174.813 seconds.

Backend: 138 tests, pass=True; frontend: {'passed': 69, 'total': 69, 'success': True}; JSON: {'failed_files': [], 'status': 'PASS', 'validated_file_count': 536}; artifact: PASS; secret leaks: 0.

History: {'available_version_count': 58, 'max_pairs': 32, 'mode': 'ONE_TIME_BOUNDED_VERSION_HISTORY', 'older_versions_not_fetched': 25, 'selected_from': '2014-05-14', 'selected_to': '2027-12-31', 'selected_version_count': 32}. Sources: {'STRUCTURED_SNAPSHOT_DIFF': 22, 'LAWGO_OLD_NEW': 10}. Recent examples: [{"event_id": "evt-cc8e838fe28801579af71610df39e8edb49cfe8418196ac4f4eeb83307658b3b", "effective_date": "2026-10-02", "changed_article_count": 0, "comparison_source": "STRUCTURED_SNAPSHOT_DIFF", "official_source_url": "https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq=288579"}, {"event_id": "evt-014fc0c274f4110b3d823d51b98f1d6618b6a36f1e2cf460cf6cdb8b3c0a73c8", "effective_date": "2026-10-02", "changed_article_count": 93, "comparison_source": "STRUCTURED_SNAPSHOT_DIFF", "official_source_url": "https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq=290189"}].

All original 106 stable IDs and existing immutable events/archives are covered by regression fixtures. Second run has identical public bytes/mtimes, snapshot hashes and event IDs.

## Hosted operation

GitHub: {"conclusion": "success", "createdAt": "2026-10-04T00:34:41Z", "event": "workflow_dispatch", "headSha": "79448b30987bcf8598919a017dabb6a265106c2b", "status": "completed", "updatedAt": "2026-10-04T00:44:01Z", "url": "https://github.com/TCA01/corrections-rule-radar/actions/runs/37165372288", "api_request_count": 138, "duration_seconds": 505.673744, "sync": {"api_request_count": 138, "api_response_seconds": 487.677279, "average_api_response_seconds": 3.533893, "dataset_version": "ds-ad3e2e2e1e7022e1725ced2003bb82c7ff4508408f1d9356218112235e66d590", "discovery_monitor_error": null, "duration_seconds": 505.673744, "error_summary": {}, "event_ids_identical": true, "failure_count": 0, "finished_at": "2026-10-04T00:43:20.528698+00:00", "last_good_dataset_version": "ds-ad3e2e2e1e7022e1725ced2003bb82c7ff4508408f1d9356218112235e66d590", "mode": "CORE_WITH_DAILY_DISCOVERY", "new_events": 0, "persistent_new_events": 0, "public_bytes_and_mtimes_identical": true, "public_page_request_count": 2, "public_page_response_seconds": 8.756176, "public_rewritten": false, "result": "NO_CHANGE", "retry_count": 1, "review_count": 0, "snapshot_hashes_identical": true, "started_at": "2026-10-04T00:34:54.854962+00:00", "success_count": 107, "total_http_request_count": 140, "transport_error_summary": {"NETWORK_ERROR": 1}}, "backend_tests": {"errors": 0, "failure_test_ids": [], "failures": 0, "passed": true, "public_contract": {"failed_files": [], "status": "PASS", "validated_file_count": 536}, "secret_scan": {"file_count": 0, "files": [], "status": "PASS"}, "tests": 138}, "normal_inputs": {"full_audit": false, "force_deploy": false}, "live_schema": "1.4", "resolved_count": 107, "frontend_tests_passed": true}

Live: {"checked_at": "2026-10-04T00:47:08.138912+00:00", "checked_public_files": [{"path": "/api/v1/manifest.json", "sha256": "8b003bf3b0b1efb3ea772a6518a8e784ae6bfd9754129ed98e09976244f713ca"}, {"path": "/api/v1/health.json", "sha256": "28415d97429d5d788ac5ab512aa1269bdfd7d2f024aad2c3225a7fa733cc1db6"}, {"path": "/api/v1/rules.json", "sha256": "984e4926763a2a43763a184450c0cfdf1f476230e4f453c13ce1783f6e744fa5"}, {"path": "/api/v1/rules/law-001671.json", "sha256": "53ac3e31254d4780f52f3c1d4134112b3a82c65d9f2fb599437412b99ad68263"}, {"path": "/api/v1/changes/history.json", "sha256": "b3af7a91872c820ce11943a94eb1ec80db41b2adb495af64ea509bc140477e34"}, {"path": "/api/v1/changes/recent.json", "sha256": "92477a3cf77531082381c13d4f84065feed370c5fd172db79d3d45eb6117cac4"}, {"path": "/api/v1/changes/upcoming.json", "sha256": "ad752ba04ff4a2274ebb905721934f82e222fa7a71856ded278b29dc8798a5ec"}, {"path": "/api/v1/changes/evt-cc8e838fe28801579af71610df39e8edb49cfe8418196ac4f4eeb83307658b3b.json", "sha256": "478df7259ac3cfb77dd4255ef4844f5e2587c0a0372db1ea782df30c8f0d5692"}, {"path": "/api/v1/rules/law-001671/versions/290189-2026-10-02-aa614223f4a01171.json", "sha256": "2ec9cb6787614a451301f2bc27cad9b4e09306173f36d782c926bc4dd1f5fdf3"}, {"path": "/api/v1/rules/law-001671/versions/288579-2026-10-02-9d5ac1ec88deb05f.json", "sha256": "a58bffc84ccf0c92e12912124492d1e87139ac37621baabd353cef1db841821a"}, {"path": "/api/v1/changes/evt-014fc0c274f4110b3d823d51b98f1d6618b6a36f1e2cf460cf6cdb8b3c0a73c8.json", "sha256": "f155e6687513bf4079f1c41401c132a4ad697d01be608a383074dcfde754dfa4"}, {"path": "/api/v1/rules/law-001671/versions/281865-2026-07-01-f6b1b1087cf9ecf9.json", "sha256": "87d15e65d9945d9c005eabc20bc0cfa0629aaa0bc2b5308523dc5ff5e50c3849"}, {"path": "/api/v1/rules/law-001671/versions/290189-2026-10-02-aa614223f4a01171.json", "sha256": "2ec9cb6787614a451301f2bc27cad9b4e09306173f36d782c926bc4dd1f5fdf3"}], "current": 105, "dataset_version": "ds-ad3e2e2e1e7022e1725ced2003bb82c7ff4508408f1d9356218112235e66d590", "historical": 2, "history_events": 32, "live_history": "PASS", "live_law": "PASS", "live_rule_count": 107, "live_schema": "1.4", "official_source_http_status": 200, "recent_article_counts": [0, 93], "recent_events": 2, "status": "PASS", "ui_checks": ["107 tracked rules", "single directory and global search match", "existing 수용·보안 filter", "current date and issue number 22009", "selection basis and three applies_to contexts", "three distinct future comparison tabs", "current July-to-October comparison: 93 articles", "two recent entries: 0 and 93 changed articles", "official source URL verified HTTP 200", "exact creator credit and subordinate personal-project disclaimer", "old footer description absent; source and legal notice retained"], "ui_status": "PASS", "url": "https://corrections-rule-radar.web.app"}

## Known issues

- One-time history backfill selects 32 of 58 listed versions plus their predecessor (25 earlier versions not fetched); normal sync does not crawl history.
- Official old/new pair/text unavailable for 22 selected events; full structured snapshot comparison is explicitly identified.
- Official department metadata is absent and remains null. No department or legal interpretation is invented.
- Hosted normal run recovered one transient NETWORK_ERROR with one retry; final review/failure count is zero.
- GitHub reported action-runtime deprecation and a forthcoming ubuntu-latest image migration; both are operational maintenance observations, not failures in this run.

Resolved initial validation failure: Initial publication rejected new discovery-source enum values; replaced with existing schema 1.4 values. Last-good remained intact.

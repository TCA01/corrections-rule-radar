# PHASE 1M — SCHEDULED RUN RELIABILITY

Audit cutoff: 2026-10-09 10:10:37 KST

EXPECTED SCHEDULES: 08:37 KST / 20:37 KST

| Expected slot KST | Run existed | Result | Run ID | Actual creation KST |
|---|---|---|---|---|
| 2026-10-07 08:37 | YES | FAILURE | 37563062041 | 2026-10-07 11:40:02 |
| 2026-10-07 20:37 | YES | FAILURE | 37663058212 | 2026-10-08 02:57:12 |
| 2026-10-08 08:37 | YES | FAILURE | 37719943653 | 2026-10-08 11:51:48 |
| 2026-10-08 20:37 | YES | FAILURE | 37820751430 | 2026-10-09 02:58:58 |
| 2026-10-09 08:37 | NO | MISSING | - | - |

MISSING is the state at the audit cutoff; it does not prove permanent cancellation or a disabled workflow.

| Run ID | Workflow / event | Created UTC / KST | Job started UTC / KST | Completed UTC / KST | Conclusion | Duration s | Head SHA |
|---|---|---|---|---|---|---|---|
| [37503211648](https://github.com/TCA01/corrections-rule-radar/actions/runs/37503211648) | Production regulation sync / schedule | 2026-10-06T17:23:46Z / 2026-10-07 02:23:46 | 2026-10-06T17:23:50Z / 2026-10-07 02:23:50 | 2026-10-06T17:35:03Z / 2026-10-07 02:35:03 | success | 677.0 | f1b7a6691c90e365495ff822b468ddd9be1d0044 |
| [37563062041](https://github.com/TCA01/corrections-rule-radar/actions/runs/37563062041) | Production regulation sync / schedule | 2026-10-07T02:40:02Z / 2026-10-07 11:40:02 | 2026-10-07T02:40:06Z / 2026-10-07 11:40:06 | 2026-10-07T02:49:27Z / 2026-10-07 11:49:27 | failure | 565.0 | d1fb756cd6909eededd82717f999b93759c1d017 |
| [37663058212](https://github.com/TCA01/corrections-rule-radar/actions/runs/37663058212) | Production regulation sync / schedule | 2026-10-07T17:57:12Z / 2026-10-08 02:57:12 | 2026-10-07T17:57:16Z / 2026-10-08 02:57:16 | 2026-10-07T18:04:30Z / 2026-10-08 03:04:30 | failure | 438.0 | d1fb756cd6909eededd82717f999b93759c1d017 |
| [37719943653](https://github.com/TCA01/corrections-rule-radar/actions/runs/37719943653) | Production regulation sync / schedule | 2026-10-08T02:51:48Z / 2026-10-08 11:51:48 | 2026-10-08T02:51:52Z / 2026-10-08 11:51:52 | 2026-10-08T03:04:38Z / 2026-10-08 12:04:38 | failure | 770.0 | d1fb756cd6909eededd82717f999b93759c1d017 |
| [37820751430](https://github.com/TCA01/corrections-rule-radar/actions/runs/37820751430) | Production regulation sync / schedule | 2026-10-08T17:58:58Z / 2026-10-09 02:58:58 | 2026-10-08T17:59:02Z / 2026-10-09 02:59:02 | 2026-10-08T18:11:24Z / 2026-10-09 03:11:24 | failure | 746.0 | d1fb756cd6909eededd82717f999b93759c1d017 |
| [37863901363](https://github.com/TCA01/corrections-rule-radar/actions/runs/37863901363) | Offline contract and artifact validation / push | 2026-10-09T00:16:12Z / 2026-10-09 09:16:12 | 2026-10-09T00:16:15Z / 2026-10-09 09:16:15 | 2026-10-09T00:18:52Z / 2026-10-09 09:18:52 | success | 160.0 | dea5cc0ce0bc4c796fb83c91c901d6ec634bca64 |
| [37863931848](https://github.com/TCA01/corrections-rule-radar/actions/runs/37863931848) | Production regulation sync / workflow_dispatch | 2026-10-09T00:16:33Z / 2026-10-09 09:16:33 | 2026-10-09T00:16:37Z / 2026-10-09 09:16:37 | 2026-10-09T00:28:43Z / 2026-10-09 09:28:43 | success | 730.0 | dea5cc0ce0bc4c796fb83c91c901d6ec634bca64 |
| [37865156917](https://github.com/TCA01/corrections-rule-radar/actions/runs/37865156917) | Production regulation sync / workflow_dispatch | 2026-10-09T00:30:45Z / 2026-10-09 09:30:45 | 2026-10-09T00:30:50Z / 2026-10-09 09:30:50 | 2026-10-09T00:43:47Z / 2026-10-09 09:43:47 | success | 782.0 | ffb83a1f1bc87042e77fc8784935960a6476ca53 |
| [37867303577](https://github.com/TCA01/corrections-rule-radar/actions/runs/37867303577) | Offline contract and artifact validation / push | 2026-10-09T00:56:34Z / 2026-10-09 09:56:34 | 2026-10-09T00:56:37Z / 2026-10-09 09:56:37 | 2026-10-09T00:59:25Z / 2026-10-09 09:59:25 | success | 171.0 | a60f627fba344ac2a445e5560867b901f1b84c94 |
| [37867380401](https://github.com/TCA01/corrections-rule-radar/actions/runs/37867380401) | Production regulation sync / workflow_dispatch | 2026-10-09T00:57:29Z / 2026-10-09 09:57:29 | 2026-10-09T00:57:39Z / 2026-10-09 09:57:39 | 2026-10-09T01:08:36Z / 2026-10-09 10:08:36 | success | 667.0 | a60f627fba344ac2a445e5560867b901f1b84c94 |

UI 2026-10-07 02:32 ORIGIN: run 37503211648, actual schedule event (`37 11 * * *`),
successful scan completed 2026-10-06T17:32:06.209233+00:00 UTC = 2026-10-07 02:32:06 KST.
It belongs to the October 6 20:37 slot and was delayed before run creation. The timezone conversion is correct.

ROOT CAUSE:

- One exact-ID collection review: CURRENT_NOT_CONFIRMED during official repeal transition.
- Three subsequent verified collections could not deploy because historical release tests froze live status counts at 105/2 (Phase1G) and 104/2 (Phase1F).
- The evening rehearsal exposed timestamp-only republication: a fresh Actions checkout restored stale private health, and sync compared its cached version instead of the published manifest. The dataset and legal events did not change. The generic baseline was corrected and a fresh-checkout regression test added.
- Scheduled dispatch was observed 3–6 hours after configured slots, before runner jobs started; underlying GitHub dispatch cause is not established.

SCHEDULE WORKFLOW ACTUALLY RUNNING: YES
LEGAL SCANS MISSED: YES; count 2 (1 incomplete collection, 1 scheduled slot not created at cutoff). Separately, 3 complete collections failed the publication gate.
OPS STATUS ONLY STALE: NO
TIMEZONE BUG: NO

Cron/default main/workflow enabled/production variable/concurrency/permissions were verified. No event-specific condition bypasses the schedule publication path.
NO_CHANGE updates the separate ops status and deploys its hash while retaining all legal bytes. The October 7 success proves that path already worked.

FIX APPLIED: fixed release-count assertions using exact-ID structured repeal evidence; kept exact approved tracking scope and original historical identities. Added optional ops trigger/run/last-scheduled provenance and a manual morning/evening policy rehearsal input. Fresh checkouts now compare legal version against the published manifest instead of stale private health. The timestamp-only republication time was corrected to the actual first legal publication, with retained run evidence. No timeout, retry, deadline or fail-closed rule was loosened.

The official API confirms admrul-35611, serial 2100000286404, 폐지, effective 2026-10-02. History and body agree. Therefore the observed live totals must become 107 tracked / 104 current / 3 repealed, rather than preserving the now-obsolete 105/2 observation.

OPS STATUS SEMANTICS: scheduled and manual results are distinguished; manual checks preserve the last real successful scheduled scan. Legacy origin annotation uses the actual uploaded report without changing timestamps.

NEXT SCHEDULE CONFIG: PASS (23:37 / 11:37 UTC). Delivery timing is best effort; this fix does not remove GitHub dispatch delays.
GitHub documents possible schedule delays/drops: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule

MANUAL SCHEDULE-POLICY REHEARSALS (actual workflow_dispatch events):

| Run ID | Policy | Result | Sync completed KST | API calls | Retries | Legal files rewritten | Deployment |
|---|---|---|---|---|---|---|---|
| 37863931848 | morning | PUBLISHED | 2026-10-09 09:25:39 | 140 | 0 | True | SUCCESS |
| 37865156917 | evening | PUBLISHED | 2026-10-09 09:40:47 | 134 | 0 | True | SUCCESS |
| 37867380401 | evening | NO_CHANGE | 2026-10-09 10:06:45 | 138 | 4 | False | SUCCESS |

LIVE HEADER:

법령·행정규칙 추적
교정관련 규정 추적기

교정업무에 관련된 법령·예규·훈령의 변경과 시행예정을 추적합니다.

최근 시스템 확인
2026.10.09 10:06 · 정상 · 수동 실행
변경 없음
최근 예약 확인: 2026.10.07 02:32
마지막 법령 데이터 반영: 2026.10.09 09:25
자동 확인 · 매일 08:37 · 20:37 (한국시간)
LIVE VERIFICATION:

```json
{
  "checked_at": "2026-10-09T01:10:23.251523+00:00",
  "counts": {
    "CURRENT": 104,
    "REPEALED": 3
  },
  "dataset_version": "ds-f5bde34929cfd8e03eac00f72b39863b25aad37a62f59abeb47ff3b29664ce9a",
  "last_scheduled_run_event_verified": "schedule",
  "official_repeal_body_matches": true,
  "ops": {
    "github_run_id": "37867380401",
    "last_good_dataset_version": "ds-f5bde34929cfd8e03eac00f72b39863b25aad37a62f59abeb47ff3b29664ce9a",
    "last_scan_completed_at": "2026-10-09T01:06:45.121999+00:00",
    "last_scan_current_count": 104,
    "last_scan_failures": 0,
    "last_scan_result": "NO_CHANGE",
    "last_scan_rule_count": 107,
    "last_scan_started_at": "2026-10-09T00:57:53.592489+00:00",
    "last_scan_status": "OK",
    "last_scheduled_scan": {
      "completed_at": "2026-10-06T17:32:06.209233+00:00",
      "cron": "37 11 * * *",
      "dataset_version": "ds-b1f5f18bf785019f3998a504462ac072e0b885a07f4da519a1a95d79289943a2",
      "github_run_id": "37503211648",
      "result": "NO_CHANGE",
      "started_at": "2026-10-06T17:24:14.430446+00:00"
    },
    "schedule_kst": [
      "08:37",
      "20:37"
    ],
    "schema_version": "1.5",
    "status_scope": "LAST_SUCCESSFUL_SCAN",
    "trigger": "MANUAL"
  },
  "published_at": "2026-10-09T00:25:23.666906+00:00",
  "run_id": 37867380401,
  "status": "PASS",
  "tracked": 107,
  "upcoming": [
    {
      "baseline": {
        "effective_date": "2026-10-02",
        "official_source_url": "https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq=290191",
        "snapshot_url": "/api/v1/rules/law-001668/versions/290191-2026-10-02-6f7111ef76469437.json",
        "version_id": "290191"
      },
      "canonical_id": "law-001668",
      "cumulative": 3,
      "date": "2026-12-24",
      "incremental": 3,
      "version_id": "280443"
    },
    {
      "baseline": {
        "effective_date": "2026-10-02",
        "official_source_url": "https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq=290189",
        "snapshot_url": "/api/v1/rules/law-001671/versions/290189-2026-10-02-aa614223f4a01171.json",
        "version_id": "290189"
      },
      "canonical_id": "law-001671",
      "cumulative": 3,
      "date": "2027-02-05",
      "incremental": 3,
      "version_id": "288579"
    },
    {
      "baseline": {
        "effective_date": "2027-02-05",
        "official_source_url": "https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq=288579",
        "snapshot_url": "/api/v1/rules/law-001671/versions/288579-2027-02-05-41d66ada95a4c1fa.json",
        "version_id": "288579"
      },
      "canonical_id": "law-001671",
      "cumulative": 5,
      "date": "2027-08-05",
      "incremental": 2,
      "version_id": "288579"
    },
    {
      "baseline": {
        "effective_date": "2027-08-05",
        "official_source_url": "https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq=288579",
        "snapshot_url": "/api/v1/rules/law-001671/versions/288579-2027-08-05-eec723645c81f23d.json",
        "version_id": "288579"
      },
      "canonical_id": "law-001671",
      "cumulative": 6,
      "date": "2027-12-31",
      "incremental": 1,
      "version_id": "281865"
    }
  ]
}
```

FINAL CHECKS:

LEGAL DATA MODIFIED: YES
OPS STATUS SEMANTICS: PASS
NEXT SCHEDULE CONFIG: PASS
MANUAL POLICY REHEARSALS COMPLETED: [37863931848, 37865156917, 37867380401]
REAL NO_CHANGE REHEARSAL: [37867380401]
LEGAL BYTE / SNAPSHOT / FUTURE PRESERVATION: PASS
TESTS: backend 173 PASS; hosted frontend 102 PASS; local frontend including Phase1L audit 213 PASS; typecheck/build/artifact PASS; secret leak 0.
NEXT REAL SCHEDULED SUCCESS VERIFIED: NO
READY FOR UNATTENDED TWICE-DAILY OPERATION: NO

A readiness NO while the next real scheduled event is unconfirmed is a conservative acceptance decision. Manual production recovery and repeated NO_CHANGE do not relabel a manual event as a schedule success. The actual post-fix schedule still needs observation.

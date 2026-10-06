# PHASE 1K OPS + SOURCE LINK + CHANGE COUNT AUDIT

## 1. OPS STATUS

LAST SUCCESSFUL SCAN: 2026-10-06 19:41:40 KST

LAST SCAN RESULT: NO_CHANGE; 107 success, 0 failure, 0 retry, 0 new events.

LAST LEGAL DATA UPDATE: 2026-10-06 18:59:24 KST. The first scan found actual new versions for admrul-29857 (2100000286176) and admrul-35611 (2100000286360); the following local and GitHub scans preserved this dataset.

SCHEDULE DISPLAY: PASS — 08:37 / 20:37 KST.

NO_CHANGE LEGAL DATA PRESERVED: PASS — local independent bytes, mtimes, snapshot set and event fingerprints; GitHub commit range b544413..a88ca81 changes only ops-status.json and the deployment marker.

OPS STATUS UPDATED ON NO_CHANGE: PASS — normal workflow, force_deploy=false; hosted status matched local status before acknowledgment.

Dataset: ds-b1f5f18bf785019f3998a504462ac072e0b885a07f4da519a1a95d79289943a2

## 2. DIRECTORY COUNT

TRACKED TOTAL: 107

CURRENT: 105

HISTORICAL/REPEALED: 2

EXCLUDED TWO IDS/TITLES:

- admrul-26424 — 교정기관 간판게시 및 교정직제 영문표기에 관한 지침
- admrul-26917 — 교정공무원 예절 규정

DIRECTORY DEFAULT COUNT: 105

DIRECTORY WITH HISTORICAL: 107

COUNT UX: PASS — live default/include/search 105/107/1; local domain medical 7 and automated zero-result filtering also verified.

## 3. EFFECTIVE-DATE SOURCE LINKS

CURRENT LINK: PASS — https://www.law.go.kr/LSW/lsInfoP.do?efYd=20261002&lsiSeq=290189

2027-02-05 LINK: PASS — https://www.law.go.kr/LSW/lsInfoP.do?efYd=20270205&lsiSeq=288579

2027-08-05 LINK: PASS — https://www.law.go.kr/LSW/lsInfoP.do?efYd=20270805&lsiSeq=288579

2027-12-31 LINK: PASS — https://www.law.go.kr/LSW/lsInfoP.do?efYd=20271231&lsiSeq=281865

EACH OPENS CORRECT EFFECTIVE STATE: PASS — all four official visible effective dates checked. Live incremental and cumulative header/footer links match selected after-state.

ADMIN RULE LINK REGRESSION: PASS — every tracked administrative rule URL preserved in frontend tests; appendix/mobile cases pass.

## 4. CRIMINAL PROCEDURE ACT AUDIT

OFFICIAL PAGE COMPARISON SEMANTICS: PROMULGATION_UNIT

A BEFORE STATE: 2026-10-02 / MST 290189 / law 22009 / 617 articles.

B 2027-02-05 STATE: 2027-02-05 / MST 288579 / law 21857 / 617 articles.

A->B CHANGED COUNT: 3

A->B CHANGED ARTICLES: 197의4, 260, 261 (keys 0197041, 0260001, 0261001).

OFFICIAL PROMULGATION-UNIT CHANGED COUNT: 97 distinct main-body article numbers. Official comparison metadata pairs MST 281865 with 288579. Independent whole-promulgation comparison yields the identical 97-key set.

WHY COUNTS DIFFER: The promulgation comparison spans changes already reflected by the current effective state and later stages: 91 already reflected by October 2, 3 at February 5, 2 at August 5, and article 199의2 classified separately for institution-dependent commencement. All four effective API bodies already contain the same article 199의2 text; its addendum conditions cannot be represented as a new textual delta. Article 245의12 also has a later current-law correction in law 22009. December's article 59의3 belongs to law 21241, not this 97-article law 21857 comparison. No inferred legal applicability was inserted into production counts.

IS CURRENT "3 ARTICLES" CORRECT: YES, as a structured full-text effective-state delta.

2027-02-05: incremental 3; cumulative 3.

2027-08-05: incremental 2 (220의2, 244의6); cumulative 5.

2027-12-31: incremental 1 (59의3); cumulative 6.

SAME MST MULTI-EFFECTIVE SUPPORT: PASS — MST 288579 plus efYd selects separate structured effective states: February 617 articles, August 619. Distinct body hashes; not deduplicated by MST alone.

Complete normalized before/after hashes and the 97-article classification are in [comparison audit](phase1k_comparison_audit.md) and [structured evidence](phase1k_comparison_audit.json).

## 5. REGRESSION

BACKEND: 169 PASS, locally and GitHub.

FRONTEND: 99 PASS, locally and GitHub; 15 responsive browser cases PASS.

PUBLIC JSON: 543 PASS; 107 rules, schema 1.5 retained.

BUILD: PASS; 546 artifact files verified.

SECRET SCAN: PASS, 0 leaks.

GITHUB REAL RUN: PASS — [37450848479](https://github.com/TCA01/corrections-rule-radar/actions/runs/37450848479), 8m31s. Sync 323.36s, 137 API requests, 0 retries. Existing discovery monitoring additionally used 2 public-page requests; legal comparisons remain structured-API based.

LIVE VERIFY: PASS — public manifest/health/rules dataset and ops payload verified; live header and all six future comparison modes inspected. Hosting acknowledged at 2026-10-06 19:44:31 KST with no pending deployment.

READY: YES

Feature commit: b544413. Hosting acknowledgment: a88ca81. Existing user modification to phase1g_legacy_rehearsal.json preserved and excluded from commits.

# Phase 1I audit: official comparison shorthand

Result: COMPARISON PLACEHOLDER. Did legal text literally change from 생략 to 현행과 같음? **NO**.

Event: `evt-18869ca99f3cd419ad147adad5289d1a1bda797251272ac8c0d23a5df75e89be`
Source: `LAWGO_ADMIN_OLD_NEW` / `OFFICIAL_COMPARISON_EXCERPT`.

Official cached JSON: `data/raw_cache/phase1e/9e2ab1b2cb6598f0357fe3151b7652bcd529f2e55280cdb23631d32c3214e143.json`.
Stored raw SHA-256: `7d59a0e069a5e20a3634d9cf4b7d26dca698d57b3c83a211eb91befe5da8e4a9` (verified against stored bytes).
Official old/new payload article 14 values match the persistent event excerpt exactly after presentation-tag removal.

## A. Official comparison old-side value

```text
제14조(교육면제) ① 소장은 수형자가 다음 각 호의 어느 하나에 해당하는 경우에는 교육을 면제할 수 있다.
1. ∼ 3. (생  략)
4. 심리치료프로그램 대상자 중 집중인성교육 기본교육 수료 기준시간 이상의 교육을 이수한 자
5. ∼ 7. (생  략)
② (생  략)
③ 면제자의 경우에도 본인의 신청에 의해 기본교육과 형기주기별 재교육을 이수할 수 있다.
```

## B. Official comparison new-side value

```text
제14조(교육면제) ① 소장은 수형자가 다음 각 호의 어느 하나에 해당하는 경우에는 교육을 면제할 수 있다.
1. ∼ 3. (현행과 같음)
5. ∼ 7. (현행과 같음)
② (현행과 같음)
③ 면제자의 경우에도 본인의 신청에 의해 기본교육과 재교육을 이수할 수 있다.
```

## C. Structured BEFORE

Version: `2100000220728`; effective date: `2023-03-14`.
Snapshot: `/api/v1/rules/admrul-37584/versions/2100000220728-2023-03-14-08db07148c7c6f6d.json`.

```text
제14조(교육면제) ① 소장은 수형자가 다음 각 호의 어느 하나에 해당하는 경우에는 교육을 면제할 수 있다.1. 65세 이상인 자2. 노역장 유치자3. 외국인4. 심리치료프로그램 대상자 중 집중인성교육 기본교육 수료 기준시간 이상의 교육을 이수한 자5. 삭제6. 정신적ㆍ신체적 장애, 질병 등으로 교육이 부적합하다고 인정되는 자7. 기타 교육 분위기를 저해할 우려가 있는 자② 소장은 제1항 제6호 및 제7호에 해당하는 경우에는 집중인성교육 면제자 및 면제사유를 교정정보시스템에 입력ㆍ관리하여야 한다.③ 면제자의 경우에도 본인의 신청에 의해 기본교육과 형기주기별 재교육을 이수할 수 있다.
```

## D. Structured AFTER

Version: `2100000285778`; effective date: `2026-10-02`.
Snapshot: `/api/v1/rules/admrul-37584/versions/2100000285778-2026-10-02-baa1be95e79d6240.json`.

```text
제14조(교육면제) ① 소장은 수형자가 다음 각 호의 어느 하나에 해당하는 경우에는 교육을 면제할 수 있다.1. 65세 이상인 자2. 노역장 유치자3. 외국인4. 삭제5. 삭제6. 정신적ㆍ신체적 장애, 질병 등으로 교육이 부적합하다고 인정되는 자7. 기타 교육 분위기를 저해할 우려가 있는 자② 소장은 제1항 제6호 및 제7호에 해당하는 경우에는 집중인성교육 면제자 및 면제사유를 교정정보시스템에 입력ㆍ관리하여야 한다.③ 면제자의 경우에도 본인의 신청에 의해 기본교육과 재교육을 이수할 수 있다.
```

## Correct presentation

The structured old body contains item 4 심리치료프로그램 대상자... and item 5 삭제. The structured new body contains item 4 삭제 and item 5 삭제. Paragraph 3 removes 형기주기별 before 재교육. Items 1–3, 5–7 and paragraph 2 remain substantive context, with no shorthand placeholders.

The source adapter uses only the event’s exact before/after snapshot references, checks canonical ID, identifier, effective date and body hash, and selects article numbers from official comparison metadata. It supplies full legal text to both unified and split rendering. Equal full article texts are excluded from visual changes; missing or mismatched snapshots produce explicit unavailability, never a shorthand word diff. Literal 생략 and 삭제 in structured bodies are preserved.

The official event selected 23 articles; full-text visual comparison contains 21. Full-text unchanged article numbers: 26, 27. Persistent event counts and raw excerpts remain immutable provenance.

No public contract/data mutation: schema 1.5, all 107 rules, all event IDs and archives are preserved. The resolver is in the client data/source adapter, not in the word-diff rendering logic. Android consumers can implement the same adapter against the existing archive contract. No law-specific production conditional or LLM is used.

## Browser regression

`tests/browser/phase1i.cua.mjs` runs the deleted appendix, all 59 long appendices and article 14 comparison cases at 360, 390, 412 and 1280px through the supported cua browser API. It measures title/action rectangles, scroll widths, mobile inline token rectangles, 44px touch targets, deleted-link safety and real substantive highlights. Mobile-only whitespace breaking removes hanging spaces; desktop horizontal layout remains.

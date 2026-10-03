# 관련 업무 분야

data/registry/business_domains.json contains all 106 identities/names, primary and
secondary domains, review status and official evidence. The 16 controlled
categories come from data/seed/business_domains.json.

Review connects title, official department, purpose/scope, headings and selected
supporting articles. Historical official scope is retained for repealed rules.
CODEX_EVIDENCE_REVIEW means source-backed information classification, not agency
or human business-owner approval or legal interpretation. Department alone is
not proof. Mappings are not exhaustive legal scope determinations.

Phase 1F classifies all 106. The product owner approved the new 보고 domain for
admrul-32484 (현황작성 및 보고요령 지침) and admrul-51868 (교정본부 보고사무지침).
They are no longer domain-review cases. New facility/construction topics use 기타
with separately reported lower confidence. A changed or missing assignment basis
automatically uses 기타 with domain_assignment_status=FALLBACK and an internal
report; approved API tracking continues without periodic human maintenance.

Primary counts sum to classified rules; combined membership counts include
secondary domains and may exceed 106. Always distinguish these counts.

Future UI label: **관련 업무 분야**. Detect and organize official changes and
provide official references. Never assert that a detected change necessarily
requires a particular work action or issue legal interpretation.

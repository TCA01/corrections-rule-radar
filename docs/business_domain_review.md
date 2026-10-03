# 관련 업무 분야

data/registry/business_domains.json contains all 68 identities/names, primary and
secondary domains, review status and official evidence. The 15 controlled
categories come from data/seed/business_domains.json.

Review connects title, official department, purpose/scope, headings and selected
supporting articles. Historical official scope is retained for repealed rules.
CODEX_EVIDENCE_REVIEW means source-backed information classification, not agency
or human business-owner approval or legal interpretation. Department alone is
not proof. Mappings are not exhaustive legal scope determinations.

66 rules are classified. Broad 현황작성 및 보고요령 지침 and 교정본부 보고사무지침
remain REVIEW with null primary and empty secondary fields pending work-owner
review. REVIEW never hides a rule. Any official name/metadata/body hash change
invalidates classification until reviewed again. Future versions may need separate
business review.

Primary counts sum to classified rules; combined membership counts include
secondary domains and may exceed 68. Always distinguish these counts.

Future UI label: **관련 업무 분야**. Detect and organize official changes and
provide official references. Never assert that a detected change necessarily
requires a particular work action or issue legal interpretation.

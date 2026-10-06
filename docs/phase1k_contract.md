# Phase 1K contract review

API schema remains 1.5. The additive `ops-status.json` endpoint describes the
LAST_SUCCESSFUL_SCAN, independently of the legal dataset. Existing schemas and
legal bytes are unchanged. The candidate lock includes its new schema.

NO_CHANGE means no legal dataset change. The isolated worker must still preserve
every legal JSON byte, snapshot, event, and dataset version. After validation and
promotion, the supervisor atomically replaces only the operational status file.
A failed/incomplete attempt does not replace the last successful public scan.
Private operational reports retain failed attempts. The public header explicitly
describes the most recent successful confirmation, not a real-time guarantee.

Each successful scan requires a Hosting release even on NO_CHANGE. The deployment
marker separately tracks the ops file SHA-256; a committed but undeployed status
remains pending. Release verification checks the hosted ops content before ack.
The schedule remains 23:37/11:37 UTC = 08:37/20:37 KST.

The canonical frontend source builder uses official version_id/lsiSeq and the
selected effective date for statutes. Administrative rules and appendix download
URLs retain their supplied official addresses. Missing statute identifiers fall
back to the supplied official URL, or the official homepage if unavailable; no
identifier is inferred from a title. A future comparison's header, footer, and
comparison link all refer to its selected after-state, including cumulative mode.
Appendix links remain tied to their current-version metadata and deletion state.

Independent audit: `scripts/audit_phase1k.py` fetches current/future structured
states only into private staging. `--package` fetches promulgation bodies;
`--crosscheck` groups official comparative rows. No audit path publishes data.
The 97 distinct main-body article numbers in law 21857's comparison match an
independent whole-promulgation full-body diff. They are not 97 changes at February's
effective transition. The effective-body chain reproducibly has 3/2/1 new changes
and 3/5/6 cumulative changes, with complete per-article hashes in the audit report.

Scope caveat: Article 199-2 is already textual content in all four official API
states but its addendum has institution-dependent commencement. Text-difference
counts cannot represent every legal applicability transition. It is classified
separately as staged in the audit; no inferred applicability is injected into
production counts. Addendum amendments to other statutes are not counted as
Criminal Procedure Act main-body article numbers. December article 59-3 belongs
to law 21241, not law 21857. The September law 22009 is the actual current baseline.

No legal interpretation or generative AI is used in production comparison.

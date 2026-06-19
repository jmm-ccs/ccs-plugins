---
name: claim-supplement-generator
description: DEPRECATED. This skill has been replaced by claim-audit-finalizer (final-delivery flow — Sanity Audit, XLSX export, invokes the estimate markup) and claim-pdf-annotator (the audit's end deliverable — a marked-up copy of the carrier's estimate with CCS's edits applied in-line). Do not invoke this skill. Invoke claim-audit-finalizer for end-of-audit closing, or claim-pdf-annotator for a fresh marked-up estimate.
---

# DEPRECATED — claim-supplement-generator

This skill is no longer in use. Its job was split across the final-delivery skills, and the audit's deliverable has since become a marked-up copy of the carrier's estimate.

**Replacements:**

- [`claim-audit-finalizer`](../claim-audit-finalizer/SKILL.md) — end-of-audit closing flow. Runs the Supplement Sanity Audit, gathers user dispositions on flagged entries, exports the suggestion list to XLSX, invokes `claim-pdf-annotator` to produce the marked-up estimate, then runs a final fact-check across the deliverables.
- [`claim-pdf-annotator`](../claim-pdf-annotator/SKILL.md) — the audit's end deliverable. Reads the suggestion list and the carrier estimate and produces a marked-up copy of the carrier's estimate: the full estimate reproduced, with CCS's edits applied in place (changed values and new lines in green, a justification box beneath every change). Callable any time during or after the audit to get a current snapshot.
- [`claim-supplement-package`](../claim-supplement-package/SKILL.md) — the legacy Word supplement document (cover letter, Alignment Summary, line-item alignments per the project's Sample Supplement). Superseded by the marked-up estimate; kept only for projects that specifically want that document.

This file can be safely deleted from the plugin. It is left in place only so any reference to `claim-supplement-generator` from older skills or chats lands on this redirect rather than failing silently.

---
name: claim-supplement-generator
description: DEPRECATED. This skill has been replaced by claim-audit-finalizer (final-delivery flow — Sanity Audit, XLSX export, invokes the annotator and the supplement package) and claim-supplement-package (the document deliverable — cover letter, Alignment Summary, and line-item alignments per the project's Sample Supplement). Do not invoke this skill. Invoke claim-audit-finalizer for end-of-audit closing, claim-supplement-package for the supplement document, or claim-pdf-annotator for a fresh annotated PDF.
---

# DEPRECATED — claim-supplement-generator

This skill is no longer in use. Its job was split across the final-delivery skills; the document deliverable it used to produce now lives in `claim-supplement-package`, rebuilt on the suggestion-list architecture.

**Replacements:**

- [`claim-audit-finalizer`](../claim-audit-finalizer/SKILL.md) — end-of-audit closing flow. Runs the Supplement Sanity Audit, gathers user dispositions on flagged entries, exports the suggestion list to XLSX, invokes `claim-pdf-annotator` and `claim-supplement-package`, then runs a final fact-check across all the deliverables.
- [`claim-supplement-package`](../claim-supplement-package/SKILL.md) — the supplement document: cover letter (verbatim from the project's Sample Supplement, info swapped), Alignment Summary, and line-item alignments in the sample's format, built from the `Agreed` suggestion-list entries.
- [`claim-pdf-annotator`](../claim-pdf-annotator/SKILL.md) — on-demand utility. Reads the suggestion list and the carrier PDF, produces an annotated copy of the PDF with each suggestion-list suggestion attached as a PDF comment. Callable any time during or after the audit to get a current snapshot.

This file can be safely deleted from the plugin. It is left in place only so any reference to `claim-supplement-generator` from older skills or chats lands on this redirect rather than failing silently.

---
name: claim-supplement-generator
description: DEPRECATED. This skill has been replaced by claim-audit-finalizer (final-delivery flow — Sanity Audit, XLSX export, invokes the annotator) and claim-pdf-annotator (on-demand utility that produces the annotated carrier PDF). The old supplement-generator produced a Word-doc supplement for the carrier; that workflow is gone — CCS now builds the carrier-facing supplement in Xactimate directly. Do not invoke this skill. Invoke claim-audit-finalizer for end-of-audit closing, or claim-pdf-annotator any time you want a fresh annotated PDF.
---

# DEPRECATED — claim-supplement-generator

This skill is no longer in use. The carrier-facing-supplement workflow has been removed because CCS builds that supplement in Xactimate directly, drawing from Claude's audit deliverables.

**Replacements:**

- [`claim-audit-finalizer`](../claim-audit-finalizer/SKILL.md) — end-of-audit closing flow. Runs the Supplement Sanity Audit, gathers user dispositions on flagged entries, exports the suggestion list to XLSX, invokes `claim-pdf-annotator` to produce the annotated carrier PDF, then runs a final fact-check across all three artifacts. This is the closest match to what the old `claim-supplement-generator` did.
- [`claim-pdf-annotator`](../claim-pdf-annotator/SKILL.md) — on-demand utility. Reads the suggestion list and the carrier PDF, produces an annotated copy of the PDF with each suggestion-list suggestion attached as a PDF comment. Callable any time during or after the audit to get a current snapshot.

This file can be safely deleted from the plugin. It is left in place only so any reference to `claim-supplement-generator` from older skills or chats lands on this redirect rather than failing silently.

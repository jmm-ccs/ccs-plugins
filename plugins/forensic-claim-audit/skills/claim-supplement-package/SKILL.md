---
name: claim-supplement-package
description: Final-delivery deliverable of the CCS forensic claim audit. Generates the ready-to-upload supplement package — a Word document with a cover letter duplicating the project's Sample Supplement (contractor/adjuster/policyholder info swapped), an Alignment Summary based on the sample, and line-item alignments in the sample's exact format — built from the Agreed entries in the suggestion list after the Sanity Audit. Trigger when the user says "generate the supplement package," "produce the supplement document," "build the cover letter and alignments," or as Phase 3b of claim-audit-finalizer. Requires the Sample Supplement file in the project folder.
---

# Claim Supplement Package (Final-Delivery Deliverable)

Goal: produce the "ready-to-upload" supplement document from the original CCS output process — written from the contractor, following the format of the project's Sample Supplement — generated from the suggestion list after the Sanity Audit has locked it in.

This is the document deliverable that travels with the Xactimate supplement. CCS still builds the line-item estimate itself in Xactimate from the XLSX; this package is the formatted document — cover letter, Alignment Summary, line-item alignments — that presents those corrections to the carrier.

## Step 0 — Read the protocols

Use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read the entire file end-to-end before doing anything else. Do this every time this skill is invoked. Critical here: §1.1 (the package contains nothing the suggestion list doesn't), §1.4 (every number copied verbatim, no recomputation drift), §1.5 (each alignment carries its plain-language Why + Source), §2.3 (labeling rules — `b`/`c`/`d`, `Supp-1a`, `Supp-New`), §2.11 (bilingual mode), and §9 (voice).

## Prerequisite

The Sanity Audit (Phase 1 of `claim-audit-finalizer`) has run, so the suggestion list reflects locked-in decisions. If the finalizer hasn't run, tell the user this package is built from the post-Sanity-Audit list and route them to `claim-audit-finalizer` first — generating it from an un-sanity-checked list produces a document CCS can't send.

## Inputs

- **The Sample Supplement** — the example supplement in the project folder (labeled as a sample; the format template for everything this skill produces). `Read` it in full. If it's missing, describe it plainly per §9.7 (an example supplement document — the model for the cover letter's wording, the Alignment Summary's categories, and the layout of the line-item alignment pages), ask the user to drop it in the project folder, and stop.
- **The suggestion list** — `Read` `outputs/audit-suggestion-list.md`. Only entries with disposition `Agreed` go into the package (`Halted` and `Needs-info` entries are unresolved and never appear in a carrier-facing document).
- **The carrier PDF** — `Read` it for the claim, policyholder, and adjuster information and for the carrier line items the alignments reference.
- **Project info for the cover letter** — contractor information (name, license, contact), adjuster information, policyholder information. Pull from the project files (carrier PDF header, contract/AOB, contractor SOW, correspondence). Anything you cannot find in a named file: use `AskUserQuestion` to get it from the user. Never invent or guess a name, license number, address, or claim number (§1).

## The package — three parts, all following the sample

Build the document with the `docx` skill, saved as `outputs/supplement-package.docx`.

### Page 1 — Cover letter

Duplicate the form and verbatim content of the Sample Supplement's cover letter **exactly**, changing only: contractor information, adjuster information, and policyholder/project information, swapped to the current project's values. No other wording changes — not a synonym, not a reordering. After building it, verify: the letter diffs against the sample's letter only at the swapped fields. If any other text differs, fix it before continuing.

### Page 2 — Alignment Summary

Based on the sample's Alignment Summary:

- Keep the sample's categories that apply to this project, using the sample's exact category titles.
- Delete categories with no corresponding Agreed entries; add categories where this project's Agreed entries need one, titling them in the same format as the sample's.
- Under each category, the supporting examples come from this project's Agreed entries — adjusted to reflect the current project, never carried over from the sample's claim.

### Additional pages — Line-item alignments

One alignment per Agreed entry, in the **exact format of the sample's alignment pages**. Each alignment carries, from the suggestion list verbatim:

- The carrier line reference (item number + title exactly as the carrier PDF has them) and the Carrier Estimate Protocol label (`b`/`c`/`d`, `Supp-1a/b`, `Supp-New`)
- The proposed change (quantities, units, prices, M/E/L — copied byte-for-byte from the list; this skill recomputes nothing)
- The justification: the entry's plain-language Why + Source from the Supporting evidence field (§1.5)

Order the alignments by carrier line item number (with `Supp-New` rooms/categories at the end, per §2.3's labeling rules). If the sample orders differently, follow the sample.

## Integrity checks before delivery

1. **Coverage** — count Agreed entries in the list and alignments in the document via `bash`; the counts must match. No entry skipped, none added.
2. **Verbatim numbers** — spot-check three entries: every figure in the document matches the suggestion list exactly.
3. **Cover letter diff** — re-verify the letter matches the sample apart from the swapped info blocks.
4. **No orphan content** — nothing appears in the package that isn't traceable to the sample (format/wording) or the suggestion list (substance).

If any check fails, fix and re-run the checks. Then report the file path and the entry count (with §1.4 provenance for the count).

## Bilingual mode (§2.11)

If `**Languages:**` in `outputs/audit-progress.md` is `English + Spanish`, also produce `outputs/supplement-package-es.docx` from the Spanish suggestion list (`outputs/audit-suggestion-list-es.md`) — same structure, numbers and carrier-line references byte-for-byte identical, descriptive prose in Spanish. The English package is unchanged, and the cover letter is translated only if the user confirms they want a Spanish cover letter; otherwise the Spanish package reuses the English letter.

## Re-running

The package can be regenerated any time after the Sanity Audit (e.g., a disposition changed, a HALT correction landed). Regenerate the whole document from the current list — never hand-patch the docx — and re-run the integrity checks.

## What this skill does NOT do

- Does not run the Sanity Audit, gather dispositions, or modify the suggestion list (that's `claim-audit-finalizer`).
- Does not produce the Xactimate estimate — CCS builds that from the XLSX.
- Does not include `Halted` or `Needs-info` entries.
- Does not change, summarize, or "improve" the sample's wording or the suggestion list's numbers.

## Related skills

- `claim-audit-finalizer` — runs the Sanity Audit, then invokes this skill as Phase 3b of final delivery.
- `claim-suggestion-list-export` — the Agreed-only XLSX working set; the same entries this package formats.
- `claim-pdf-annotator` — the annotated carrier PDF; the third deliverable alongside the XLSX and this package.
- `claim-project-inventory` — flags a missing Sample Supplement before the audit starts.

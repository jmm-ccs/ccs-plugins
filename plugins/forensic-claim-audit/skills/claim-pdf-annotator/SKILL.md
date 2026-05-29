---
name: claim-pdf-annotator
description: On-demand utility for the CCS forensic claim audit. Reads the suggestion list and the carrier PDF, then produces an annotated copy of the PDF with each suggestion-list suggestion attached as a PDF comment at the location of the carrier line item it modifies. Trigger any time the user says "annotate the PDF," "show the suggestions on the PDF," "give me a current PDF snapshot of the audit," "produce the marked-up estimate," or whenever they want the suggestion list visualized on the carrier estimate. Can be called mid-audit for a snapshot or at final delivery — the skill is independent of any other audit stage.
---

# Claim PDF Annotator (On-Demand Utility)

Goal: take the current state of the suggestion list and produce an annotated copy of the carrier PDF with each suggestion placed as a comment at the corresponding carrier line item.

This skill does **not** run the Sanity Audit, does not gather dispositions, and does not export the XLSX. It only annotates the PDF. It can be invoked at any point in an audit (mid-audit for a snapshot, at final delivery for the deliverable, or any other time the user wants the suggestion list visualized on the carrier estimate).

For the final-delivery flow that runs the Sanity Audit and exports the XLSX, see `claim-audit-finalizer`.

## Step 0 — Read the protocols

Use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read the entire file end-to-end before doing anything else. Do this every time this skill is invoked. The Carrier Estimate Protocol (§2.3, including the suggestion-list spec and Sub-Item Numbering Conflicts) and Output Integrity (§1.1) are critical here — comments on the PDF use the suggestion list's own wording and never add content the suggestion list doesn't have.

## Inputs

- **The suggestion list** — `Read` `outputs/audit-suggestion-list.md` (in the project folder)
- **The carrier PDF** — `Read` it (will be duplicated; the original stays untouched)

If either is missing, use `AskUserQuestion` to gather the path and stop until provided.

## Method

1. **Duplicate the carrier PDF.** Use the `pdf` skill to make a copy at `outputs/[carrier-pdf-name]-annotated.pdf`. Never modify the original.

2. **Walk the suggestion list.** For each entry:
   - **Include every entry** in the suggestion list. The only dispositions are `Agreed`, `Halted`, and `Needs-info`; tag each comment with its disposition (below) so the snapshot shows the full current state. There is nothing to skip — rejected suggestions are never added to the list, so they aren't here.

3. **Locate each carrier line item** in the duplicate PDF using the entry's **Carrier line** field (item number + the title exactly as the PDF has it). If the line cannot be found, do not invent a location — flag the entry to the user as "could not locate on PDF" and skip it.

4. **Attach a PDF comment** at the located line. Comment text:
   - **Disposition** (`Agreed` / `Halted` / `Needs-info`) — as the first line, so it's visible at a glance
   - **Suggestion type** (Add / Correct / Flag)
   - **Label** per Carrier Estimate Protocol (`b`/`c`/`d` ancillary letter, `Supp-1a/b` for sub-letter conflicts, or `Supp-New`)
   - **Proposed change** (the fields and values from the suggestion list)
   - **Number provenance** (per §1.4 — the calculated-or-copied breakdown)
   - **Supporting evidence** (the plain-language Why + named source files, per §1.5 — this is the reviewer-facing reason and evidence; copy it verbatim so the comment explains, in basic language, why the suggestion exists and which file backs it)

5. **Save** the annotated PDF as `outputs/[carrier-pdf-name]-annotated.pdf`. Report to the user how many comments were placed and how many entries (if any) could not be located.

## What this skill does NOT do

- Does not run the Sanity Audit (that's `claim-audit-finalizer`)
- Does not gather user dispositions on flagged items (that's `claim-audit-finalizer`)
- Does not export the suggestion list to XLSX (that's `claim-audit-finalizer`)
- Does not modify the suggestion list itself (that happens in the audit stages and the finalizer)

## Output

Short confirmation in chat — no 4-section response. The message includes:

- The saved file's path (`outputs/[carrier-pdf-name]-annotated.pdf`).
- How many suggestions made it onto the PDF.
- If any entries couldn't be located, each one as:
  - Its suggestion number,
  - The suggestion's one-line summary plus the Carrier line text it was trying to anchor against,
  - A note to point you at the right line so you can re-run.

If every entry landed, the message is one sentence (path + count). If some didn't, that sentence plus a list of the missed ones. Missed entries are never identified by number alone — the auditor needs enough context to fix them without opening the suggestion list.

## Re-running

Safe to invoke as many times as the user wants during an audit. Each invocation reads the current state of the suggestion list and produces a fresh annotated PDF, overwriting the previous one. To preserve a snapshot, the user should rename or move the previous annotated PDF before re-invoking.

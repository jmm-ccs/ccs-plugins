---
name: claim-pdf-annotator
description: On-demand utility for the CCS forensic claim audit. Reads the suggestion list and the carrier estimate, then produces a marked-up copy of the carrier's estimate — the full estimate reproduced page-flow style, with each suggestion's edits applied in place (changed values, new lines, and new rooms in the CCS edit color) and a justification box directly beneath every change. Renders via the bundled interpret → render pipeline (Xactimate and Symbility), then visually verifies every output page against the carrier estimate and the sample supplements in a fix-and-recheck loop. Trigger any time the user says "annotate the PDF," "show the suggestions on the estimate," "give me a current snapshot of the audit," "produce the marked-up estimate," or whenever they want the suggestion list rendered onto the carrier estimate. Can be called mid-audit for a snapshot or at final delivery — the skill is independent of any other audit stage.
---

# Claim Estimate Markup (On-Demand Utility)

Goal: take the current state of the suggestion list and produce **a marked-up copy of the carrier's estimate** — the full carrier estimate reproduced, with CCS's edits applied in place. This is the audit's end deliverable: not a changes-only list and not a separate addendum, but the whole original estimate with the corrections made in-line.

This skill does **not** run the Sanity Audit, does not resolve flags, and does not gather reason-box wording. Those live in `claim-audit-finalizer`, which invokes this skill as its rendering step. Run standalone, this skill renders whatever the suggestion list currently says.

## Step 0 — Read the protocols

Use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read the entire file end-to-end before doing anything else. Do this every time this skill is invoked. The Carrier Estimate Protocol (§2.3), Output Integrity (§1.1), and Math Integrity (§1.4) are critical here — the marked-up copy uses the suggestion list's own wording and numbers and never adds content the suggestion list doesn't have.

## Prerequisite — enforced gate (refuse until met)

Run this check before producing the markup, per §2.14 of the protocols. Re-check on every attempt.

1. **Active project.** `outputs/audit-progress.md` must exist (setup has run). If it doesn't, refuse and tell the user to run `/claim-audit-setup` first, then stop.
2. **Something to mark up.** `outputs/audit-suggestion-list.md` must exist and hold at least one suggestion row (more than the header). If it's missing or header-only, say so plainly and stop. (This utility can run mid-audit; it does **not** require all 13 stages complete.)

Proceed only when both pass.

## Inputs

- **The suggestion list** — `Read` `outputs/audit-suggestion-list.md`
- **The carrier estimate PDF** — in the project folder root (it will be reproduced; the original stays untouched)
- **The sample supplements** — the three canonical reference renders, in the project folder:
  - `Sample Supplement Xactimate-Green.pdf` — Xactimate carrier, green CCS edits
  - `Sample Supplement Symbility-Terracotta.pdf` — Symbility carrier whose lines use green/teal, terracotta CCS edits
  - `Sample Supplement Symbility-Green.pdf` — Symbility carrier with no green/teal, green CCS edits

  These are ground truth for what a correct render looks like. For every visual comparison, use the sample matching the carrier's platform **and** the edit color the renderer chose; the other-platform sample is your reference for the format check in step 2. If a named sample is missing from the project folder, say so and ask for it before the verification loop.
- **Confirmed reason wording** — `outputs/reason-wording.json`, if present (written by `claim-audit-finalizer`; maps suggestion `#` → the exact user-confirmed reason-box text)

If the suggestion list or the carrier PDF is missing, use `AskUserQuestion` to gather the path and stop until provided.

## What the deliverable looks like

A copy of the carrier's estimate, reproduced faithfully — every room, category, and line item the carrier wrote, in the carrier's order and numbering, clip-composed from the carrier's own pages so text and figures are exact even when the PDF's text layer is corrupt (§2.3). Summary/recap pages are dropped, diagram pages are kept, the CCS header replaces the carrier's branding, and the all-placeholder CCS cover letter is prepended (the auditor fills the `[PLACEHOLDER]`s by hand — the letter is never auto-filled). On top of that reproduction, CCS's edits are applied in place:

- **Changed values** — the field a Correct alters (quantity, unit price, grade wording) is whited out and re-rendered in the **CCS edit color**, in place. Only the field the suggestion actually changes is recolored (§1.1).
- **New lines** — Adds render as new line items under their parent carrier item, aligned to the carrier's own column grid, entirely in the edit color. Added line items are numbered sequentially in the order they appear on the output — `Supp-1.`, `Supp-2.`, `Supp-3.`, … — assigned by the renderer (§2.3); the suggestion list's Label column stays the audit-record identifier.
- **New rooms** — render as real folders in the carrier's folder style for that platform (Symbility: grey header box with dimension grid and sketch cell; Xactimate: room title + rule + two-column dimension block and left diagram cell), placed by their anchor **where the room physically is** (a Main Level room goes in the Main Level section). Dimensions and the drawn footprint sketch come **only** from the suggestion list's `Dimensions [...]` clause — the pipeline never derives or invents a measurement.
- **The CCS edit color** is green by default; the renderer switches to terracotta `#CE7C6B` **only** when the carrier's own line items use a green or green-adjacent color, so CCS edits can never be confused with carrier content.
- **A justification box under every change** carrying the entry's reason text: the user-confirmed wording from `outputs/reason-wording.json` when it exists, otherwise the entry's plain-language Why + Source from `Supporting evidence`, verbatim.

Only entries with **Disposition `Agreed`** and suggestion type **Add or Correct** render. Flags and unresolved entries (`Halted`, `Needs-info`) stay off the output.

## Method — the bundled pipeline

The markup is produced by **two bundled, deterministic scripts** — do **not** hand-roll PDF rendering (§1.1; hand-rolling is what produced the anchor and missing-character bugs these scripts replaced):

- `scripts/interpret.py` — suggestion list + carrier PDF → edit-plan JSON. Deterministic parse/validate; extracts swaps, add cells, new-room anchors/dims/sketch; flags anything interpretive as `[REVIEW]`. It never derives data — every number and measurement must be in the suggestion list.
- `scripts/build_spec.py` — edit-plan JSON → the marked-up PDF. Auto-detects the platform, reflows the carrier content, draws the edits. It computes no math.

### 1. Set up working copies

The plugin's copy of the scripts is a read-only cache. Copy both into the project so runtime fixes are possible:

```bash
SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/claim-pdf-annotator/scripts"
[ -f "$SCRIPTS/interpret.py" ] || SCRIPTS="$(dirname "$(find / -path '*claim-pdf-annotator/scripts/interpret.py' 2>/dev/null | head -1)")"
mkdir -p outputs/pipeline && cp "$SCRIPTS/interpret.py" "$SCRIPTS/build_spec.py" outputs/pipeline/
python3 -c "import fitz" 2>/dev/null || pip install pymupdf --break-system-packages
```

If a rendering defect later requires editing a working copy, log the fix as a process-change request (§2.16) so it can be folded into the plugin permanently.

### 2. Visually identify the platform (independent check)

Before running anything, determine **by looking** whether the carrier estimate is Xactimate or Symbility — separate from the pipeline's own detection. Rasterize the first breakdown page of the carrier PDF and the first breakdown pages of `Sample Supplement Xactimate-Green.pdf` and `Sample Supplement Symbility-Terracotta.pdf` (`page.get_pixmap()` via `bash`, then `Read` the images) — the carrier estimate will visibly match one family or the other:

- **Symbility** — bare item numbers (`31`), room subtotal lines like `Bathroom - Subtotal (35 items)`, grey column stripes on Unit Price/ACV, grey room-header boxes with a sketch cell.
- **Xactimate** — numbered items with periods (`186.`), `Totals: <Room>` lines, per-folder `QUANTITY  UNIT PRICE  TAX  GCO&P …` column headers, plain-text room headers with a left diagram.

Record which one you saw and why (one sentence each for carrier and samples).

### 3. Interpret

Run from the **project folder root** (the carrier PDF's filename must resolve from the working directory):

```bash
python3 outputs/pipeline/interpret.py outputs/audit-suggestion-list.md "<carrier estimate PDF>" outputs/edit-plan.json
```

Read its report in full. **Cross-check the format:** the report's `[format: …]` must match your step-2 visual identification. If they disagree, HALT — show the user both findings and ask which is right before continuing.

### 4. Resolve the interpreter's review flags

The report lists `[REVIEW]` items — add-line descriptions left as `[CONFIRM DESC]`, anchors needing confirmation, page ranges. Resolve every one with `AskUserQuestion` (batch up to 4 questions per call, consecutive batches until done). For add descriptions, the user's answer is the exact line text. Apply every answer to `outputs/edit-plan.json` with `Edit`, verbatim.

### 5. Apply confirmed reason wording

If `outputs/reason-wording.json` exists, replace each plan entry's `reason` with the confirmed text for its `suggestion` number — byte-for-byte, no rewording. Entries without a mapping keep their suggestion-list text. Standalone runs without the file skip this step.

### 6. Render

```bash
python3 outputs/pipeline/build_spec.py outputs/edit-plan.json "outputs/<carrier-pdf-name>-annotated.pdf"
```

The script prints the saved path and edit counts — read and relay them.

### 7. Page-by-page visual verification loop

Verify the output **by looking at it**, one page at a time, against the sources:

1. Rasterize output page N (`get_pixmap`, `Read` the image).
2. Rasterize the **matching carrier page(s)** — match by folder/item content, not page index (the reflow shifts pages) — and the page showing the same construct (a corrected line, an add, a new room, a folder header) in the matching named sample: `Sample Supplement Xactimate-Green.pdf`, `Sample Supplement Symbility-Terracotta.pdf`, or `Sample Supplement Symbility-Green.pdf`, chosen by the carrier's platform and the edit color the renderer picked.
3. Examine closely: folder title + dimension block + column header present and complete; spacing consistent with the surrounding folders; diagrams whole, not clipped; carrier text/figures identical to the original; CCS edits in the right field and color; a justification box under every edit; no overlapping or clipped text; page numbers sequential.
4. Also run the mechanical cross-walk in `bash`: every carrier line item present in the output exactly once (count numbered items at the left margin in both), column-header rows paired on every breakdown page.
5. Any issue found: fix it (the edit-plan JSON if the data is wrong; the working-copy script if the rendering is wrong — then log §2.16), re-render, and **restart this loop from page 1**.
6. The loop ends only when a complete pass over every page finds nothing.

### 8. Whole-document consistency pass

One more read of the full output front to back, checking cross-page consistency: folder-title lead-in spacing uniform, exactly one column header per folder, one edit color throughout, cover letter present and all-placeholder, diagram pages present, footer numbering continuous.

## Bilingual mode (§2.11)

If `**Languages:**` in `outputs/audit-progress.md` is `English + Spanish`, repeat steps 3–8 with the Spanish suggestion list (`outputs/audit-suggestion-list-es.md`) to produce `outputs/<carrier-pdf-name>-annotated-ES.pdf`. Reason-box wording for the Spanish copy is the Spanish rendering of the confirmed English wording — translate each confirmed entry and patch the Spanish plan the same way; numbers, codes, and carrier-line targets stay identical. Never produce the Spanish copy instead of the English one.

## What this skill does NOT do

- Does not run the Sanity Audit, resolve flags, or gather reason-box wording (that's `claim-audit-finalizer`)
- Does not export the suggestion list to XLSX (`claim-suggestion-list-export`)
- Does not modify the suggestion list itself
- Does not recompute, derive, or reword anything — every number, measurement, and reason renders from the suggestion list (or the confirmed-wording file) verbatim (§1.1, §1.4)

## Output

**Hand the marked-up estimate to the user** (the file-sharing / present-files step — include the `-ES` copy if bilingual mode produced one), then print this, exactly:

> This PDF rendering pipeline is in beta and may have issues. Please carefully examine each page against the carrier estimate to ensure formatting, diagrams, and text/figures match. Send me a screenshot, explain the issue, and ask me to fix it for any issues you find.

Follow with one sentence: the saved path and the edit counts (corrects / add-lines / new rooms). If any suggestion could not be anchored, list each with its number, one-line summary, and the Carrier line it was trying to match, so the user can point you at the right line and re-run.

## Re-running

Safe to invoke as many times as the user wants during an audit. Each invocation reads the current state of the suggestion list (and the wording file, if present) and produces a fresh marked-up estimate. To preserve a snapshot, rename the previous copy before re-invoking.

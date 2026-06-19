---
name: claim-pdf-annotator
description: On-demand utility for the CCS forensic claim audit. Reads the suggestion list and the carrier estimate, then produces a marked-up copy of the carrier's estimate — the full estimate reproduced, with each suggestion's edits applied in place (changed values and new lines in green) and a justification box directly beneath every change reading "[x] changed from [old] to [new] for [reason]." Trigger any time the user says "annotate the PDF," "show the suggestions on the estimate," "give me a current snapshot of the audit," "produce the marked-up estimate," or whenever they want the suggestion list rendered onto the carrier estimate. Can be called mid-audit for a snapshot or at final delivery — the skill is independent of any other audit stage.
---

# Claim Estimate Markup (On-Demand Utility)

Goal: take the current state of the suggestion list and produce **a marked-up copy of the carrier's estimate** — the full carrier estimate reproduced, with CCS's edits applied in place. This is the audit's end deliverable: not a changes-only list and not a separate addendum, but the whole original estimate with the corrections made in-line.

This skill does **not** run the Sanity Audit, does not gather dispositions, and does not export the XLSX. It only produces the marked-up estimate copy. It can be invoked at any point in an audit (mid-audit for a snapshot, at final delivery for the deliverable, or any other time the user wants the suggestion list rendered onto the carrier estimate).

For the final-delivery flow that runs the Sanity Audit and exports the XLSX, see `claim-audit-finalizer`.

## Step 0 — Read the protocols

Use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read the entire file end-to-end before doing anything else. Do this every time this skill is invoked. The Carrier Estimate Protocol (§2.3, including the suggestion-list spec, the labeling rules, and Sub-Item Numbering Conflicts) and Output Integrity (§1.1) are critical here — the marked-up copy uses the suggestion list's own wording and numbers and never adds content the suggestion list doesn't have.

## Prerequisite — enforced gate (refuse until met)

Run this check before producing the markup, per §2.14 of the protocols. Re-check on every attempt.

1. **Active project.** `outputs/audit-progress.md` must exist (setup has run). If it doesn't, refuse and tell the user to run `/claim-audit-setup` first, then stop.
2. **Something to mark up.** `outputs/audit-suggestion-list.md` must exist and hold at least one suggestion row (more than the header). If it's missing or header-only, there's nothing to render onto the estimate yet — say so plainly and stop. (This utility can run mid-audit; it does **not** require all 13 stages complete — only that the suggestion list has entries.)

Proceed only when both pass.

## Inputs

- **The suggestion list** — `Read` `outputs/audit-suggestion-list.md` (in the project folder)
- **The carrier estimate** — `Read` the carrier PDF (it will be reproduced; the original stays untouched)

If either is missing, use `AskUserQuestion` to gather the path and stop until provided.

## What the deliverable looks like

A copy of the carrier's estimate, reproduced in full and faithful to the original — same rooms, same categories, same line items, same order, same numbering (§2.3). On top of that faithful reproduction, CCS's edits are applied in place:

- **Changed values are green.** Any value a suggestion alters — a quantity, a unit price, an M/E/L flag, a waste factor, a grade, a line total — is rendered in **green** in the reproduced estimate, replacing (or sitting in place of) the carrier's original value. Only the field the suggestion actually changes turns green (§1.1 — adjust the field that holds the error, nothing else).
- **New lines are green.** Any line a suggestion adds — an ancillary/related line item, a `Supp-New` line, an entirely new sub-room or room/category — is inserted at the location the labeling rules dictate (§2.3: ancillary items directly below their parent line as `b`/`c`/`d` or `Supp-1a/b`; additional items at the end of the room/category as `Supp-New`; whole new rooms/categories at the end of the estimate as `Supp-New`) and rendered entirely in **green**.
- **A justification box under every change or addition.** Directly beneath each changed value and each new line, place a boxed justification that reads:

  > **[x] changed from [old] to [new] for [reason].**

  - `[x]` is the field or line that changed (e.g., "Quantity", "Unit price", "Subfloor line item").
  - `[old]` is the carrier's original value, copied verbatim from the carrier estimate (for a new line, `[old]` is "not present" / "no line").
  - `[new]` is the suggestion's value, copied verbatim from the suggestion list's `Proposed change` (§1.4 — copied, no recomputation).
  - `[reason]` is the suggestion's plain-language **Why + Source** from the `Supporting evidence` field (§1.5), copied verbatim so the box explains, in basic language, what's wrong/missing and which named file or citation backs it.

  The box also carries the suggestion's **disposition** (`Agreed` / `Halted` / `Needs-info`), its **suggestion type** (Add / Correct / Flag), and its **label** (the `b`/`c`/`d` ancillary letter, `Supp-1a/b`, or `Supp-New` per §2.3), so a reader can tell at a glance whether the edit is locked in and that it is CCS's, not the carrier's.

Everything the carrier wrote that no suggestion touches is reproduced black and unchanged. The green is the only thing that signals a CCS edit, and every green element has a justification box beneath it.

## Method

The marked-up estimate is produced by a **bundled, deterministic script** — `scripts/build_annotated_estimate.py`. Do **not** hand-roll the PDF rendering: hand-built rendering is exactly what produced the anchor-misplacement and missing-character bugs this script exists to prevent. The script reproduces the carrier estimate faithfully (original never touched, carrier content black), anchors each suggestion to its carrier line by the **left-column item number** (so it never latches onto a dollar amount in the cost columns), draws the green box + green note, builds the justification appendix, and transliterates characters the PDF base fonts can't render (≈, —, →) so nothing prints as "?".

1. **Ensure the engine is present.** The script needs PyMuPDF. If `python3 -c "import fitz"` errors, install it: `pip install pymupdf --break-system-packages`.

2. **Locate the script** (bundled next to this skill at `scripts/build_annotated_estimate.py`):

   ```bash
   SCRIPT="${CLAUDE_PLUGIN_ROOT}/skills/claim-pdf-annotator/scripts/build_annotated_estimate.py"
   [ -f "$SCRIPT" ] || SCRIPT="$(find / -path '*claim-pdf-annotator/scripts/build_annotated_estimate.py' 2>/dev/null | head -1)"
   ```

3. **Run it** with three arguments — the carrier estimate PDF (in the project folder), the suggestion list, and the output path:

   ```bash
   python3 "$SCRIPT" "<carrier estimate PDF>" "outputs/audit-suggestion-list.md" "outputs/<carrier-pdf-name>-annotated.pdf"
   ```

   How the script renders each entry (per "What the deliverable looks like" above, §2.3):
   - An entry that names a **carrier item** ("Item NNN") → a green box around that carrier line and a green note beneath it (`> CCS #N [type/label/disposition]: <proposed change>`).
   - An entry with **no parent carrier line** — a `Supp-New` room/grounds space or a whole-estimate flag — → carried in the justification appendix (it has no line to sit on).
   - **Every** entry → a full green box in the **justification appendix** at the end, grouped by carrier page, carrying Carrier line, Change (the `Proposed change`), Provenance, and Why/Source — plus disposition, type, and label. Numbers and prose are copied **byte-for-byte** from the suggestion list (§1.1, §1.4 — the script recomputes and rewords nothing).

4. **Read the script's report and relay it.** It prints the saved path (a versioned name if the project folder blocked overwriting a prior file — use whatever it prints), the count of suggestions anchored to a carrier line, and any that landed **appendix-only**. If an entry that *should* sit on a carrier line couldn't be located, surface it to the user with its number, one-line summary, and the Carrier line it was trying to anchor against, so they can point you at the right line and re-run.

**Bilingual mode (§2.11).** If `**Languages:**` in `outputs/audit-progress.md` is `English + Spanish`, run the script a **second time** with the Spanish suggestion list and a `-ES` output name:

```bash
python3 "$SCRIPT" "<carrier estimate PDF>" "outputs/audit-suggestion-list-es.md" "outputs/<carrier-pdf-name>-annotated-ES.pdf"
```

This produces the Spanish marked-up copy **alongside** the English one — carrier line targets, changed values, numbers, and codes identical (they come from the same carrier estimate); only the note and justification prose differ, since the script reads them from the Spanish list. Never produce the Spanish copy instead of the English one.

## Integrity checks before delivery

- **Full reproduction** — the marked-up copy contains every room, category, and line item the carrier estimate has, in the carrier's order and numbering. Nothing the carrier wrote is dropped. Spot-check the room/category list against the carrier PDF.
- **Coverage** — every suggestion-list entry that landed appears as a green edit with a justification box; every green edit traces back to exactly one suggestion-list entry. No green element exists without a suggestion behind it.
- **Right field, verbatim values** — for each Correct entry, only the field the suggestion changes is green, and `[old]`/`[new]` match the carrier estimate and the suggestion list byte-for-byte. Spot-check three entries in detail.
- **Justification present** — every green element has a justification box beneath it carrying the `[x] changed from [old] to [new] for [reason]` line plus disposition, type, and label.

If any check fails, fix and re-render the affected page(s).

## What this skill does NOT do

- Does not run the Sanity Audit (that's `claim-audit-finalizer`)
- Does not gather user dispositions on flagged items (that's `claim-audit-finalizer`)
- Does not export the suggestion list to XLSX (that's `claim-audit-finalizer`)
- Does not modify the suggestion list itself (that happens in the audit stages and the finalizer)
- Does not recompute or reword any value — it renders the suggestion list's numbers and prose onto the estimate verbatim (§1.1, §1.4)

## Output

Short confirmation in chat — no 4-section response. The message includes:

- The saved file's path (`outputs/[carrier-pdf-name]-annotated.pdf`).
- How many edits were applied to the estimate (green changes + green new lines).
- If any entries couldn't be located, each one as:
  - Its suggestion number,
  - The suggestion's one-line summary plus the Carrier line text it was trying to anchor against,
  - A note to point you at the right line so you can re-run.

If every entry landed, the message is one sentence (path + count). If some didn't, that sentence plus a list of the missed ones. Missed entries are never identified by number alone — the auditor needs enough context to fix them without opening the suggestion list.

## Re-running

Safe to invoke as many times as the user wants during an audit. Each invocation reads the current state of the suggestion list and produces a fresh marked-up estimate, overwriting the previous one. To preserve a snapshot, the user should rename or move the previous marked-up copy before re-invoking.

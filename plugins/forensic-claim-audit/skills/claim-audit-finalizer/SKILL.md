---
name: claim-audit-finalizer
description: Final-delivery stage of the CCS forensic claim audit. Runs the Supplement Sanity Audit (factual integrity, alignment with the CCS objective, friction-flagging), gathers user dispositions on every flagged entry, exports the suggestion list to XLSX, and invokes the claim-pdf-annotator skill to produce the annotated carrier PDF. Trigger after the Sales Tax Audit, or when the user says "ready for output," "finalize the audit," "produce the deliverables," or "wrap up the audit." This is the closing skill of the 13-stage pipeline.
---

# Claim Audit Finalizer (Output Step)

Goal: close out the audit. Run the Sanity Audit, lock in user decisions on flagged entries, and produce both deliverables (XLSX export of the suggestion list + annotated carrier PDF) for CCS to use alongside Xactimate when building the carrier-facing supplement.

CCS will use these deliverables to build the actual carrier-facing supplement in Xactimate. Claude does not produce that supplement.

## Step 0 — Read the protocols

Use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read the entire file end-to-end before doing anything else in this stage. Do this every time this skill is invoked. The Output Integrity rules (§1.1), Math Integrity (§1.4), Carrier Estimate Protocol (§2.3, including the suggestion-list spec and Sub-Item Numbering Conflicts), and the Final factual integrity and logic pass (§3) are all critical here.

## Prerequisite

The 13 audit stages have all been confirmed complete and the suggestion list at `outputs/audit-suggestion-list.md` (in the project folder) reflects the user-confirmed state. If any stage is incomplete or the suggestion list is stale, stop and route the user back to the appropriate stage skill or to `forensic-claim-audit` (the master orchestrator).

## Inputs you need

- **The suggestion list** — `Read` `outputs/audit-suggestion-list.md`
- **The carrier PDF** — `Read` it (the PDF annotator will need it)
- **Project documentation** referenced in the suggestion list's Supporting evidence column — `Read` as needed for cross-checks
- **The per-stage output files** in `outputs/stage-outputs/` (§2.9) — each stage's recorded work product. `Read` the relevant one when an entry's rationale, citation, or math needs cross-checking during the Sanity Audit; they hold the *why* behind suggestion-list entries.

If any of the above are missing, use `AskUserQuestion` to gather them and stop until provided.

## Phase 1 — Supplement Sanity Audit

Three goals, run in order. Update the suggestion list (`Edit` on `outputs/audit-suggestion-list.md`) as you go.

### Goal 1 — Absolute factual integrity

`Read` the carrier PDF for every cross-check. For each entry in the suggestion list:

- Does the **Carrier line** (item number + title) match the carrier PDF exactly?
- Does the **Supporting evidence** still exist and still support the suggestion — and does it pass the §1.5 plain-language test? A reviewer who never saw this claim must be able to read it and understand, in basic language, **why** the suggestion exists and **which named source file** backs it. If the Why or the source file is missing, vague, or named only by category, flag the entry for rewrite before delivery.
- Does any number in the **Proposed change** or **Number provenance** column hold up against §1.4 (calculated via `bash` or copied with explicit source)? Re-run any sums in `bash` that look load-bearing.
- Is the unit cost plausible against construction reality?
- Is there any judgmental or hyperbolic language in the entry's **Proposed change** or notes?
- Has every code citation been `WebSearch`-verified?

Anything that fails: fix the entry so it holds up (it stays `Agreed`), set its **Disposition** to `Needs-info` with a Claude note saying what's missing, or — if it can't be supported at all — drop it from the suggestion list. Do not proceed to Phase 2 with known integrity gaps.

### Goal 2 — Alignment with the CCS objective

CCS's stated goal is *"Getting Contractors the Funds to Rebuild Properly Without Insurance Fights or Homeowner Negotiation."* For each entry, ask: *does this suggestion meaningfully advance the contractor's ability to rebuild properly, or is it edge-case revenue that risks the relationship with the carrier and the homeowner?*

Default to keeping everything technically correct. Flag for human decision (these are starting-point friction categories — apply additional considerations as the project warrants):

- Entries where the Supporting evidence is weak
- Entries that depend on a hypothesis that couldn't be `WebSearch`-verified
- Entries with a large dollar impact relative to the project total
- Entries the carrier is likely to bring in their own engineer or expert to dispute

### Goal 3 — Friction-flagging

Explicitly enumerate any entry that might reasonably trigger:

- An insurance fight (carrier denial, request for engineer's letter, request for re-inspection, dispute on regional pricing)
- A homeowner negotiation (selection-grade decisions, scope decisions, items the homeowner might want to upgrade or substitute)

For each flagged entry, use `AskUserQuestion`. Each question must include:

- The suggestion's `#` and a one-line plain-English summary of what it does (e.g., what it adds/changes, where, and the relevant numbers).
- The specific friction — what the carrier is likely to push back on, or what the homeowner is likely to counter, with the reason. One sentence.
- The actual decision, asked last.

Options (3):

- `Keep it`
- `Modify it`
- `Drop it`

`Keep it` and `Modify it` send the suggestion through to the carrier-facing supplement (as-is or adjusted). `Drop it` pulls it.

Batch related entries into a single question only when they truly travel together (e.g., three sub-items under one Carrier line). Otherwise one entry per question.

Wait for the user's decision on each, then apply it: **Keep** leaves the entry `Agreed`; **Modify** applies the change and it stays `Agreed`; **Drop** removes it from the suggestion list. (Per §2.3 the list holds only `Agreed`, `Halted`, and `Needs-info` — there is no `Modified` or `Rejected` disposition; a dropped suggestion simply leaves the list.) Do not proceed to Phase 2 until every flagged entry has been signed off on.

## Phase 2 — Export the suggestion list to XLSX

Use the `xlsx` skill:

1. `Read` `outputs/audit-suggestion-list.md` (now reflecting all Phase 1 updates).
2. Convert the markdown table to a clean `.xlsx` and save as `outputs/audit-suggestion-list.xlsx`.
3. Preserve all fields. Sort by **Stage of origin** then by **Carrier line** item number. Freeze the header row. Apply column widths that fit the typical content of each field.
4. Include all entries regardless of disposition (the XLSX is the full audit record; CCS reviews it and decides what to push into Xactimate based on disposition).

Confirm the XLSX was written successfully before moving to Phase 3.

**Bilingual mode (§2.11).** If `**Languages:**` in `outputs/audit-progress.md` is `English + Spanish`, also produce a Spanish duplicate `outputs/audit-suggestion-list-es.xlsx`, built from the Spanish suggestion list `outputs/audit-suggestion-list-es.md` (same all-entries scope, same columns; numbers, codes, and carrier-line references identical, descriptive fields in Spanish). Write it **alongside** the English XLSX. The annotator (Phase 3) produces the Spanish-annotated PDF on its own when bilingual is on.

## Phase 3 — Invoke the PDF annotator

Use the `Read` tool on `../claim-pdf-annotator/SKILL.md` and execute that skill end-to-end. The annotator reads the suggestion list, duplicates the carrier PDF, and places comments at each relevant carrier line. It will save the annotated PDF as `outputs/[carrier-pdf-name]-annotated.pdf`.

Wait for the annotator to confirm completion (and report any entries it couldn't locate on the PDF).

## Phase 4 — Final fact-check of the deliverables

Phase 1's Sanity Audit checked the *suggestion-list entries themselves*. Phase 4 is a separate check that the *deliverables* faithfully represent those entries — the markdown → XLSX export and the suggestion-list → PDF annotation are both transformations, and either could silently drop or corrupt an entry.

Re-read all three artifacts: `outputs/audit-suggestion-list.md`, `outputs/audit-suggestion-list.xlsx`, and `outputs/[carrier-pdf-name]-annotated.pdf`. Then verify:

**Markdown ↔ XLSX cross-check.**

- Every row in the markdown appears as a row in the XLSX, and vice versa. Run `bash` with Python to count rows in both and confirm the counts match.
- Every field value matches between markdown and XLSX (no truncation, no misordering, no character-encoding changes). Spot-check three random entries in detail.
- The XLSX is sorted by Stage of origin, then by Carrier line item number, with header row frozen.

**Markdown ↔ annotated PDF cross-check.**

- Every suggestion-list entry (`Agreed`, `Halted`, or `Needs-info`) has a corresponding comment on the annotated PDF.
- No comment exists on the PDF that doesn't trace back to a suggestion-list entry.
- Each PDF comment reproduces its suggestion-list entry — disposition, suggestion type, label, proposed change, number provenance, supporting evidence — with the exact wording from the suggestion list.
- Each PDF comment is anchored at the correct carrier line item.

**Final factual-integrity-and-logic pass on the whole output** (per §3 of the protocols).

- Every fact in any user-facing summary you produce in this stage has provenance.
- Every number you report (entry counts, dollar totals, etc.) ran through `bash` and shows the input and result.
- The deliverables contain no hyperbolic language and no judgmental framing.
- Audit-Myopia: no entry appears twice in any deliverable.

If any check fails, fix the affected deliverable(s) and re-run Phase 4. Do not advance to Phase 5 until every cross-check passes. This phase is load-bearing — by the time the user sees the deliverables, the suggestion list, the XLSX, and the annotated PDF must be a tight three-way match, with no drift introduced by the transformations.

## Phase 5 — Manual checks reminder

After both deliverables are in place, tell the user the files are saved and present the six checks below for them to run themselves. The message:

- Opens with one sentence saying the files are saved and these checks are load-bearing.
- Lists the six checks below, in this order, in the same plain-English action voice.
- Has nothing else before, between, or after.

The six checks:

1. Pick three random entries from the middle of the suggestion list and Ctrl+F their Carrier line item numbers against the carrier PDF. Item number and title must match exactly.
2. Read every suggestion's *Proposed change* and *Number provenance*. The language should be factual; the math should be reproducible.
3. Confirm specs match the home — no high-grade finishes specified in a low-grade home.
4. Re-run three random calculated numbers in a calculator or spreadsheet. They should land on the same result.
5. Walk the carrier PDF top to bottom and confirm no rooms or line items got skipped on the supplement side.
6. Any single line whose dollar impact looks disproportionate to construction reality — that's a goal-seeking flag. Flag it now.

These checks are load-bearing. Do not skip the reminder, and do not let the user skip the checks.

## Verification gate

After both deliverables are produced and the manual-checks reminder has been delivered, write a short closing message. It includes:

- Both file paths (`outputs/audit-suggestion-list.xlsx` and `outputs/[carrier-pdf-name]-annotated.pdf`) so the user can find them.
- That the checks above are what they should run on those files.
- That confirming closes out the audit.

Two sentences max.

If the user invokes HALT or requests revisions, follow §6 of the protocols: stop, re-anchor against the carrier PDF using `Read`, update the affected suggestion-list entry, and re-run only Phase 2 and Phase 3 to refresh the deliverables. Do not regenerate from scratch unless the user asks.

## Re-invoking the annotator separately

The PDF annotator is independent — the user can re-invoke `claim-pdf-annotator` at any point (during or after the audit) to refresh the annotated PDF without re-running the full finalizer. Useful when the user marks an entry's disposition after the audit closes and wants a fresh PDF without redoing the Sanity Audit.

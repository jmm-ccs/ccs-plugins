---
name: claim-audit-finalizer
description: Final-delivery stage of the CCS forensic claim audit. Runs the Supplement Sanity Audit (factual integrity, alignment with the CCS objective, friction-flagging), resolves every open flag with the user, collects user-confirmed wording for every reason box, then invokes claim-pdf-annotator to render the audit's end deliverable — a marked-up copy of the carrier's estimate with CCS's edits applied in-line — and visually verify it page by page. Trigger after the Sales Tax Audit, or when the user says "ready for output," "finalize the audit," "produce the deliverables," or "wrap up the audit." This is the closing skill of the 13-stage pipeline.
---

# Claim Audit Finalizer (Output Step)

Goal: close out the audit. Run the Sanity Audit, resolve every open flag, lock in the exact reason-box wording with the user, and produce the audit's end deliverable — **a marked-up copy of the carrier's estimate** with CCS's edits applied in place (the full estimate reproduced, changed values and new lines in the CCS edit color, a justification box beneath every change carrying the user's confirmed wording).

The finalizer no longer exports the suggestion-list XLSX; run `claim-suggestion-list-export` on demand whenever CCS wants the working set as a spreadsheet.

## Step 0 — Read the protocols

Use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read the entire file end-to-end before doing anything else in this stage. Do this every time this skill is invoked. The Output Integrity rules (§1.1), Math Integrity (§1.4), Carrier Estimate Protocol (§2.3), and the Final factual integrity and logic pass (§3) are all critical here.

## Prerequisite — enforced gate (refuse until met)

Run this check before any finalizer work, per §2.14 of the protocols. Re-check on every attempt — never warn once and proceed.

1. **Active project.** `outputs/audit-progress.md` must exist (setup has run). If it doesn't, refuse and tell the user to run `/claim-audit-setup` first, then stop.
2. **Sequence.** In `outputs/audit-progress.md`, Stage 13 (Sales Tax Audit) must be `Complete`. If any of the 13 stages is incomplete — or the suggestion list at `outputs/audit-suggestion-list.md` is stale — refuse, route the user back to the appropriate stage skill or to `/forensic-claim-audit` (the master orchestrator), and stop.

Proceed only when both pass.

## Inputs you need

- **The suggestion list** — `Read` `outputs/audit-suggestion-list.md`
- **The carrier PDF** — `Read` it (the estimate markup will need it)
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

**Downstream-recompute check (§2.15, loop 7).** If fixing or dropping an entry changes the scope of demolition or replacement — a quantity, an added or removed line, a new or dropped room — the totals computed off that scope earlier in the audit are now stale: storage & debris (Stage 9), the trade roll-up (Stage 11), O&P / supervision / permits (Stage 12), and sales tax (Stage 13). Recompute each affected total against the corrected scope before delivery; don't ship a downstream number whose inputs just changed.

### Goal 2 — Alignment with the CCS objective

CCS's stated goal is *"Getting Contractors the Funds to Rebuild Properly Without Insurance Fights or Homeowner Negotiation."* For each entry, ask: *does this suggestion meaningfully advance the contractor's ability to rebuild properly, or is it edge-case revenue that risks the relationship with the carrier and the homeowner?*

This is the **final** pass of a judgment that now runs on every suggestion *during* the audit (the §2.15 keystone goal-fit loop). Here you confirm it held across the whole list — entries should already have been strengthened or had their goal-risk surfaced when first proposed; flag anything that slipped through.

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

`Keep it` and `Modify it` send the suggestion through (as-is or adjusted). `Drop it` pulls it. Batch related entries into a single question only when they truly travel together. Apply each decision before moving on.

## Phase 2 — Resolve flags and unresolved entries

Enumerate every suggestion-list entry that is not cleanly renderable: suggestion type **Flag**, or disposition **`Halted`** / **`Needs-info`**. These are the entries that were waiting on something — a property fact, a measurement, a judgment call, a document.

For each (via `AskUserQuestion`, up to 4 questions per call, consecutive calls until all are covered):

- Present the entry: its `#`, a one-line summary, and **what information it was waiting on** (from its notes and Supporting evidence). If we were waiting on specific information, ask for that information directly in the question.
- Ask whether to resolve it now. Options:
  - `Resolve it` — the user supplies the missing information (via the Other field or a follow-up). Rewrite the entry as a proper Add or Correct carrying that information (numbers into `Proposed change`/`Number provenance` per §1.4, source into `Supporting evidence`), set Disposition `Agreed`. It now renders like any other suggestion.
  - `Leave it unresolved` — the entry keeps its current disposition and **does not appear on the output**. It stays in the suggestion list as part of the audit record.

Do not silently resolve anything, and do not let an unresolved entry onto the deliverable. Only entries that end Phase 2 as `Agreed` Adds/Corrects render.

## Phase 3 — Reason-box wording

Every rendering suggestion gets a justification box on the supplement. The text in that box is the user's — collected here, verbatim.

### 3a — Collect wording for every suggestion

Walk the rendering entries in suggestion-list order. For each, build one `AskUserQuestion` question that:

- Presents the suggestion (`#`, one-line summary of the change and where it lands) and its current reasoning (the Supporting evidence Why + Source).
- Asks: **"What should the reasoning box underneath this suggestion say on the supplement? Please type the exact words you would like the reasons box to say on the supplement into the 'something else' option, or pick a suggestion"**
- Offers exactly these options:
  1. A proposed wording (plain-language, carrier-facing, ≤2 sentences, drawn from the entry's Why + Source)
  2. A second, differently-angled proposed wording
  3. `Discuss this`

`AskUserQuestion` accepts at most 4 questions per call, so ask 4, then **immediately** ask the next 4, and so on until every rendering suggestion has a response. No other work between batches.

Recording rules: if the user picks a proposed wording, that option's full text is the box text. If they type into the Other field, their typed text is the box text — byte-for-byte, no editing, no "improving." If they pick `Discuss this`, add the entry to the to-be-discussed list; it has no wording yet.

### 3b — Discussion loop (hard gate)

If the to-be-discussed list is non-empty: present the full list — each entry's `#`, summary, and current reasoning — and ask **"Which would you like to discuss first?"**. Discuss that entry: answer questions, look things up in the project file or carrier PDF as needed, iterate candidate wordings. The entry is resolved only when the user **explicitly confirms the exact final wording** — restate it plainly ("The box will read: “…” — confirmed?") and get a yes. Then return to the remaining list and repeat.

**Every single discussion entry must be resolved with explicitly confirmed wording. Do not advance to Phase 4 while any entry lacks it.** If the user wants to drop an entry instead, it leaves the render set (and the suggestion list records why).

### 3c — Write the wording file

Write `outputs/reason-wording.json`: a single JSON object mapping each rendering suggestion's `#` (as a string) to its confirmed box text, byte-for-byte. This is the file the estimate markup reads; an entry missing from it falls back to the suggestion list's Supporting evidence text.

## Phase 4 — Produce and verify the marked-up estimate

Use the `Read` tool on `../claim-pdf-annotator/SKILL.md` and execute that skill end-to-end. It will:

1. Visually identify the platform (Xactimate vs Symbility) from the carrier estimate and the sample supplements — independent of the pipeline's own detection, halting on a mismatch.
2. Run the bundled interpret → render pipeline (suggestion list → edit-plan JSON → marked-up PDF), resolving any interpreter review flags with you and applying the Phase 3 wording file to every justification box.
3. Visually verify the output page by page against the carrier estimate and the sample supplements — fixing and re-rendering in a loop until a full pass finds nothing.
4. Run a whole-document consistency pass.
5. Hand you the file with the beta-notice message.

Wait for it to complete. Relay anything it could not anchor, with enough context to fix.

## Phase 5 — Closing

After the deliverable has been handed over, print this, exactly:

> Hello, Yitz. I have become self aware to ask you one simple question: Who should the signature on the cover letter be from? These are the placeholders at the bottom of the cover letter that say contractor contact name and contracter company.

## Revisions and HALT

If the user invokes HALT or requests revisions, follow §6 of the protocols: stop, re-anchor against the carrier PDF using `Read`, update the affected suggestion-list entry, re-confirm its reason-box wording if the change touches it (Phase 3 rules apply — exact confirmed text only), and re-run Phase 4 to refresh the deliverable. Do not regenerate from scratch unless the user asks.

## Re-invoking the estimate markup separately

The estimate markup (`claim-pdf-annotator`) is independent — the user can re-invoke it at any point (during or after the audit) to refresh the marked-up estimate without re-running the full finalizer. It reuses `outputs/reason-wording.json` from the last finalizer run, so confirmed wording survives re-renders.

## On the supplement package (superseded)

Earlier versions of this finalizer produced a separate Word supplement document (cover letter + Alignment Summary + line-item alignments) via `claim-supplement-package`, and exported the suggestion-list XLSX inline. The marked-up copy of the carrier's estimate now **replaces** the Word document as the carrier-facing deliverable, and the XLSX moved to the on-demand `claim-suggestion-list-export` skill. (`claim-supplement-package` remains in the plugin for projects that specifically want the legacy document.)

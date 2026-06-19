---
name: claim-line-item-audit
description: Stage 2 of the CCS forensic claim audit. Room-by-room line-by-line audit of the carrier's Xactimate estimate to flag missed, mis-priced, or mis-quantified line items. Trigger after the Scope Audit, or when the user asks "what's missing in [room name]," "audit the line items room by room," "compare against industry-standard frequently-missed items," or asks about site protection / hardware / prep labor / debris that a carrier macro tends to omit.
---

# Line Item Audit (Stage 2 of 13)

Goal: room by room, audit the carrier's individual Xactimate line items against project evidence and industry-standard frequently-missed items. Output: corrections to existing items + additions, both labeled per the Carrier Estimate Protocol so the carrier's structure stays intact.

## Step 0 — Read the protocols

Use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read the entire file end-to-end before doing anything else in this stage. Do this every time this skill is invoked, regardless of whether the protocols were loaded earlier. The Carrier Estimate Protocol (numbering, Supp-New labels, Sub-Item Numbering Conflicts), the Output Integrity rule (adjust the right field), and the Audit-Myopia check are critical here.

**§1.5 reminder — every suggestion this stage raises needs its plain-language Why + Source.** In basic language: what's wrong or missing and why the fix is justified, plus the basis it rests on — a named project file, a verified citation, or an openly flagged judgment call. No Why or no Source means it isn't ready: don't propose it and don't record it (§1.5 completeness gate, §2.3).

## Prerequisite — enforced gate (refuse until met)

Run this check before any work in this stage, per §2.14 of the protocols. Re-check on every attempt — never warn once and proceed.

1. **Active project.** `outputs/audit-progress.md` must exist (setup has run). If it doesn't, this isn't an active claim project yet: refuse, tell the user to run `/claim-audit-setup` first, and stop.
2. **Sequence.** In `outputs/audit-progress.md`, Stage 1 (Scope Audit) must be `Complete` or `Skipped`. If it isn't, refuse, point the user to `/claim-scope-audit`, and stop.

Proceed only when both pass.

## Method — one macro-area at a time, room by room within each

Work the property **one macro-area at a time** (§2.8 of the protocols). Read `outputs/macro-areas.md`, walk the macro-areas in the order it lists them, and inside each macro-area go **room by room**. The per-room gate (below) nests inside the per-macro-area gate.

Do **not** try to audit the whole estimate in one response. The carrier's estimate has dozens of rooms; auditing them all at once will hit token limits and force you to summarize, which violates the protocols (§2.1 Token Limit Check).

For each room (within the current macro-area):

1. **Anchor against the source.** Use `Read` on the carrier PDF and quote the room title and item list (item numbers and titles) directly from the PDF. If you cannot quote a number-and-title pair from the PDF, do not include it.

2. **Walk the carrier's items in order.** For each carrier item:
   - State the item number and title exactly as written.
   - Note quantity, unit, unit price, and Xactimate M/E/L flags.
   - Compare against project evidence (photos, sketches, scope of work, measurements). Flag any material discrepancy in *quantity* (square footage, linear footage, count) or *grade* (e.g., "high-grade" cabinets specified in a low-grade home).
   - Flag any item where the per-unit price appears to deviate materially from the Xactimate regional default — note this as a *hypothesis*, not a verified fact, unless you've used `WebSearch` to verify the regional price list.

3. **Identify items the carrier missed.** Use `Read` on `references/frequently-missed-categories.md` for the Checklist 3 starting-point categories (site protection, hardware & fixtures, preparatory labor, waste & debris). The reference is a **starting point, not exhaustive** — apply any other reliable, independently-verifiable, industry-standard guidance.

4. **Label additions per the Carrier Estimate Protocol** (protocols §2.3):
   - Ancillary item under existing carrier line: `[carrier item number] b, c, d, …`
   - **If the carrier already uses sub-letters** (e.g., `1a`, `1b`): use `Supp-1a`, `Supp-1b`, etc. (Sub-Item Numbering Conflicts Directive)
   - New item in same room: `Supp-New` at end of room
   - New room/category entirely: comes in via a follow-up scope amendment (rare at this stage; usually caught in Stage 1)

5. **Run the Audit-Myopia check.** Before finalizing each correction, confirm you have not already proposed the same correction earlier in this room or in a prior room. Document the check.

## Adjusting the right field

If the carrier under-quantified a material with built-in waste (baseboard, paint, flooring), the correction is to **quantity**, not unit price. Inflating unit price to backfill is an Output Integrity violation (protocols §1.1).

## Output — per room

This is substantive — use the four-section format (Analysis / Recommendations / Challenge to AI / Challenge to User) plus verified/unverified facts.

**Recommendations** is a structured table per room:

| # | Carrier Item (as in the PDF) | Qty | Unit | Issue | Proposed correction | Label |

Issues fall into: *Quantity*, *Unit price*, *Grade/spec*, *Missing M/E/L component*, *Missing related item* (defer most of those to Stage 4 unless trivially obvious here).

## Stage output (§2.9)

This stage's deliverable is the **room-by-room record of carrier line-item corrections and additions** — every flagged quantity/price/grade discrepancy and every missed item, with its label and proposed fix. Record it in `outputs/stage-outputs/02-line-item.md`, organized by macro-area then room (the same order you walked), and record its findings in the consolidated audit-findings artifact (`claim-audit-findings`, §2.9) — add/refresh this stage's entry, one group per macro-area. Build both incrementally as you finish each macro-area; markdown is canonical.

## Token-limit check

If a single room's audit looks like it will not fit in one response, propose a sub-division (e.g., "audit the Master Bath in two passes — fixtures first, then flooring + walls"). Do not summarize to fit.

## Stay in this stage's lane

Per §2.10 of the protocols, this stage decides only **whether each carrier line item has the right quantity, unit price, and grade — and whether any line item was missed**. It works the carrier's existing items room by room.

While doing it you will see things that belong to other stages — whether a line is missing its Material/Equipment/Labor components or a waste factor (Stage 3), a missing companion/related item such as subfloor, leveling compound, or a transition strip (Stage 4), peril-specific scope (Stage 5), exterior structures (Stage 6), code upgrades (Stage 7), or debris/disposal volumes (Stage 9). Do not mention them, do not ask whether to flag them, and do not record them anywhere. Drop them; the owning stage re-examines the whole estimate and will catch them. Noticing an out-of-stage item and asking whether to flag it is the §2.10 violation to avoid.

## Recording suggestions in the suggestion list

For every suggestion this stage produces (corrections to existing line items, new additions, flagged grade/quantity discrepancies), walk each one through the per-suggestion confirmation flow defined in §2.3 of the protocols: call `AskUserQuestion` per suggestion with options Accept / Reject / Modify / Ask a question. Only Accepted entries get appended to `outputs/audit-suggestion-list.md` (disposition `Agreed`). Refresh the live artifact after each append.

**Strict per-suggestion flow (§2.3).** Every suggestion above gets its **own** `AskUserQuestion` call — one suggestion per call. Do not batch them, do not replace them with a single "shall I add these?" question, and do not ask the verification gate until every suggestion this stage produced has been individually Accepted, Rejected, or Modified-then-Accepted.

## Verification gate — per room

After each room (procedural turn — short and direct, not 4-section):

> "Do you believe the Line Item Audit for [Room Name] is complete? If not, please direct me to the incomplete item(s)."

After confirmation, prompt for the next room in the macro-area.

## Per-macro-area gate

When every room in a macro-area is done, ask the per-macro-area gate (§2.8) before moving to the next macro-area:

> "Do you believe the Line Item Audit for [Macro-area] is complete? If not, please direct me to the incomplete item(s)."

After confirmation, move to the next macro-area.

## Stage-end gate

When all macro-areas are done:

> "Do you believe the Line Item Audit is complete? If not, please direct me to the incomplete item(s)."

After the user confirms, route per §4 of the protocols (which honors the audit mode in `outputs/audit-progress.md`). The next stage is **Line Item Completeness Audit** (skill: `claim-line-item-completeness-audit`).

In single-session mode, §4 prompts *"Ready for Line Item Completeness Audit."* and waits for "begin completeness audit" (or equivalent) before chaining. In multi-session mode, §4 prints the multi-session hand-off and stops here — the user begins the Line Item Completeness Audit in a fresh chat in this same Cowork project.

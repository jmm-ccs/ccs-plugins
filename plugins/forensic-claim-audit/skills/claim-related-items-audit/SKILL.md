---
name: claim-related-items-audit
description: Stage 4 of the CCS forensic claim audit. Room-by-room check that each line item's related/companion items are also included — subfloor, leveling compound, adhesive, transition strips, grout, drywall mud, primer, etc. Trigger after the Line Item Completeness Audit, or when the user asks "are the companion items there," asks about transition strips, subfloor, leveling compound, paint primer, drywall mud/tape, grout, or any item that travels with another.
---

# Related Items Audit (Stage 4 of 13)

Goal: room by room, re-examine each line item to confirm the related/companion items it depends on are also present in the estimate.

## Step 0 — Read the protocols

Use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read the entire file end-to-end before doing anything else in this stage. Do this every time this skill is invoked. The Audit-Myopia check is especially critical here — many related items overlap with Stage 3 corrections.

**§1.5 reminder — every suggestion this stage raises needs its plain-language Why + Source.** In basic language: what's wrong or missing and why the fix is justified, plus the basis it rests on — a named project file, a verified citation, or an openly flagged judgment call. No Why or no Source means it isn't ready: don't propose it and don't record it (§1.5 completeness gate, §2.3).

## Prerequisite

Stages 1, 2, and 3 must be confirmed complete.

## What "related items" means

A line item rarely stands alone in real construction. Installing the primary item requires companion items that the carrier's macro often misses.

Use `Read` on `references/companion-items-by-trade.md` for the starting-point list of companion items organized by trade (flooring, tile, drywall, paint, cabinetry, trim, plumbing fixtures, electrical fixtures, roofing, siding, HVAC R&R). The reference is a **starting point, not exhaustive** — apply any other reliable, independently-verifiable, industry-standard guidance for the trade and the specific project.

## Method — one macro-area at a time, room by room within each

Work the property **one macro-area at a time** (§2.8 of the protocols). Read `outputs/macro-areas.md`, walk the macro-areas in order, and inside each go room by room. The per-room gate nests inside the per-macro-area gate (both below).

For each room (within the current macro-area):

1. **List every line item now in the estimate** (carrier original + every supplement added in Stages 2–3). Use `Read` on the carrier PDF for exact item numbers and titles.

2. **For each item, identify its companion items.** Mentally walk the trade installation sequence — what does a real installer need to bring on the truck and bill for?

3. **Cross-check against the current estimate.** Companion already there? Mark Present. Missing? Recommend addition.

4. **Run the Audit-Myopia check.** This is the stage where double-counting is most likely. If transition strips were already added in Stage 2, do not re-add them here. Document the check.

5. **Label additions** per the Carrier Estimate Protocol — `[item] b, c, d` for ancillary additions to a specific carrier item, or `Supp-1a` / `Supp-1b` if the carrier already uses sub-letters; `Supp-New` for additions belonging to the room generally.

## Output — per room

Substantive — four-section format plus verified/unverified facts.

**Recommendations** structured as:

| Primary item | Companion item | Status (Present / Missing) | Proposed addition (if missing) | Label |

## Stage output (§2.9)

This stage's deliverable is the **companion-item record** — for each primary line item, which related/companion items are present vs. missing, and the proposed additions. Record it in `outputs/stage-outputs/04-related-items.md`, organized by macro-area then room, and record its findings in the consolidated audit-findings artifact (`claim-audit-findings`, §2.9) — this stage's entry, one group per macro-area. Build incrementally; markdown is canonical.

## Stay in this stage's lane

Per §2.10 of the protocols, this stage decides only **whether each line item's companion items are present (subfloor, leveling compound, adhesive, transition strips, grout, drywall mud, primer, and the like)**. It checks for the items that travel *with* an existing line.

While doing it you will see things that belong to other stages — the primary item's price, quantity, or grade (Stage 2), its Material/Equipment/Labor make-up (Stage 3), peril-specific items (Stage 5), or code upgrades (Stage 7). Do not mention them, do not ask whether to flag them, and do not record them anywhere. Drop them; the owning stage re-examines the whole estimate and will catch them. Noticing an out-of-stage item and asking whether to flag it is the §2.10 violation to avoid.

## Recording suggestions in the suggestion list

For every suggestion this stage produces (missing companion items per primary line), walk each one through the per-suggestion confirmation flow defined in §2.3 of the protocols: call `AskUserQuestion` per suggestion with options Accept / Reject / Modify / Ask a question. Only Accepted entries get appended to `outputs/audit-suggestion-list.md` (disposition `Agreed`). Refresh the live artifact after each append.

**Strict per-suggestion flow (§2.3).** Every suggestion above gets its **own** `AskUserQuestion` call — one suggestion per call. Do not batch them, do not replace them with a single "shall I add these?" question, and do not ask the verification gate until every suggestion this stage produced has been individually Accepted, Rejected, or Modified-then-Accepted.

## Verification gates

Per-room (procedural):

> "Do you believe the Related Items Audit for [Room Name] is complete? If not, please direct me to the incomplete item(s)."

Per-macro-area (§2.8), after every room in the macro-area is done:

> "Do you believe the Related Items Audit for [Macro-area] is complete? If not, please direct me to the incomplete item(s)."

Stage end (after all macro-areas):

> "Do you believe the Related Items Audit is complete? If not, please direct me to the incomplete item(s)."

After the user confirms, route per §4 of the protocols (which honors the audit mode in `outputs/audit-progress.md`). The next stage is **Type-of-Loss Audit** (skill: `claim-type-of-loss-audit`).

In single-session mode, §4 prompts *"Ready for Type-of-Loss Audit."* and waits for "begin type of loss audit" (or equivalent) before chaining. In multi-session mode, §4 prints the multi-session hand-off and stops here — the user begins the Type-of-Loss Audit in a fresh chat in this same Cowork project.

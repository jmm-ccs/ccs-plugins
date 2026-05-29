---
name: claim-line-item-completeness-audit
description: Stage 3 of the CCS forensic claim audit. Room-by-room verification that each line item correctly includes Material (with appropriate waste factor), Equipment, and Labor as applicable. Trigger after the Line Item Audit, or when the user asks "is each line item complete with M/E/L," asks about waste factors, asks whether labor is missing on a material-only line, or asks whether equipment rental was scoped.
---

# Line Item Completeness Audit (Stage 3 of 13)

Goal: room by room, re-evaluate each line item for completeness — does it correctly include Material (with waste where appropriate), Equipment, and Labor as applicable?

## Step 0 — Read the protocols

Use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read the entire file end-to-end before doing anything else in this stage. Do this every time this skill is invoked. The Output Integrity rule about adjusting the right field (quantity vs. unit price) is especially important here.

## Prerequisite

Stages 1 (Scope) and 2 (Line Item) must be confirmed complete.

## What "complete" means in Xactimate

Most Xactimate line items roll up some combination of Material (M), Equipment (E), and Labor (L). Common failure modes — these are starting points, not exhaustive:

- **Material-only line that should include Labor**: e.g., "Cabinet — base, premium grade" listed as material only, with no install labor.
- **Labor-only line that should include Equipment**: e.g., "Carpet — remove" without dumpster/equipment allocation when bulk removal is involved.
- **Material with no waste factor**: cut materials (baseboard, casing, trim, flooring, drywall, paint, roofing, siding) inherently scrap during installation. Industry-standard waste factors apply (typical: 10% for cut linear materials, 5–10% for sheet goods, 15% for diagonal flooring or complex roof geometry — use `WebSearch` to verify against the localized Xactimate default before applying).
- **Equipment line missing the matching labor or material**: scaffolding rental without the trade labor that justifies it; specialized extraction equipment without the IICRC-aligned labor codes.

## Method — one macro-area at a time, room by room within each

Work the property **one macro-area at a time** (§2.8 of the protocols). Read `outputs/macro-areas.md`, walk the macro-areas in order, and inside each go room by room. The per-room gate nests inside the per-macro-area gate (both below).

For each room (within the current macro-area), walk every line item (carrier originals + Supp-New / lettered additions from Stage 2). Use `Read` on the carrier PDF for exact item titles.

For each line item:

1. **State the item exactly** — number, title, current M/E/L flags, quantity, unit, unit price.
2. **Decide what M/E/L the item should contain** based on best-practices building standards appropriate to *this specific project* (not a generic model home). Cite the basis — Xactimate macro definition, IICRC standard, manufacturer spec, etc. Use `WebSearch` to verify any cited industry standard.
3. **Compare and flag.**
   - Missing Material → recommend adding material with quantity and waste factor.
   - Missing Labor → recommend adding labor at the appropriate Xactimate labor code.
   - Missing Equipment → recommend adding equipment line with hours/days.
   - Wrong waste factor → recommend correcting the **quantity** (Output Integrity §1.1 — adjust the right field).
4. **Run the Audit-Myopia check** — make sure you are not double-correcting an item already corrected in Stage 2.

## Where to apply waste factors — starting points, not exhaustive

Apply waste only on cut/installed materials.

- Baseboard, shoe mold, casing, crown — typically ~10%
- Carpet, vinyl plank, hardwood — sheet/plank goods, ~5–10%, more for diagonal layouts
- Drywall — ~10% on standard walls, more in complex geometry
- Roof shingles — ~10–15% depending on hips/valleys/dormers
- Paint — ~10%

Do not apply waste to fixtures, appliances, hardware, fully prefabricated items.

If you are unsure of the localized waste convention, declare it as an unverified fact and note the literature source.

## Output — per room

Substantive analytical response — four-section format plus verified/unverified facts.

**Recommendations** is a structured table:

| # | Item (as in the PDF) | Current M/E/L | Missing component | Proposed addition | Quantity / waste / labor code |

## Stage output (§2.9)

This stage's deliverable is the **completeness record** — for each line item, what Material / Equipment / Labor it should carry, what's missing, and the waste-factor corrections. Record it in `outputs/stage-outputs/03-completeness.md`, organized by macro-area then room, and record its findings in the consolidated audit-findings artifact (`claim-audit-findings`, §2.9) — this stage's entry, one group per macro-area. Build incrementally; markdown is canonical.

## Stay in this stage's lane

Per §2.10 of the protocols, this stage decides only **whether each existing line item correctly carries Material (with waste where appropriate), Equipment, and Labor**. It checks the make-up of items already on the estimate.

While doing it you will see things that belong to other stages — whether an item is missing entirely or mis-priced/mis-quantified (Stage 2), a missing companion/related item (Stage 4), or peril-specific items (Stage 5). Do not mention them, do not ask whether to flag them, and do not record them anywhere. Drop them; the owning stage re-examines the whole estimate and will catch them. Noticing an out-of-stage item and asking whether to flag it is the §2.10 violation to avoid.

## Recording suggestions in the suggestion list

For every suggestion this stage produces (missing M/E/L components, waste-factor corrections, grade adjustments), walk each one through the per-suggestion confirmation flow defined in §2.3 of the protocols: call `AskUserQuestion` per suggestion with options Accept / Reject / Modify / Ask a question. Only Accepted entries get appended to `outputs/audit-suggestion-list.md` (disposition `Agreed`). Refresh the live artifact after each append.

**Strict per-suggestion flow (§2.3).** Every suggestion above gets its **own** `AskUserQuestion` call — one suggestion per call. Do not batch them, do not replace them with a single "shall I add these?" question, and do not ask the verification gate until every suggestion this stage produced has been individually Accepted, Rejected, or Modified-then-Accepted.

## Verification gates

Per-room procedural turn:

> "Do you believe the Line Item Completeness Audit for [Room Name] is complete? If not, please direct me to the incomplete item(s)."

Per-macro-area (§2.8), after every room in the macro-area is done:

> "Do you believe the Line Item Completeness Audit for [Macro-area] is complete? If not, please direct me to the incomplete item(s)."

Stage end (after all macro-areas):

> "Do you believe the Line Item Completeness Audit is complete? If not, please direct me to the incomplete item(s)."

After the user confirms, route per §4 of the protocols (which honors the audit mode in `outputs/audit-progress.md`). The next stage is **Related Items Audit** (skill: `claim-related-items-audit`).

In single-session mode, §4 prompts *"Ready for Related Items Audit."* and waits for "begin related items audit" (or equivalent) before chaining. In multi-session mode, §4 prints the multi-session hand-off and stops here — the user begins the Related Items Audit in a fresh chat in this same Cowork project.

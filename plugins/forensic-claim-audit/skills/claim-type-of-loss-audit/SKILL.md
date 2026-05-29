---
name: claim-type-of-loss-audit
description: Stage 5 of the CCS forensic claim audit. Re-audit the entire estimate against peril-specific industry standards — wind/hail/storm roofing, water mitigation (IICRC S500/S520), or fire/smoke/odor — to catch peril-specific items the carrier missed. Trigger after the Related Items Audit, or when the user mentions IICRC standards, drying logs, moisture mapping, smoke/soot/HVAC contamination, hail test squares, ridge cap, starter strip, or asks for a fire / water / storm specific review. Auto-routes to roofing.md, water.md, or fire.md based on loss type.
---

# Type-of-Loss Audit (Stage 5 of 13)

Goal: re-examine the entire estimate through the lens of the specific peril(s) that caused the loss. The carrier's estimate may pass a generic line-item check but still miss peril-specific items.

## Step 0 — Read the protocols

Use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read the entire file end-to-end before doing anything else in this stage. Do this every time this skill is invoked.

## Prerequisite

Stages 1–4 confirmed complete.

## Step 1 — Confirm the type(s) of loss

Ask the user (or infer from FNOL and carrier estimate). Then `Read` whichever reference file(s) apply:

- Wind / hail / storm (roofing and exterior) → `Read` `references/roofing.md`
- Water / flood → `Read` `references/water.md`
- Fire / smoke → `Read` `references/fire.md`

A single loss can involve multiple perils. A fire claim almost always has a major water component (suppression water from the fire department). A storm claim may have water intrusion. Read and apply every reference file that fits.

The reference files are **starting-point checklists, not exhaustive**. Apply additional industry-standard guidance for the specific peril and the specific project.

For each peril identified, state explicitly which reference file(s) you are using and why.

## Step 2 — Walk the relevant reference(s), one macro-area at a time

Work **one macro-area at a time** (§2.8 of the protocols). Read `outputs/macro-areas.md` and apply each peril checklist within the macro-areas it actually touches — e.g., roofing/exterior checklist items land in the *Exterior & Roof* macro-area; water-mitigation items land in the affected interior macro-areas. Walk the macro-areas in order, ask the per-macro-area gate at each boundary (see Verification gate below), then move on.

For each item on each applicable checklist (within the current macro-area):

1. Use `Read` on the carrier PDF and confirm whether the carrier's estimate (after Stages 2–4) already covers the item.
2. If yes, note the carrier's item number and move on.
3. If no, recommend the addition with proper labeling per the Carrier Estimate Protocol.
4. Run the Audit-Myopia check before finalizing each addition.
5. Use `WebSearch` to verify any peril-specific industry standard or formula (IICRC equipment formulas, hail-strike thresholds, structural-engineer-letter requirements) before citing it.

## Step 3 — Subdivide aggressively

Type-of-loss audits hit token limits faster than most stages because they cut across the whole estimate, not just one room. Propose subdivision early — for a multi-peril fire+water claim, run fire first (with explicit user confirmation), then water.

## Output

Substantive — four-section format per peril segment plus verified/unverified facts.

**Recommendations** lists items added per peril with cited reference and Xactimate labeling.

## Stage output (§2.9)

This stage's deliverable is the **peril-specific findings record** — the items each applicable peril checklist (roofing / water / fire) flagged as missing, with the cited standard and labeling. Record it in `outputs/stage-outputs/05-type-of-loss.md`, organized by macro-area (note which peril drove each area's findings), and record its findings in the consolidated audit-findings artifact (`claim-audit-findings`, §2.9) — this stage's entry. Build incrementally; markdown is canonical.

## Stay in this stage's lane

Per §2.10 of the protocols, this stage decides only **peril-specific items the carrier missed (roofing/hail/wind, water per IICRC S500/S520, or fire/smoke)**. It re-scans the estimate through the lens of the specific peril.

While doing it you will see things that belong to other stages — generic line-item pricing or quantity (Stage 2), Material/Equipment/Labor completeness (Stage 3), companion items (Stage 4), exterior structures (Stage 6), or code upgrades (Stage 7). Do not mention them, do not ask whether to flag them, and do not record them anywhere. Drop them; the owning stage re-examines the whole estimate and will catch them. Noticing an out-of-stage item and asking whether to flag it is the §2.10 violation to avoid.

## Recording suggestions in the suggestion list

For every peril-specific suggestion this stage produces (e.g., missing starter shingles, missing antimicrobial on a Cat 2 water claim, missing ozone-replacement odor neutralization on a fire claim), walk each one through the per-suggestion confirmation flow defined in §2.3 of the protocols: call `AskUserQuestion` per suggestion with options Accept / Reject / Modify / Ask a question. Only Accepted entries get appended to `outputs/audit-suggestion-list.md` (disposition `Agreed`). Refresh the live artifact after each append.

**Strict per-suggestion flow (§2.3).** Every suggestion above gets its **own** `AskUserQuestion` call — one suggestion per call. Do not batch them, do not replace them with a single "shall I add these?" question, and do not ask the verification gate until every suggestion this stage produced has been individually Accepted, Rejected, or Modified-then-Accepted.

## Verification gate

Per-macro-area (§2.8), after finishing a macro-area:

> "Do you believe the Type of Loss Audit for [Macro-area] is complete? If not, please direct me to the incomplete item(s)."

When you believe this stage is complete (across all macro-areas and all applicable perils):

> "Do you believe the Type of Loss Audit is complete? If not, please direct me to the incomplete item(s)."

After the user confirms, route per §4 of the protocols (which honors the audit mode in `outputs/audit-progress.md`). The next stage is **Appurtenances Audit** (skill: `claim-appurtenances-audit`).

In single-session mode, §4 prompts *"Ready for Appurtenances Audit."* and waits for "begin appurtenances audit" (or equivalent) before chaining. In multi-session mode, §4 prints the multi-session hand-off and stops here — the user begins the Appurtenances Audit in a fresh chat in this same Cowork project.

## Reference files

- `references/roofing.md` — wind, hail, storm exterior damage
- `references/water.md` — water mitigation per IICRC S500 / S520
- `references/fire.md` — fire, smoke, soot, odor restoration

---
name: claim-code-ordinance-law-audit
description: Stage 7 of the CCS forensic claim audit. Identify every line item subject to building code, ordinance, or law upgrade requirements (insulation R-value, AFCI/GFCI, hardwired smoke detectors, seismic retrofit, energy-code windows, accessibility), then audit the carrier's coverage and trigger the Ordinance & Law rider where applicable. Trigger after the Appurtenances Audit, or when the user asks about code upgrades, O&L coverage, "is the building code rider triggered," asks about R-value, AFCI breakers, hardwired smoke detectors, energy-code windows, or seismic retrofit. Three explicit sub-steps with confirmation between each — do not collapse them.
---

# Code, Ordinance & Law Audit (Stage 7 of 13)

Goal: trigger and quantify the Ordinance & Law rider on the policy. This is one of the most lucrative and most-frequently-missed categories. Standard policies cover "like kind and quality" — they do NOT cover the cost of bringing an old structure up to current code unless the O&L rider is invoked, and carriers will not volunteer it.

## Step 0 — Read the protocols

Use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read the entire file end-to-end before doing anything else in this stage. Do this every time this skill is invoked. The Material Fact Verification rule (§1.2) and the Tool Usage table (§7) are critical here — every code citation must be live-search-verified via `WebSearch` against a real, currently-enforced municipal code in this project's jurisdiction.

**§1.5 reminder — every suggestion this stage raises needs its plain-language Why + Source.** In basic language: what's wrong or missing and why the fix is justified, plus the basis it rests on — a named project file, a verified citation, or an openly flagged judgment call. No Why or no Source means it isn't ready: don't propose it and don't record it (§1.5 completeness gate, §2.3).

## Prerequisite — enforced gate (refuse until met)

Run this check before any work in this stage, per §2.14 of the protocols. Re-check on every attempt — never warn once and proceed.

1. **Active project.** `outputs/audit-progress.md` must exist (setup has run). If it doesn't, this isn't an active claim project yet: refuse, tell the user to run `/claim-audit-setup` first, and stop.
2. **Sequence.** In `outputs/audit-progress.md`, Stage 6 (Appurtenances Audit) must be `Complete` or `Skipped`. If it isn't, refuse, point the user to `/claim-appurtenances-audit`, and stop.

Proceed only when both pass.

## Macro-area handling

This stage **gathers area by area, then rolls up globally** (§2.8 of the protocols). Read `outputs/macro-areas.md`. In Sub-step (a), walk the estimate one macro-area at a time to find code-impacted items, asking the per-macro-area gate at each boundary:

> "Do you believe the code-impacted-item list for [Macro-area] is complete? If not, please direct me to the missing items."

Sub-steps (b) and (c) then operate on the full assembled list. The Ordinance & Law rider trigger is a **single project-wide determination** — do not try to trigger or quantify it one macro-area at a time. Gather the impacted items area by area; make the rider determination once, across the whole property.

## Three-step structure — do not collapse

This audit has three sub-steps with user confirmation between each. Do not move to step (b) until the user confirms step (a), and so on.

### Sub-step (a) — Build the list of potentially code-impacted items

Use `Read` on the carrier PDF and walk the entire current estimate (carrier original + every supplement to date). For each line item, ask: *is this item subject to a code, ordinance, or law requirement?*

Use `Read` on `references/potentially-code-impacted-items.md` for the starting-point list of categories that typically are subject to code (and the categories that typically are not). The reference is a **starting point, not exhaustive** — apply additional industry-standard guidance for the specific project and jurisdiction.

Output the list. Then ask:

> "Here is the list of potentially code-impacted items. Do you believe this list is complete? If not, please direct me to the missing items."

Wait for user confirmation. Do not proceed.

### Sub-step (b) — Audit the list vs. the carrier's estimate

For each item on the agreed list, use `Read` on the carrier PDF:

- What does the carrier's estimate currently provide for this item? (Item number, quantity, spec.)
- Does that provision satisfy the current code requirement?
- If not, what is the gap?

Output the comparison table. Then ask:

> "Here is the gap analysis. Do you agree with the identified gaps? If not, please direct me to any item that needs revision."

Wait for user confirmation. Do not proceed.

### Sub-step (c) — Generate item-by-item corrections, with citations

For each gap, produce a supplement line item with:

- Carrier line being corrected (item number + title from the PDF)
- Proposed correction (quantity, spec, M/E/L, unit price hypothesis)
- **Specific code citation** — section number, year of adoption, the specific municipal/county/state body that adopted it. Use `WebSearch` to verify before citing.
- **Proof of enforcement** — see below
- Label per Carrier Estimate Protocol (`item b` / `Supp-1a` if carrier already uses sub-letters / `Supp-New`)

#### "Enforcement" is the bar, not "existence"

Per industry practice, it is legally insufficient that a code merely exists in a manual. The contractor must prove the local building official is **actively enforcing** it for *this specific repair project*. See `references/potentially-code-impacted-items.md` for the starting-point list of acceptable enforcement evidence types. Do not assert enforcement you cannot prove.

#### Bifurcate repair cost from upgrade cost

The supplement must clearly separate (1) the cost to repair the original damage and (2) the additional cost of the code-required upgrade. This is what triggers the O&L rider rather than the dwelling coverage.

## Live-search every code

Every code citation goes through §1.2 verification using `WebSearch`. Verify:

- Code is currently adopted in this jurisdiction (year of model code + local amendments)
- Section number is correct
- Threshold for application is met (e.g., "X% of dwelling damage triggers Y rule")

If verification is paywalled (some municipal codes are): follow the unverified-fact + paywall protocol from `claim-audit-protocols` §1.3.

## Output

Substantive — four-section format. The verified/unverified facts section is heavy here — every code is a verified fact with link to the adopting jurisdiction's code page.

## Stage output (§2.9)

This stage's deliverable is the **Ordinance & Law record**: the list of code-impacted items (gathered area by area), the gap analysis against the carrier's estimate, and the item-by-item corrections — each with its code citation, proof of enforcement, and the repair-cost-vs-upgrade-cost bifurcation — plus the project-wide O&L rider determination. Record it in `outputs/stage-outputs/07-code-ordinance.md`, with the impacted-items/gap sections organized by macro-area and the rider determination as a single project-wide section, and record its findings in the consolidated audit-findings artifact (`claim-audit-findings`, §2.9) — this stage's entry. Markdown is canonical.

## Stay in this stage's lane

Per §2.10 of the protocols, this stage decides only **which line items are subject to a building-code, ordinance, or law upgrade, and whether the Ordinance & Law rider is triggered**. It bifurcates like-kind repair from code-driven upgrade.

While doing it you will see things that belong to other stages — the base repair scope, price, or quantity (Stages 2–4), peril-specific items (Stage 5), or exterior structures (Stage 6). Do not mention them, do not ask whether to flag them, and do not record them anywhere. Drop them; the owning stage re-examines the whole estimate and will catch them. Noticing an out-of-stage item and asking whether to flag it is the §2.10 violation to avoid.

## Recording suggestions in the suggestion list

For every code-upgrade suggestion this stage produces (Sub-step c output — code-cited corrections), walk each one through the per-suggestion confirmation flow defined in §2.3 of the protocols: call `AskUserQuestion` per suggestion with options Accept / Reject / Modify / Ask a question. Only Accepted entries get appended to `outputs/audit-suggestion-list.md` (disposition `Agreed`). Refresh the live artifact after each append.

**Strict per-suggestion flow (§2.3).** Every suggestion above gets its **own** `AskUserQuestion` call — one suggestion per call. Do not batch them, do not replace them with a single "shall I add these?" question, and do not ask the verification gate until every suggestion this stage produced has been individually Accepted, Rejected, or Modified-then-Accepted.

(Sub-step a — the list of potentially code-impacted items — and Sub-step b — the gap analysis — are user-confirmation gates, not suggestion gates. The per-suggestion flow applies to Sub-step c only.)

## Verification gate

> "Do you believe the Code, Ordinance, and Law Audit is complete? If not, please direct me to the incomplete item(s)."

After the user confirms, route per §4 of the protocols (which honors the audit mode in `outputs/audit-progress.md`). The next stage is **Continuity / Room-Myopia Audit** (skill: `claim-continuity-audit`).

In single-session mode, §4 prompts *"Ready for Continuity / Room-Myopia Audit."* and waits for "begin continuity audit" (or equivalent) before chaining. In multi-session mode, §4 prints the multi-session hand-off and stops here — the user begins the Continuity / Room-Myopia Audit in a fresh chat in this same Cowork project.

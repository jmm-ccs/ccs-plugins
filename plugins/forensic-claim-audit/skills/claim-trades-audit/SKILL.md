---
name: claim-trades-audit
description: Stage 11 of the CCS forensic claim audit. Audit and reconstruct the Xactimate Trade Summary — confirm the trade list, every line item is correctly assigned to one trade, and the trade summary numbers reconcile to the line-item detail. Trigger after the Cleanup & Occupant Protection Audit, or when the user asks about Xactimate Trade Summary reconciliation, missing trades, line items not rolling up to the right trade, or whether the trade list supports O&P / supervision math. Six explicit sub-steps with confirmation between them.
---

# Trades Audit (Stage 11 of 13)

Goal: produce a clean, reconciled Trade Summary. The trade count and trade list become the input to the Permits & Contractor Cost Audit (which decides whether O&P and Project Supervision are warranted).

## Step 0 — Read the protocols

Use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read the entire file end-to-end before doing anything else in this stage. Do this every time this skill is invoked.

**§1.5 reminder — every suggestion this stage raises needs its plain-language Why + Source.** In basic language: what's wrong or missing and why the fix is justified, plus the basis it rests on — a named project file, a verified citation, or an openly flagged judgment call. No Why or no Source means it isn't ready: don't propose it and don't record it (§1.5 completeness gate, §2.3).

## Prerequisite — enforced gate (refuse until met)

Run this check before any work in this stage, per §2.14 of the protocols. Re-check on every attempt — never warn once and proceed.

1. **Active project.** `outputs/audit-progress.md` must exist (setup has run). If it doesn't, this isn't an active claim project yet: refuse, tell the user to run `/claim-audit-setup` first, and stop.
2. **Sequence.** In `outputs/audit-progress.md`, Stage 10 (Cleanup & Occupant Protection Audit) must be `Complete` or `Skipped`. If it isn't, refuse, point the user to `/claim-cleanup-protection-audit`, and stop.

Proceed only when both pass.

## Macro-area handling

This stage **gathers area by area, then reconciles globally** (§2.8 of the protocols). Read `outputs/macro-areas.md`. In Sub-step (3), build the line-item-to-trade mapping one macro-area at a time so no line item is missed. But the trade list, the reconciliation (Sub-step 4), and the Trade Summary itself are **project-wide** — a trade spans the whole property, and the distinct-trade *count* that drives O&P and Project Supervision downstream is a single global number. Gather the mapping area by area; produce the trade list, reconciliation, and Trade Summary once, across the whole estimate. Never reconcile or count trades one macro-area at a time.

## Six-step structure — do not collapse

This stage has six sub-steps with explicit confirmations between them. Do not skip ahead.

### (1) Generate the list of trades you believe the project requires

Use `Read` on `references/common-trades.md` for the starting-point list of residential trades. The reference is a **starting point, not exhaustive** — pick what applies, do not include trades you cannot tie to a real line item, and add additional trades the project requires.

Output the trade list with the rationale for each.

### (2) Confirm with the user

> "Here is my proposed trade list. Do you agree, or are there trades to add or remove?"

Wait for confirmation. Do not proceed.

### (3) Generate the line-item-to-trade mapping

For each agreed trade, list every line item in the current estimate that belongs to it. Use `Read` on the carrier PDF + supplement for exact item numbers and titles.

### (4) Reconcile — every single line item, accounted for

This is the audit's tripwire. Cross-check: is every line item in the current estimate (carrier original + every supplement to date) assigned to exactly one trade? Track:

- **Assigned**: line item appears under exactly one trade. ✓
- **Unassigned**: line item not under any trade — list it explicitly with the question: *"What trade should this be under?"*
- **Multiply assigned**: line item appears under more than one trade — explain why and propose the resolution.

Output the unassigned and multiply-assigned lists. Then ask:

> "Here are the line items that did not cleanly map to a single trade. How would you like each handled?"

Wait for the user's directions on each.

### (5) Final trade-line-item reconciliation, confirmed

Apply the user's directions, regenerate the mapping, and confirm:

> "Here is the reconciled trade-to-line-item mapping. Do you agree, or are there corrections?"

Wait for confirmation.

### (6) Trade Summary corrections

Compare your reconciled summary against the carrier's Trade Summary section. Recommend corrections — added trades, missing line items per trade, removed trades — preserving the carrier's existing summary structure per Carrier Estimate Protocol.

## Output

Substantive — four-section format across the sub-steps. The reconciled trade-to-line-item mapping is the persistent artifact this stage produces.

## Stage output (§2.9)

This stage's deliverable is the **reconciled Trade Summary** — the agreed trade list, the full trade-to-line-item mapping (every line item assigned to exactly one trade), and the distinct-trade count. This is a shared artifact: Stage 12 (Permits & Contractor Cost) reads it to decide O&P and Project Supervision, so it must be a file, not just chat. Record it in `outputs/stage-outputs/11-trades.md` and record its findings in the consolidated audit-findings artifact (`claim-audit-findings`, §2.9) — this stage's entry. Since trades span the property, organize by trade (not by macro-area). Markdown is canonical.

## Stay in this stage's lane

Per §2.10 of the protocols, this stage decides only **the Xactimate Trade Summary — every line item assigned to exactly one trade, and the trade totals reconciled to the line-item detail**. It classifies and reconciles what's already on the estimate; it does not re-audit scope.

While doing it you will see things that belong to other stages — whether a line item is missing, mis-priced, or incomplete (earlier stages), or the O&P / Project Supervision math (Stage 12). Do not mention them, do not ask whether to flag them, and do not record them anywhere. Drop them; the owning stage re-examines the whole estimate and will catch them. Noticing an out-of-stage item and asking whether to flag it is the §2.10 violation to avoid.

## Recording suggestions in the suggestion list

For every Trade Summary correction this stage produces (Sub-step 6 output — added trades, line-item-to-trade reassignments, removed trades), walk each one through the per-suggestion confirmation flow defined in §2.3 of the protocols: call `AskUserQuestion` per suggestion with options Accept / Reject / Modify / Ask a question. Only Accepted entries get appended to `outputs/audit-suggestion-list.md` (disposition `Agreed`). Refresh the live artifact after each append.

**Strict per-suggestion flow (§2.3).** Every suggestion above gets its **own** `AskUserQuestion` call — one suggestion per call. Do not batch them, do not replace them with a single "shall I add these?" question, and do not ask the verification gate until every suggestion this stage produced has been individually Accepted, Rejected, or Modified-then-Accepted.

(Sub-steps 1–5 — generating the trade list, mapping line items, reconciling unassigned/multiply-assigned items — are user-confirmation gates within the stage, not suggestion gates. The per-suggestion flow applies to Sub-step 6 only.)

## Verification gate

> "Do you believe the Trades Audit is complete? If not, please direct me to the incomplete item(s)."

After the user confirms, route per §4 of the protocols (which honors the audit mode in `outputs/audit-progress.md`). The next stage is **Permits and Contractor Cost Audit** (skill: `claim-permits-contractor-cost-audit`).

In single-session mode, §4 prompts *"Ready for Permits and Contractor Cost Audit."* and waits for "begin permits audit" (or equivalent) before chaining. In multi-session mode, §4 prints the multi-session hand-off and stops here — the user begins the Permits and Contractor Cost Audit in a fresh chat in this same Cowork project.

## Why this stage matters for downstream

The number of distinct trades determines whether O&P and Project Supervision are warranted (per the Permits & Contractor Cost Audit). It also drives the permit list. So the *count* of distinct trades produced here is a load-bearing number.

---
name: claim-cleanup-protection-audit
description: Stage 10 of the CCS forensic claim audit. Audit during-construction occupant protection (HVAC return masking, dust barriers, negative-air containment, poly between zones) and post-construction cleanup (final clean, duct cleaning, air quality testing, HEPA vacuuming). Trigger after the Storage/Debris Audit, or when the user asks about dust protection, negative air, HVAC masking during sanding, post-construction cleaning, duct cleaning, air quality testing, or when occupants are in the home during work.
---

# Cleanup & Occupant Protection Audit (Stage 10 of 13)

Goal: ensure the estimate properly accounts for protections during construction and cleanup after construction.

## Step 0 — Read the protocols

Use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read the entire file end-to-end before doing anything else in this stage. Do this every time this skill is invoked.

**§1.5 reminder — every suggestion this stage raises needs its plain-language Why + Source.** In basic language: what's wrong or missing and why the fix is justified, plus the basis it rests on — a named project file, a verified citation, or an openly flagged judgment call. No Why or no Source means it isn't ready: don't propose it and don't record it (§1.5 completeness gate, §2.3).

## Prerequisite

Stages 1–9 confirmed complete.

## During-construction protections and post-construction cleanup

Use `Read` on `references/protections-and-cleanup.md` for the starting-point lists of (a) during-construction protections and (b) post-construction cleanup operations. The reference is a **starting point, not exhaustive** — apply additional industry-standard protections and cleanup operations appropriate to the trade, project conditions, and occupant situation.

Use `Read` on the carrier PDF + supplement to walk every active demolition and finish-trade line item in the current estimate, and identify which protections and cleanup items the project requires.

## Method

Work **one macro-area at a time** (§2.8 of the protocols). Read `outputs/macro-areas.md`. Protections and cleanup are largely zone-specific (a dust barrier or negative-air containment belongs to the area where the work happens), so walk the macro-areas in order and ask the per-macro-area gate at each boundary: *"Do you believe the Cleanup and Occupant Protection Audit for [Macro-area] is complete?…"*

1. For the current macro-area, inventory the ongoing operations in the current estimate using `Read` on the carrier PDF + supplement.
2. For each, identify required during-construction protections and confirm they're scoped.
3. Identify post-construction cleanup items appropriate to the project and confirm they're scoped.
4. Audit-Myopia check — some protections (dust barriers, HEPA scrubbers) may already be accounted for in Stage 5 (water/fire) or Stage 8 (continuity). Don't double-count.
5. Recommend additions per Carrier Estimate Protocol labeling.

## Output

Substantive — four-section format. **Recommendations** in two sections — During-Construction Protections and Post-Construction Cleanup — with line-item tables.

## Stage output (§2.9)

This stage's deliverable is the **protections-and-cleanup record** — the during-construction protections and post-construction cleanup the project requires and whether each is scoped. Record it in `outputs/stage-outputs/10-cleanup-protection.md`, organized by macro-area (protections are largely zone-specific), and record its findings in the consolidated audit-findings artifact (`claim-audit-findings`, §2.9) — this stage's entry. Build incrementally; markdown is canonical.

## Stay in this stage's lane

Per §2.10 of the protocols, this stage decides only **during-construction occupant protection (dust barriers, negative air, HVAC masking) and post-construction cleanup (final clean, duct cleaning, air-quality testing)**. It covers protection while work happens and cleanup after.

While doing it you will see things that belong to other stages — the construction line items themselves (earlier stages) or debris hauling and disposal (Stage 9). Do not mention them, do not ask whether to flag them, and do not record them anywhere. Drop them; the owning stage re-examines the whole estimate and will catch them. Noticing an out-of-stage item and asking whether to flag it is the §2.10 violation to avoid.

## Recording suggestions in the suggestion list

For every protection-or-cleanup suggestion this stage produces (during-construction protections, post-construction cleanup additions), walk each one through the per-suggestion confirmation flow defined in §2.3 of the protocols: call `AskUserQuestion` per suggestion with options Accept / Reject / Modify / Ask a question. Only Accepted entries get appended to `outputs/audit-suggestion-list.md` (disposition `Agreed`). Refresh the live artifact after each append.

**Strict per-suggestion flow (§2.3).** Every suggestion above gets its **own** `AskUserQuestion` call — one suggestion per call. Do not batch them, do not replace them with a single "shall I add these?" question, and do not ask the verification gate until every suggestion this stage produced has been individually Accepted, Rejected, or Modified-then-Accepted.

## Verification gate

> "Do you believe the Cleanup and Occupant Protection Audit is complete? If not, please direct me to the incomplete item(s)."

After the user confirms, route per §4 of the protocols (which honors the audit mode in `outputs/audit-progress.md`). The next stage is **Trades Audit** (skill: `claim-trades-audit`).

In single-session mode, §4 prompts *"Ready for Trades Audit."* and waits for "begin trades audit" (or equivalent) before chaining. In multi-session mode, §4 prints the multi-session hand-off and stops here — the user begins the Trades Audit in a fresh chat in this same Cowork project.

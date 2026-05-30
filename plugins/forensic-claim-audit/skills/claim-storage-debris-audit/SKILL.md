---
name: claim-storage-debris-audit
description: Stage 9 of the CCS forensic claim audit. Audit personal-property pack-out / moving / storage and construction-debris removal / disposal — dumpsters, hauling, tonnage codes, hazmat disposal, recycling fees. Trigger after the Continuity Audit, or when the user asks about pack-out, contents storage, dumpster, debris, hauling, tonnage, or whether disposal is properly scoped. The current scope of demolition and replacement (which has grown across Stages 2–8) drives storage and debris quantities — recompute, do not copy old numbers.
---

# Storage, Debris & Disposal Audit (Stage 9 of 13)

Goal: re-audit the entire estimate for industry-standard moving/storage of personal property and construction debris disposal — based on the *current updated* scope, not the carrier's original.

## Step 0 — Read the protocols

Use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read the entire file end-to-end before doing anything else in this stage. Do this every time this skill is invoked.

**§1.5 reminder — every suggestion this stage raises needs its plain-language Why + Source.** In basic language: what's wrong or missing and why the fix is justified, plus the basis it rests on — a named project file, a verified citation, or an openly flagged judgment call. No Why or no Source means it isn't ready: don't propose it and don't record it (§1.5 completeness gate, §2.3).

## Prerequisite

Stages 1–8 confirmed complete. The scope has grown materially across those stages — that growth changes both content storage volume and debris tonnage, so the carrier's original numbers are almost certainly stale.

## Storage and debris categories

Use `Read` on `references/storage-and-debris.md` for the starting-point lists of (a) personal-property storage / pack-out categories and (b) construction debris and disposal categories with localized tonnage conversion factors. The reference is a **starting point, not exhaustive** — apply additional industry-standard considerations as the project warrants.

Debris quantity is driven by what's being torn out. Use `Read` on the carrier PDF + supplement to inventory every demolition and removal line item, then apply the conversion factors and use `bash` with Python for the actual sums.

## Method

This stage **gathers area by area, then rolls up globally** (§2.8 of the protocols). Read `outputs/macro-areas.md`. Walk the rooms macro-area by macro-area to gather volumes and tonnage — but the project totals (and the dumpster/storage line items they justify) are a **single global rollup**. Never compute a project total one macro-area at a time; gather per area, sum once (§1.4).

1. Use `Read` to re-inventory all rooms in scope, grouped by macro-area.
2. For each room (walking one macro-area at a time), list:
   - Personal-property volume (boxes, furniture pieces, special items)
   - Demolition tonnage by material type
   - Ask the per-macro-area gate (§2.8) before moving to the next area: *"Do you believe the storage/debris inventory for [Macro-area] is complete?…"*
3. After all macro-areas are gathered, aggregate to project totals using `bash` with Python — do not predict sums in your head, and do not partial-sum per area into the final figure separately.
4. Compare against carrier's existing storage and debris line items.
5. Recommend additions and corrections per Carrier Estimate Protocol labeling.
6. Audit-Myopia check — many demolition lines added in Stages 2–5 have implicit debris consequences that may already be partially scoped.

## Output

Substantive — four-section format. **Recommendations** in two clear sections — Personal Property Storage and Construction Debris Disposal — each with line-item tables.

## Stage output (§2.9)

This stage's deliverable is the **recomputed storage/debris record** — personal-property storage volumes and demolition tonnage gathered per macro-area, the project totals from the global rollup (with the `bash` math), and the resulting additions/corrections vs. the carrier. Record it in `outputs/stage-outputs/09-storage-debris.md`, with the per-area gather organized by macro-area and the totals as a single rollup section, and record its findings in the consolidated audit-findings artifact (`claim-audit-findings`, §2.9) — this stage's entry. Markdown is canonical.

## Stay in this stage's lane

Per §2.10 of the protocols, this stage decides only **personal-property pack-out/storage and construction-debris removal/disposal, computed from the current updated scope**. It sizes storage and debris from the scope the earlier stages produced.

While doing it you will see things that belong to other stages — the repair or demolition line items that generate the debris (those were scoped in Stages 2–8 — don't re-open or re-price them), or occupant protection and cleanup (Stage 10). Do not mention them, do not ask whether to flag them, and do not record them anywhere. Drop them; the owning stage re-examines the whole estimate and will catch them. Noticing an out-of-stage item and asking whether to flag it is the §2.10 violation to avoid.

## Recording suggestions in the suggestion list

For every storage-or-debris suggestion this stage produces (pack-out / storage additions, debris/tonnage corrections, hazmat/specialty hauling), walk each one through the per-suggestion confirmation flow defined in §2.3 of the protocols: call `AskUserQuestion` per suggestion with options Accept / Reject / Modify / Ask a question. Only Accepted entries get appended to `outputs/audit-suggestion-list.md` (disposition `Agreed`). Refresh the live artifact after each append.

**Strict per-suggestion flow (§2.3).** Every suggestion above gets its **own** `AskUserQuestion` call — one suggestion per call. Do not batch them, do not replace them with a single "shall I add these?" question, and do not ask the verification gate until every suggestion this stage produced has been individually Accepted, Rejected, or Modified-then-Accepted.

## Verification gate

> "Do you believe the Storage, Debris, and Disposal Audit is complete? If not, please direct me to the incomplete item(s)."

After the user confirms, route per §4 of the protocols (which honors the audit mode in `outputs/audit-progress.md`). The next stage is **Cleanup and Occupant Protection Audit** (skill: `claim-cleanup-protection-audit`).

In single-session mode, §4 prompts *"Ready for Cleanup and Occupant Protection Audit."* and waits for "begin cleanup audit" (or equivalent) before chaining. In multi-session mode, §4 prints the multi-session hand-off and stops here — the user begins the Cleanup and Occupant Protection Audit in a fresh chat in this same Cowork project.

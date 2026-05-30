---
name: claim-permits-contractor-cost-audit
description: Stage 12 of the CCS forensic claim audit. Audit required permits (general + each trade-specific permit by jurisdiction) and contractor cost components — Overhead & Profit (10/10) and Project Supervision — per the Xactimate threshold rules. Trigger after the Trades Audit, or when the user asks about permit fees, building permit, electrical/plumbing/mechanical/roofing permits, O&P, "10 and 10," or Project Supervision (LAB SUP).
---

# Permits & Contractor Cost Audit (Stage 12 of 13)

Goal: ensure permits required by the project's jurisdiction are scoped, and apply Overhead & Profit and Project Supervision where the threshold rules trigger.

## Step 0 — Read the protocols

Use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read the entire file end-to-end before doing anything else in this stage. Do this every time this skill is invoked. The Material Fact Verification rule (§1.2) is critical — every permit fee and jurisdictional rule must be `WebSearch`-verified.

**§1.5 reminder — every suggestion this stage raises needs its plain-language Why + Source.** In basic language: what's wrong or missing and why the fix is justified, plus the basis it rests on — a named project file, a verified citation, or an openly flagged judgment call. No Why or no Source means it isn't ready: don't propose it and don't record it (§1.5 completeness gate, §2.3).

## Prerequisite

Stages 1–11 confirmed complete. The Trades Audit produced a reconciled trade list that drives this stage.

## Macro-area handling

This stage is a **project-wide rollup** (§2.8 of the protocols). Permits are issued by jurisdiction and trade, and O&P and Project Supervision are project-level figures computed off the whole estimate — none of them can be computed one macro-area at a time without corrupting the math (§1.4). Read `outputs/macro-areas.md` and use it only to confirm that every macro-area's work is represented in the totals the math runs on (so the project-cost sum and trade count aren't missing an area). Compute permits, O&P, and Supervision **once**, across the whole property.

## Part A — Permits

### Step 1 — Identify the jurisdiction

Determine the project's exact jurisdiction (city, county, special district). Use `WebSearch` to verify — permit requirements are jurisdiction-specific.

### Step 2 — List required permits by jurisdiction and trade

For each trade in the agreed Trades list:

- Does this jurisdiction require a separate trade permit?
- What is the fee structure (flat, valuation-based, square-footage-based)?
- Are there inspection fees in addition to the permit fee?

Use `Read` on `references/common-permits.md` for the starting-point list of permit categories to audit for. The reference is a **starting point, not exhaustive** — permit requirements are jurisdiction-specific, so use `WebSearch` to verify what this specific jurisdiction requires.

### Step 3 — Confirm against carrier estimate

Use `Read` on the carrier PDF. Is each required permit included? At what cost? Recommend additions for missing permits and corrections for under-priced ones, citing the jurisdiction's published fee schedule (verified via `WebSearch`).

## Part B — Overhead & Profit (O&P)

Apply the standard Xactimate rule:

- **If three or more distinct trades AND total project cost > $15,000** → 10% Overhead and 10% Profit ("10/10") apply across the estimate per standard Xactimate process.

Compute (use `bash` with Python for the actual math):

- Distinct trade count = the count from the agreed Trades List (Stage 11).
- Total project cost = sum of all line items (carrier + supplements to date), pre-tax, pre-O&P.

If both thresholds are met and the carrier's estimate does not include 10/10, recommend its application across the estimate. If the carrier applied O&P selectively (only on certain rooms or trades), recommend uniform application unless there's a documented reason to do otherwise.

## Part C — Project Supervision

Apply the standard Xactimate rule:

- **If three or more distinct trades AND total project cost > $25,000**, **OR if five or more distinct trades** → Project Supervision should be included.

The calculation per the source CCS process is **12% of total project cost**, using Xactimate labor code **LAB SUP**, footnoted with the calculation. Use `bash` with Python for the math.

Note: there is a parallel formulation in the field where Project Supervision is calculated as 12% of *total labor hours* × the market hourly rate for project supervision. Both formulations exist in practice; the source CCS process uses 12% of total project cost. If you encounter the labor-hours formulation in a specific jurisdiction or carrier, flag the discrepancy to the user and ask which they want applied.

## Output

Substantive — four-section format. **Recommendations** has three sub-sections — Permits, O&P, Project Supervision — each with the math shown and citations.

The verified-facts section should contain:

- Jurisdiction's permit fee schedule URL
- Trade-count and total-project-cost computation
- Source URL for any `WebSearch`-verified data

## Stage output (§2.9)

This stage's deliverable is the **permits + contractor-cost record** — the required permits by jurisdiction and trade with their fees, and the O&P and Project Supervision determinations with the `bash` math (trade count from `outputs/stage-outputs/11-trades.md`, total project cost). Record it in `outputs/stage-outputs/12-permits-contractor.md` and record its findings in the consolidated audit-findings artifact (`claim-audit-findings`, §2.9) — this stage's entry. These are project-wide figures, so organize by component (Permits / O&P / Supervision), not by macro-area. Markdown is canonical.

## Stay in this stage's lane

Per §2.10 of the protocols, this stage decides only **required permits, Overhead & Profit (10/10), and Project Supervision**. It applies the permit and contractor-cost rules to the reconciled scope.

While doing it you will see things that belong to other stages — the underlying line items (earlier stages), the trade list and Trade Summary (Stage 11), or sales tax (Stage 13). Do not mention them, do not ask whether to flag them, and do not record them anywhere. Drop them; the owning stage re-examines the whole estimate and will catch them. Noticing an out-of-stage item and asking whether to flag it is the §2.10 violation to avoid.

## Recording suggestions in the suggestion list

For every suggestion this stage produces (missing or under-priced permits, O&P additions, Project Supervision additions), walk each one through the per-suggestion confirmation flow defined in §2.3 of the protocols: call `AskUserQuestion` per suggestion with options Accept / Reject / Modify / Ask a question. Only Accepted entries get appended to `outputs/audit-suggestion-list.md` (disposition `Agreed`). Refresh the live artifact after each append.

**Strict per-suggestion flow (§2.3).** Every suggestion above gets its **own** `AskUserQuestion` call — one suggestion per call. Do not batch them, do not replace them with a single "shall I add these?" question, and do not ask the verification gate until every suggestion this stage produced has been individually Accepted, Rejected, or Modified-then-Accepted.

## Verification gate

> "Do you believe the Permits and Contractor Cost Audit is complete? If not, please direct me to the incomplete item(s)."

After the user confirms, route per §4 of the protocols (which honors the audit mode in `outputs/audit-progress.md`). The next stage is **Sales Tax Audit** (skill: `claim-sales-tax-audit`).

In single-session mode, §4 prompts *"Ready for Sales Tax Audit."* and waits for "begin sales tax audit" (or equivalent) before chaining. In multi-session mode, §4 prints the multi-session hand-off and stops here — the user begins the Sales Tax Audit in a fresh chat in this same Cowork project.

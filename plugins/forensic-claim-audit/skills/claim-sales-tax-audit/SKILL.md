---
name: claim-sales-tax-audit
description: Stage 13 of the CCS forensic claim audit — the final audit stage. Apply the correct sales tax to every line item based on the project's jurisdiction. Verify the local rate, verify whether the jurisdiction taxes labor as well as materials, then apply the per-line-item formulas (materials-only, labor-only, mixed M+L, neither). Trigger after the Permits & Contractor Cost Audit, or when the user asks about sales tax on the supplement, taxability of labor in the project's jurisdiction, or sales tax verification for an Xactimate estimate.
---

# Sales Tax Audit (Stage 13 of 13)

Goal: apply the correct sales tax to every line item, with the rate and the labor-taxability rule both verified by `WebSearch` against the project's jurisdiction.

## Step 0 — Read the protocols

Use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read the entire file end-to-end before doing anything else in this stage. Do this every time this skill is invoked.

**§1.5 reminder — every suggestion this stage raises needs its plain-language Why + Source.** In basic language: what's wrong or missing and why the fix is justified, plus the basis it rests on — a named project file, a verified citation, or an openly flagged judgment call. No Why or no Source means it isn't ready: don't propose it and don't record it (§1.5 completeness gate, §2.3).

## Prerequisite

Stages 1–12 confirmed complete.

## Step 1 — Verify the sales tax rate

Use `WebSearch` to verify the sales tax rate for the project's exact jurisdiction. Be specific:

- City rate
- County rate
- State rate
- Special district rates (transit, stadium, school, etc.)

Combined effective rate is the sum of all applicable layers. Cite each layer with its source URL.

If the project sits inside multiple overlapping jurisdictions (city + county + special district), confirm all layers apply.

## Step 2 — Verify labor taxability

Use `WebSearch` to verify whether the jurisdiction charges sales tax on **labor** as well as materials, specifically on construction/restoration services. Possible answers — these are **starting-point categories, not exhaustive**:

- Labor fully taxed (rare in construction)
- Labor not taxed (most common in residential construction)
- Labor partially taxed (e.g., installation services on tangible goods)
- Mixed-use rules where lump-sum vs. time-and-materials contracts are taxed differently

This rule is jurisdiction-specific and changes — the live-search verification is non-optional.

## Step 3 — Apply the formulas

Per the source CCS process, for each line item:

- **Materials only**:
  `tax = quantity × unit_price × sales_tax_rate`

- **Labor only**:
  - If labor is taxed in this jurisdiction:
    `tax = quantity × unit_price × sales_tax_rate`
  - If labor is not taxed:
    `tax = 0`

- **Materials + Labor (mixed line item)**:
  - If labor is taxed in this jurisdiction:
    `tax = quantity × unit_price × sales_tax_rate`
  - If labor is not taxed:
    `tax = quantity × unit_price × (sales_tax_rate / 2)`
  - (The half-rate approximation reflects the materials portion of a typical mixed line; if the line has a clearly identified materials/labor split, use the actual materials portion instead.)

- **Neither materials nor labor** (e.g., overhead, supervision, fees):
  `tax = 0`

If the jurisdiction has special construction-tax rules (e.g., contractor pays tax at material purchase rather than reseller-permits), flag this to the user — it changes who is invoicing whom for the tax.

## Step 4 — Apply to every line item, one macro-area at a time

This stage **gathers area by area, then totals globally** (§2.8 of the protocols). The rate and labor-taxability rule (Steps 1–2) are project-wide — verify them once. Then read `outputs/macro-areas.md` and walk the line items **one macro-area at a time**, applying the per-line-item formula within each, asking the per-macro-area gate at each boundary: *"Do you believe the sales-tax application for [Macro-area] is complete?…"* After all macro-areas, compute the **final tax totals once** across the whole estimate — don't carry per-area subtotals into the final figure separately.

Use `Read` on the carrier PDF + supplement to walk every line item. Apply the appropriate formula. Document the rate and rule used.

**Use `bash` with Python for every line-item tax calculation and the final totals.** Do not predict math in your head. Sample approach: build a list of `(qty, unit_price, type)` tuples and run a Python loop that applies the right formula per type, then sums.

Audit-Myopia check: tax on supplement-added items should not duplicate tax already shown on the carrier's pre-existing items.

## Output

Substantive — four-section format. **Recommendations** is the line-item tax application table:

| # | Item | M / L / M+L / Neither | Quantity × Unit Price | Formula applied | Tax |

Plus a totals roll-up.

Verified-facts section must include:

- The sales tax rate(s) and source URL for each layer
- The labor-taxability rule and source URL

## Stage output (§2.9)

This stage's deliverable is the **sales-tax record** — the verified rate layers and labor-taxability rule, the per-line-item tax table (with the formula applied to each), and the final tax total from the global rollup (with the `bash` math). Record it in `outputs/stage-outputs/13-sales-tax.md`, with the per-line-item table grouped by macro-area and the total as a single rollup section, and record its findings in the consolidated audit-findings artifact (`claim-audit-findings`, §2.9) — this stage's entry. Markdown is canonical.

## Stay in this stage's lane

Per §2.10 of the protocols, this stage decides only **the correct sales tax on every line item for the project's jurisdiction**. By now the lines are settled — this stage touches only tax.

While doing it you will see things that belong to other stages — anything about a line item's scope, price, quantity, grade, or completeness (all of Stages 2–12). Do not mention them, do not ask whether to flag them, and do not record them anywhere. Drop them; the owning stage re-examines the whole estimate and will catch them. Noticing an out-of-stage item and asking whether to flag it is the §2.10 violation to avoid.

## Recording suggestions in the suggestion list

For every sales-tax suggestion this stage produces (per-line-item tax additions, special construction-tax-rule flags), walk each one through the per-suggestion confirmation flow defined in §2.3 of the protocols: call `AskUserQuestion` per suggestion with options Accept / Reject / Modify / Ask a question. Only Accepted entries get appended to `outputs/audit-suggestion-list.md` (disposition `Agreed`). Refresh the live artifact after each append.

**Strict per-suggestion flow (§2.3).** Every suggestion above gets its **own** `AskUserQuestion` call — one suggestion per call. Do not batch them, do not replace them with a single "shall I add these?" question, and do not ask the verification gate until every suggestion this stage produced has been individually Accepted, Rejected, or Modified-then-Accepted.

## Verification gate

> "Do you believe the Sales Tax Audit is complete? If not, please direct me to the incomplete item(s)."

After the user confirms, route per §4 of the protocols (which honors the audit mode in `outputs/audit-progress.md`). The next step is **Final Delivery** (skill: `claim-audit-finalizer`) — Stage 13 is the last audit stage, and Final Delivery runs the Sanity Audit, exports the suggestion list to XLSX, produces the annotated carrier PDF, and generates the supplement package document.

In single-session mode, §4 prompts *"Ready for Output Process."* and waits for "begin output process" (or equivalent) before chaining into `claim-audit-finalizer`. In multi-session mode, §4 prints the multi-session hand-off (substituting "Final Delivery" / `claim-audit-finalizer` for the next-stage values) and stops here — the user begins Final Delivery in a fresh chat in this same Cowork project.

This is the last audit stage. The next skill to invoke is `claim-audit-finalizer`. (`claim-supplement-generator` is deprecated — see its SKILL.md for details.)

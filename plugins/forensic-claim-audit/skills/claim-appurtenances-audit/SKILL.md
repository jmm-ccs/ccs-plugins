---
name: claim-appurtenances-audit
description: Stage 6 of the CCS forensic claim audit. Audit damage to structures outside the primary dwelling — siding, fencing, landscaping, decks, pools, sheds, retaining walls, driveways, gates, mailboxes, outdoor lighting, irrigation. Trigger after the Type-of-Loss Audit, or when the user asks "did the carrier scope the fence / siding / deck / pool / landscaping," when project photos show damaged exterior structures, or after a wind/hail event. Each appurtenance gets the line-item + completeness pattern from Stages 2–3.
---

# Appurtenances Audit (Stage 6 of 13)

Goal: identify exterior structures the carrier missed entirely or scoped inaccurately, then run the full line-item + completeness pattern on each.

## Step 0 — Read the protocols

Use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read the entire file end-to-end before doing anything else in this stage. Do this every time this skill is invoked.

**§1.5 reminder — every suggestion this stage raises needs its plain-language Why + Source.** In basic language: what's wrong or missing and why the fix is justified, plus the basis it rests on — a named project file, a verified citation, or an openly flagged judgment call. No Why or no Source means it isn't ready: don't propose it and don't record it (§1.5 completeness gate, §2.3).

## Prerequisite

Stages 1–5 confirmed complete.

## Method

Work **one macro-area at a time** (§2.8 of the protocols). Appurtenances live in the exterior and detached-structure macro-areas. Read `outputs/macro-areas.md`, walk those macro-areas in order, and within each treat each appurtenance as the working unit. Ask the per-macro-area gate at each boundary (see Verification gates). If the map has no exterior/detached macro-area but the photos show appurtenances, that's a scope gap — note it and add the macro-area to the map per §2.8 before proceeding.

### Step 1 — Inventory all appurtenances on the property

Use `Read` on project documentation (photos, sketches, satellite imagery, Matterport exterior, walk-around video) to build a complete list of structures outside the dwelling.

Use `Read` on `references/appurtenance-categories.md` for the starting-point list of appurtenance categories to inventory. The reference is a **starting point, not exhaustive** — apply additional industry-standard considerations for the specific property.

### Step 2 — Compare against the carrier's estimate

For each appurtenance, use `Read` on the carrier PDF and confirm:

- Is it on the carrier's estimate? Note the carrier's line items.
- Is the damage scope accurate against the project documentation?
- For **discontinued products** (siding profile no longer made, fence pickets in a discontinued color/profile), document the discontinuation (use `WebSearch` to verify discontinuation if needed) and argue for full-elevation or full-line replacement under the policy's matching language.

### Step 3 — Run the line-item + completeness pattern on each appurtenance

For every appurtenance — whether already on the estimate or being added new — apply the Stage 2 + Stage 3 pattern:

- Line item exists with correct quantity, unit, grade?
- Material + Equipment + Labor each present where applicable?
- Waste factor on cut materials?

Use the room-by-room subdivision approach but treat each appurtenance as the "room" for token management.

### Step 4 — Special considerations by appurtenance

See `references/appurtenance-categories.md` for the starting-point special considerations by appurtenance type (siding hidden housewrap/sheathing damage, fencing lineal footage and gate hardware, deck structural elements, pool equipment, landscaping policy caps). These are **starting points**, not an exhaustive list — apply additional industry-standard considerations.

## Output

Substantive — four-section format per appurtenance group plus verified/unverified facts.

**Recommendations** organized appurtenance-by-appurtenance with line-item tables.

## Stage output (§2.9)

This stage's deliverable is the **appurtenance record** — each exterior/detached structure, whether the carrier scoped it, the scope corrections, and any matching-clause arguments for discontinued products. Record it in `outputs/stage-outputs/06-appurtenances.md`, organized by the exterior/detached macro-areas then by appurtenance, and record its findings in the consolidated audit-findings artifact (`claim-audit-findings`, §2.9) — this stage's entry. Build incrementally; markdown is canonical.

## Stay in this stage's lane

Per §2.10 of the protocols, this stage decides only **damage to structures outside the primary dwelling (siding, fencing, decks, pools, sheds, retaining walls, driveways, gates, outdoor lighting, irrigation)**. It scopes the exterior structures, then runs the line-item + completeness pattern on those structures only.

While doing it you will see things that belong to other stages — interior rooms and their line items (Stages 1–4), peril-specific interior items (Stage 5), or code upgrades (Stage 7). Do not mention them, do not ask whether to flag them, and do not record them anywhere. Drop them; the owning stage re-examines the whole estimate and will catch them. Noticing an out-of-stage item and asking whether to flag it is the §2.10 violation to avoid.

## Recording suggestions in the suggestion list

For every appurtenance suggestion this stage produces (missing appurtenance entirely, scope corrections per appurtenance, matching-clause additions), walk each one through the per-suggestion confirmation flow defined in §2.3 of the protocols: call `AskUserQuestion` per suggestion with options Accept / Reject / Modify / Ask a question. Only Accepted entries get appended to `outputs/audit-suggestion-list.md` (disposition `Agreed`). Refresh the live artifact after each append.

**Strict per-suggestion flow (§2.3).** Every suggestion above gets its **own** `AskUserQuestion` call — one suggestion per call. Do not batch them, do not replace them with a single "shall I add these?" question, and do not ask the verification gate until every suggestion this stage produced has been individually Accepted, Rejected, or Modified-then-Accepted.

## Verification gates

After each appurtenance group (procedural):

> "Do you believe the audit for [Appurtenance] is complete? If not, please direct me to the incomplete item(s)."

Per-macro-area (§2.8), after every appurtenance in a macro-area is done:

> "Do you believe the Appurtenances Audit for [Macro-area] is complete? If not, please direct me to the incomplete item(s)."

Stage end (after all macro-areas):

> "Do you believe the Appurtenances Audit is complete? If not, please direct me to the incomplete item(s)."

After the user confirms, route per §4 of the protocols (which honors the audit mode in `outputs/audit-progress.md`). The next stage is **Code, Ordinance, and Law Audit** (skill: `claim-code-ordinance-law-audit`).

In single-session mode, §4 prompts *"Ready for Code, Ordinance, and Law Audit."* and waits for "begin code audit" (or equivalent) before chaining. In multi-session mode, §4 prints the multi-session hand-off and stops here — the user begins the Code, Ordinance, and Law Audit in a fresh chat in this same Cowork project.

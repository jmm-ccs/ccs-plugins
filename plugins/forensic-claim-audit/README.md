# Forensic Claim Audit Plugin

A plugin that breaks the Construction Claim Services (CCS) forensic supplement-audit process into discrete, individually-invokable Claude skills.

## What's inside

**Foundation**
- `claim-audit-protocols` — the Factual Integrity, Process, and Output Requirements rules, plus the audit-mode toggle (§2.7), the macro-area unit of work (§2.8), and the verification-gate routing (§4). Every audit skill loads this first. Single source of truth so the protocols are updated in one place.

**Audit modes (single-session vs. multi-session)**

Audits run in one of two modes, recorded as a `**Mode:**` line at the top of `outputs/audit-progress.md`:

- **`multi-session`** (default) — each stage runs in its own fresh chat in the same Cowork project. Each stage finishes by directing the user to start the next stage in a new chat. Recommended for long claims because per-stage context stays clean.
- **`single-session`** — the entire audit unfolds in one Cowork chat. The master orchestrator walks all 13 stages back-to-back with verify-then-advance gates between them.

See §2.7 of `claim-audit-protocols` for the full toggle spec.

**Macro-areas (the unit of work within every stage)**

The property is divided into **macro-areas** — large physical sections that group rooms and categories (e.g., Main Floor Interior, Upper Floor Interior, Basement, Exterior & Roof, Detached Structures). Every audit stage works **one macro-area at a time**, with a confirmation gate at each area boundary, so no stage tries to swallow the whole property at once.

- The map lives in `outputs/macro-areas.md` (canonical markdown).
- **Created** at setup — `claim-audit-setup` (or the orchestrator in single-session) proposes a division from the carrier estimate's diagram pages / sketches / photos, and you confirm or adjust it. (Setup also creates all three live artifacts: suggestion list, progress, findings.)
- **Updated** by the Scope Audit (Stage 1) once the true scope is confirmed — new rooms get assigned, new sections get added.

Stages use the map in one of four ways: room-based stages (line item, completeness, related items) go room-by-room *inside* each area; area-decomposable stages (type-of-loss, appurtenances, cleanup/protection) take the area's contents as the unit; project-wide stages (code/ordinance, storage/debris, trades, permits/O&P, sales tax) gather area-by-area but compute their project-level totals once; and the continuity stage is the deliberate exception — it works the *boundaries between* areas. See §2.8 of `claim-audit-protocols` for the full spec.

The mode toggle (§2.7) and macro-areas (§2.8) are independent: the mode controls what happens *between* stages, macro-areas control how work is chunked *within* a stage.

**Per-stage outputs (every stage leaves a visible work product)**

Each stage records its own deliverable as a file in `outputs/stage-outputs/` (e.g., `01-scope.md`, `11-trades.md`), organized by macro-area where the stage works area by area. All stages also feed one consolidated live "audit findings" artifact (a collapsible section per stage) rather than a separate artifact each. The content is whatever that stage is *for* — Scope's cross-walk, the Trades Audit's reconciled trade mapping, the Sales Tax Audit's per-line-item tax table, and so on — not a uniform template. These sit alongside the three cross-cutting files (the macro-area map, the suggestion list, the progress file). The suggestion list holds the *accepted suggestions* headed for the supplement; the stage files hold the *full work product* (the why). Both feed the Xactimate build. See §2.9 of `claim-audit-protocols`.

The progress file (`outputs/audit-progress.md`) carries the macro-areas as sub-points under each stage, so progress is visible per area within a stage; the stage's status is the rollup of its areas (Scope and Final Delivery have no sub-points). See §2.6.

**Setup / orchestrator**
- `claim-audit-setup` — explicit multi-session initializer. Creates the workspace (`outputs/`, suggestion list, progress file, all three live artifacts), runs the project-document inventory, proposes the macro-area division for you to confirm (`outputs/macro-areas.md`), and writes `**Mode:** multi-session`, then stops. Use when you want to seed the workspace up front before starting Stage 1 in a fresh chat.
- `forensic-claim-audit` — single-session orchestrator. Runs the full 13-stage audit end-to-end with verify-then-advance gates between stages. When invoked, asks whether to switch to single-session if the project is currently in multi-session mode (default answer: keep multi-session). Use this when you want to audit a full claim from scratch in one continuous chat.

**13 stage skills (use individually when you only need one stage)**
1. `claim-scope-audit`
2. `claim-line-item-audit`
3. `claim-line-item-completeness-audit`
4. `claim-related-items-audit`
5. `claim-type-of-loss-audit` (roofing / water / fire branches)
6. `claim-appurtenances-audit`
7. `claim-code-ordinance-law-audit`
8. `claim-continuity-audit`
9. `claim-storage-debris-audit`
10. `claim-cleanup-protection-audit`
11. `claim-trades-audit`
12. `claim-permits-contractor-cost-audit`
13. `claim-sales-tax-audit`

**Output / utilities**
- `claim-audit-finalizer` — end-of-audit closing flow. Runs the Supplement Sanity Audit, gathers dispositions on flagged entries, resolves every open flag with the user (unresolved entries stay off the output), collects user-confirmed wording for every reason box, then invokes the estimate markup to render and visually verify the marked-up copy of the carrier's estimate. (The XLSX export moved to the on-demand `claim-suggestion-list-export` skill.)
- `claim-pdf-annotator` — produces the audit's **end deliverable**: a marked-up copy of the carrier's estimate, via the bundled interpret → render pipeline (Xactimate and Symbility, auto-detected and visually cross-checked). Reads the suggestion list and the carrier estimate, reproduces the full estimate, and applies CCS's edits in place — changed values, new lines (numbered `Supp-1.`, `Supp-2.`, … in output order), and new rooms in the CCS edit color, with a justification box beneath every change — then visually verifies every output page against the carrier estimate and sample supplements in a fix-and-recheck loop. Saved as `outputs/[carrier-pdf-name]-annotated.pdf`. The finalizer auto-invokes this; the user can also invoke it standalone at any point during or after the audit for a current snapshot.
- `claim-supplement-package` — **superseded.** The legacy Word supplement document (cover letter duplicating the project's Sample Supplement, an Alignment Summary, and line-item alignments in the sample's format). The marked-up copy of the carrier's estimate now replaces it as the carrier-facing deliverable, so the standard output flow no longer produces it and the finalizer no longer invokes it. Kept in the plugin only for projects that specifically want the legacy document. Requires the Sample Supplement in the project folder.
- `claim-video-intake` — on-demand utility. Converts walkthrough videos into audit-readable evidence: examines every frame, saves each visually distinct one as a timestamped still, transcribes the narration, and writes a per-video manifest into `video-intake/` in the project folder. The orchestrator runs it automatically before Stage 1 when an unprocessed video is present.
- `claim-bilingual-mode` — on-demand utility. Turns project-wide Spanish output on or off (§2.11): English files stay English; the Spanish lives in separate `-es` duplicates of the suggestion list and every deliverable, and the per-suggestion approval popups are shown in Spanish.
- `claim-suggestion-list-export` — on-demand utility. Exports only the **Agreed** entries from the suggestion list to `outputs/audit-suggestion-list-agreed.xlsx` (the CCS working set). Use mid-audit or at close-out any time CCS wants a spreadsheet of the accepted suggestions — the finalizer no longer exports an XLSX of its own.
- `claim-project-inventory` — pre-flight document inventory. Walks the workspace, categorizes every file (carrier estimate, photos, sketches/floor plans, scope of work, measurement reports, drying logs, invoices, checklists, marketing sheets, etc.), flags expected-but-missing categories, and writes both `outputs/project-inventory.md` and `outputs/project-inventory.xlsx`. Invoked automatically by `claim-audit-setup` as part of the multi-session initialization, and also runnable on its own any time the user wants a fresh inventory.

CCS builds the line-item supplement estimate in Xactimate from the Agreed-only XLSX (`claim-suggestion-list-export`); the marked-up copy of the carrier's estimate (the full estimate reproduced with CCS's edits applied in-line — changes in the CCS edit color, a justification box under each) is the carrier-facing deliverable that shows every correction in context on the carrier's own estimate.

## How the skills relate

```
claim-project-inventory  (pre-flight; optional)
    ↓ produces:  outputs/project-inventory.{md,xlsx}
forensic-claim-audit (master)
    ↓ loads at every stage
claim-audit-protocols
    ↓ writes to and reads from
outputs/audit-suggestion-list.md  (the suggestion list — canonical)
outputs/macro-areas.md         (the macro-area map — set at setup, refined by scope)
    ↓ then walks through, in order (each stage one macro-area at a time):
scope → line-item → completeness → related-items → type-of-loss
  → appurtenances → code/ordinance → continuity → storage/debris
  → cleanup/protection → trades → permits/contractor → sales-tax
    ↓ each stage records its own deliverable in:
outputs/stage-outputs/NN-slug.md  (all rolled into one live "audit findings" artifact)
    ↓ at end of audit
claim-audit-finalizer (Sanity Audit → flag resolution → reason-box wording)
    └ invokes ─→ claim-pdf-annotator
                 (interpret → render pipeline + page-by-page visual verification;
                  the marked-up copy of the carrier's estimate — the end deliverable;
                  also callable standalone any time)
    ↓ produces in outputs/:
reason-wording.json  +  [carrier-pdf-name]-annotated.pdf  (marked-up estimate)

claim-supplement-package  (superseded legacy Word document; not in the standard flow)

claim-suggestion-list-export  (on-demand; mid-audit or post-audit)
    ↓ produces:  outputs/audit-suggestion-list-agreed.xlsx  (Agreed-only working set)
```

Each stage skill is fully invokable on its own — for example, `/claim-sales-tax-audit` will load the protocols, run the sales-tax audit, and stop.

## Installation

This plugin is laid out in standard Cowork plugin form. To install:

1. The folder `.claude-plugin/` already contains `plugin.json` at the plugin root.
2. Drop the plugin directory into your local plugins folder, or zip and load it as a marketplace bundle.

Individual skills can also be installed standalone — each `skills/<name>/` directory is a complete, self-contained skill.

## Source materials

This plugin codifies the workflow defined by:
- *Master Prompts for Gemini Claim Auditing* (the manual orchestration guide)
- *Forensic Claim Analysis Checklists* (the nine domain checklists)

The protocols, audit ordering, and verification gates are taken directly from those documents.

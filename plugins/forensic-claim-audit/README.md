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
- **Created** at setup — `claim-audit-setup` (or the orchestrator in single-session) proposes a division from the carrier estimate's diagram pages / sketches / photos, and you confirm or adjust it.
- **Updated** by the Scope Audit (Stage 1) once the true scope is confirmed — new rooms get assigned, new sections get added.

Stages use the map in one of four ways: room-based stages (line item, completeness, related items) go room-by-room *inside* each area; area-decomposable stages (type-of-loss, appurtenances, cleanup/protection) take the area's contents as the unit; project-wide stages (code/ordinance, storage/debris, trades, permits/O&P, sales tax) gather area-by-area but compute their project-level totals once; and the continuity stage is the deliberate exception — it works the *boundaries between* areas. See §2.8 of `claim-audit-protocols` for the full spec.

The mode toggle (§2.7) and macro-areas (§2.8) are independent: the mode controls what happens *between* stages, macro-areas control how work is chunked *within* a stage.

**Per-stage outputs (every stage leaves a visible work product)**

Each stage records its own deliverable as a file in `outputs/stage-outputs/` (e.g., `01-scope.md`, `11-trades.md`), organized by macro-area where the stage works area by area. All stages also feed one consolidated live "audit findings" artifact (a collapsible section per stage) rather than a separate artifact each. The content is whatever that stage is *for* — Scope's cross-walk, the Trades Audit's reconciled trade mapping, the Sales Tax Audit's per-line-item tax table, and so on — not a uniform template. These sit alongside the three cross-cutting files (the macro-area map, the suggestion list, the progress file). The suggestion list holds the *accepted suggestions* headed for the supplement; the stage files hold the *full work product* (the why). Both feed the Xactimate build. See §2.9 of `claim-audit-protocols`.

The progress file (`outputs/audit-progress.md`) carries the macro-areas as sub-points under each stage, so progress is visible per area within a stage; the stage's status is the rollup of its areas (Scope and Final Delivery have no sub-points). See §2.6.

**Setup / orchestrator**
- `claim-audit-setup` — explicit multi-session initializer. Creates the workspace (`outputs/`, suggestion list, progress file, both live artifacts), runs the project-document inventory, proposes the macro-area division for you to confirm (`outputs/macro-areas.md`), and writes `**Mode:** multi-session`, then stops. Use when you want to seed the workspace up front before starting Stage 1 in a fresh chat.
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
- `claim-audit-finalizer` — end-of-audit closing flow. Runs the Supplement Sanity Audit, gathers dispositions on flagged entries, exports the suggestion list to XLSX (full record — all dispositions), invokes the annotator and the supplement package, then runs a final fact-check across the deliverables (markdown / XLSX / annotated PDF / package) to verify they faithfully match each other.
- `claim-supplement-package` — the supplement document deliverable, built from the `Agreed` entries after the Sanity Audit: a cover letter duplicating the project's Sample Supplement verbatim (contractor/adjuster/policyholder info swapped), an Alignment Summary based on the sample, and one line-item alignment per entry in the sample's exact format. Requires the Sample Supplement in the project folder. Saved as `outputs/supplement-package.docx`.
- `claim-pdf-annotator` — on-demand utility, callable at any point during or after the audit. Reads the suggestion list and the carrier PDF, produces an annotated copy of the PDF with each non-rejected suggestion attached as a PDF comment at the carrier line it modifies. The finalizer auto-invokes this; the user can also invoke it standalone for a current snapshot.
- `claim-suggestion-list-export` — on-demand utility. Exports only the **Agreed** entries from the suggestion list to `outputs/audit-suggestion-list-agreed.xlsx` (the CCS working set). Independent of the finalizer's full-record XLSX — the two outputs coexist. Use mid-audit any time CCS wants a fresh spreadsheet of the accepted suggestions.
- `claim-project-inventory` — pre-flight document inventory. Walks the workspace, categorizes every file (carrier estimate, photos, sketches/floor plans, scope of work, measurement reports, drying logs, invoices, checklists, marketing sheets, etc.), flags expected-but-missing categories, and writes both `outputs/project-inventory.md` and `outputs/project-inventory.xlsx`. Invoked automatically by `claim-audit-setup` as part of the multi-session initialization, and also runnable on its own any time the user wants a fresh inventory.

CCS builds the line-item supplement estimate in Xactimate from the XLSX; the supplement package (cover letter + Alignment Summary + alignments, formatted per the project's Sample Supplement) is the carrier-facing document that travels with it.

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
claim-audit-finalizer (Sanity Audit → full XLSX export → final fact-check)
    ├ invokes ─→ claim-pdf-annotator
    │            (also callable standalone any time)
    └ invokes ─→ claim-supplement-package
                 (cover letter + Alignment Summary + alignments, per the Sample Supplement)
    ↓ produces in outputs/:
audit-suggestion-list.xlsx  +  [carrier-pdf-name]-annotated.pdf  +  supplement-package.docx

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

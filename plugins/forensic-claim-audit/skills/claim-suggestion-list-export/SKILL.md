---
name: claim-suggestion-list-export
description: On-demand utility for the CCS forensic claim audit. Exports the suggestion list to a clean XLSX file containing only entries with disposition `Agreed` — the working set CCS uses to build the Xactimate supplement. Trigger any time the user says "export the suggestion list," "give me the XLSX," "spreadsheet of the agreed suggestions," "export accepted entries," or "send me the working set as Excel." Independent of the finalizer — invoke whenever a fresh export is wanted (mid-audit snapshot or post-audit refresh).
---

# Claim Suggestion list Export — Agreed-Only XLSX

Goal: produce a clean, sortable `.xlsx` of the suggestion list filtered to only the **Agreed** entries (the CCS working set), without running the full finalizer flow. Useful any time the user wants a current spreadsheet of the accepted suggestions — mid-audit, between stages, or after final delivery if entries get re-dispositioned.

This skill is independent of `claim-audit-finalizer` (which produces a separate XLSX containing *all* entries regardless of disposition for the full audit record). The two outputs serve different purposes:

| Skill | Output filename | Scope |
|---|---|---|
| `claim-suggestion-list-export` (this skill) | `outputs/audit-suggestion-list-agreed.xlsx` | Only `Agreed` entries — the CCS working set |
| `claim-audit-finalizer` Phase 2 | `outputs/audit-suggestion-list.xlsx` | All entries regardless of disposition (full audit record) |

The two files coexist in `outputs/` and do not overwrite each other.

## Step 0 — Read the protocols

Use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read the entire file end-to-end before doing anything else. Pay particular attention to:

- §1.1 — Output Integrity (the XLSX must faithfully represent the markdown source)
- §2.3 — Carrier Estimate Protocol, including the suggestion-list spec and disposition values (`Agreed`, `Halted`, `Needs-info`)
- §3 — Final factual integrity and logic pass (run on the export before declaring success)

Do this every time this skill is invoked, regardless of whether the protocols were loaded earlier in the conversation.

## Prerequisite — enforced gate (refuse until met)

Run this check before exporting, per §2.14 of the protocols. Re-check on every attempt.

**Active project.** `outputs/audit-progress.md` must exist (setup has run). If it doesn't, this isn't an active claim project: refuse and tell the user to run `/claim-audit-setup` first, then stop. (Once a project is active, Step 1 below handles the case where the suggestion list has no `Agreed` entries yet — that's a "nothing to export," not a precondition failure.)

Proceed only when it passes.

## Step 1 — Locate and read the suggestion list

The suggestion list lives in the project workspace at `outputs/audit-suggestion-list.md`. Use `Read` on it.

If the file doesn't exist, the audit hasn't started yet (or the project isn't set up). Use `AskUserQuestion`. The question must include:

- That there's nothing to export because there's no suggestion list yet, and what the suggestion list is (where suggestions accumulate as you go through an audit; stays empty until you start one).
- The two startup options with their actual tradeoffs:
  - Each stage in its own chat: each stage stays focused, suggestion list and progress carry over between chats, can step away and come back later. More chats to track. The usual way.
  - All 13 stages in one chat: faster end-to-end, everything in one place. One long chat. Good for short claims.

Options:

- `Set up — each stage in its own chat (the usual way)` — then say to send `/claim-audit-setup` in this chat to set things up. Stop.
- `Set up — all 13 stages in one chat` — then say to send `/forensic-claim-audit` to run the full audit here, and that this export can be re-run any time for a snapshot. Stop.
- `Stop here for now` — exit silently.

Do not create or fabricate a suggestion list. If the source markdown is missing or empty (header row only), there's nothing to export.

## Step 2 — Filter to Agreed entries

Parse the markdown table. Keep only rows whose **Disposition** column value is exactly `Agreed`.

Drop:

- Rows with `Halted` disposition (waiting on the user to accept a corrected entry per §6 of the protocols)
- Rows with `Needs-info` disposition (waiting on contractor input)
- Any other disposition value (treat unknown values as not-Agreed and skip)

Run `bash` with Python to count rows in the source markdown and the Agreed-only filtered set. Both counts must reconcile against the user's understanding of the suggestion list. Show the math (per §1.4): input row count, filter rule, output row count.

If the filter produces zero rows (no entries are currently `Agreed`), tell the user:

- Nothing was exported because no entries in the suggestion list are currently marked Agreed.
- The total row count and the breakdown by disposition (e.g., 4 Halted, 2 Needs-info).
- That this can be re-run once more suggestions are accepted.

Do not produce an empty XLSX file.

## Step 3 — Export to XLSX

Use the `xlsx` skill:

1. Convert the filtered Agreed-only rows to a clean `.xlsx` and save as `outputs/audit-suggestion-list-agreed.xlsx`.
2. Preserve all fields from the markdown table:
   - `#` (sequential suggestion number)
   - `Stage of origin`
   - `Carrier line`
   - `Suggestion type`
   - `Label`
   - `Proposed change`
   - `Number provenance`
   - `Supporting evidence` (carries the plain-language Why + named source files, per §1.5 — the reviewer-facing reason and evidence; copy verbatim, do not summarize)
   - `User notes`
   - `Claude notes`
   - `Disposition` (will always be `Agreed` for every row in this export — kept for column-parity with the finalizer's full-record XLSX)
3. Sort by **Stage of origin** ascending, then by **Carrier line** item number ascending.
4. Freeze the header row. Apply column widths that fit the typical content of each field (use the same widths as the finalizer's full-record XLSX, so CCS can place the two files side-by-side).

Confirm the XLSX wrote successfully before proceeding.

**Bilingual mode (§2.11).** If `**Languages:**` in `outputs/audit-progress.md` is `English + Spanish`, also produce a Spanish duplicate `outputs/audit-suggestion-list-agreed-es.xlsx`, built from the Spanish suggestion list `outputs/audit-suggestion-list-es.md` with the same Agreed-only filter and the same columns — numbers, codes, and carrier-line references identical, descriptive fields in Spanish. Write it **alongside** the English XLSX, never instead of it.

## Step 4 — Final factual-integrity pass

Run the §3 final pass on this export:

- Open `outputs/audit-suggestion-list-agreed.xlsx` (read it back via `bash` or the `xlsx` skill) and verify every row matches the source markdown exactly — no truncation, no character-encoding changes, no row drops, no row duplications.
- Run `bash` with Python to count rows in the XLSX. The count must match the Agreed-only row count from Step 2.
- Spot-check three random rows in detail (compare `Carrier line`, `Proposed change`, `Number provenance` exactly).
- Confirm every row's `Disposition` column reads `Agreed`.

If any check fails, fix and re-export. Do not advance to Step 5 with known integrity gaps.

## Step 5 — Confirm to the user

The closing message includes:

- The export path (`outputs/audit-suggestion-list-agreed.xlsx`) and the row count.
- That the rows are sorted by stage of origin and then Carrier line.
- That this can be re-run any time for a refresh.
- That `/claim-audit-finalizer` produces the full-record XLSX (every entry, every disposition).

Do not start any next step.

## What this skill does NOT do

- Does not run the Sanity Audit (that's `claim-audit-finalizer` Phase 1).
- Does not re-annotate the carrier PDF (that's `claim-pdf-annotator`).
- Does not include `Halted` or `Needs-info` entries.
- Does not modify `outputs/audit-suggestion-list.md` — the markdown is canonical and read-only from this skill's perspective.
- Does not advance any audit-progress state. The progress file (`outputs/audit-progress.md`) is not touched by this export.

## Related skills

- `claim-audit-finalizer` — full closing flow that produces the all-dispositions XLSX. Use at final delivery, not for mid-audit snapshots.
- `claim-pdf-annotator` — produces the annotated carrier PDF from the suggestion list. Pair with this skill when CCS wants both the spreadsheet and the marked-up PDF.
- `claim-audit-protocols` — the protocols this skill operates against. Read at Step 0.

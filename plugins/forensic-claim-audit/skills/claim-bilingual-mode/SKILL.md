---
name: claim-bilingual-mode
description: On-demand utility for the CCS forensic claim audit. Turns project-wide bilingual output on or off. When on, every suggestion is shown in English AND Spanish everywhere it already appears — the per-suggestion prompts, the live suggestion list, the markdown source, and all exports and the annotated PDF — for the rest of the project. Make sure to use this skill whenever the user says "show the suggestions in Spanish," "in English and Spanish," "make it bilingual," "translate the suggestions," "turn on Spanish," or wants to present the audit to a Spanish-speaking client or policyholder — even if they don't say the word "bilingual." Sets a persistent flag that sticks across chats; invoke again to switch Spanish back off.
---

# Claim Bilingual Mode — English + Spanish, project-wide

Goal: flip a single persistent setting so that suggestions are presented in **English + Spanish** (or back to English only) for the entire project. This skill does not produce a separate translated document — it switches on the rule defined in §2.11 of the protocols, after which the Spanish appears inline next to the English everywhere a suggestion already shows up.

The setting lives in the project's progress file and persists across chats, so once it's on, every stage and every other skill honors it for the rest of the audit.

## Step 0 — Read the protocols

Use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read it end-to-end before doing anything else. Pay particular attention to:

- **§2.11 — Bilingual output mode**: the exact rule this skill switches on (what gets translated, what stays verbatim, the `**Languages:**` flag and its values).
- **§2.6 — Audit progress tracking**: the structure of `outputs/audit-progress.md`, where the `**Languages:**` line lives (directly under `**Mode:**`).
- **§2.3 — the suggestion list and the per-suggestion flow**: the descriptive cells (Proposed change, Supporting evidence, Claude notes) that carry the Spanish, and the artifact-refresh protocol.

Do this every time this skill is invoked, regardless of whether the protocols were loaded earlier in the conversation.

## Step 1 — Locate the project state

The project folder is the Cowork workspace, already attached. Do not ask the user to identify it; operate inside the workspace. Ensure the `outputs/` sub-folder exists.

`Read` `outputs/audit-progress.md`:

- **If it exists**, find the current `**Languages:**` line (directly under `**Mode:**`). If there is no such line, the current setting is the default, **English** only.
- **If it does not exist**, the audit hasn't been set up yet. You can still record the preference: create `outputs/audit-progress.md` following the §2.6 structure — a `# Audit Progress` header, `**Mode:** multi-session`, the `**Languages:**` line set per Step 3, then the 13 stage headings plus Final Delivery, each `Not started` and without area sub-points (no map exists yet). This is a valid §2.6 progress file, so `claim-audit-setup` and the stage skills will preserve it rather than overwrite it. Tell the user the audit isn't set up yet, but their language preference is now recorded and will apply the moment they start.

## Step 2 — Decide the direction (and confirm)

Read the current value (treat missing/unrecognized as **English**).

- **If currently English (off):** the user is turning it on — proceed to set `English + Spanish`.
- **If currently `English + Spanish` (already on):** use `AskUserQuestion` to ask whether to keep it on or switch back. Options: `Keep English + Spanish` (stop, nothing to change) and `Switch to English only` (proceed to set `English`).

## Step 3 — Write the persistent flag

Set the `**Languages:**` line in `outputs/audit-progress.md` to the chosen value — `English + Spanish` or `English`:

```
**Languages:** English + Spanish
```

- If the line already exists, replace its value in place.
- If the line is missing, insert it on its own line directly **under** the `**Mode:**` line.
- Preserve everything else in the file exactly — the `**Mode:**` line, every stage heading, every area sub-point, and all statuses. Do not touch stage state.

## Step 4 — Offer to backfill existing entries (only when turning ON)

`Read` `outputs/audit-suggestion-list.md`. If it has data rows beyond the header, those entries were recorded in English only. Use `AskUserQuestion`:

- `Add Spanish to the existing [N] suggestions now` — for every existing row, add the Spanish to the descriptive cells (**Proposed change**, **Supporting evidence**, and any **Claude notes**) per §2.11: English text, then `<br>ES:` and the Spanish, leaving every number, unit, price, code citation, carrier line reference, label code, and disposition exactly as-is. Then refresh the live suggestion-list artifact per the §2.3 Artifact-refresh protocol.
- `Only apply to new suggestions from here on` — leave existing rows in English; only suggestions added after this point will be bilingual.

If the suggestion list is empty (header row only), skip this step — there's nothing to backfill.

When turning the mode **off**, do not strip Spanish from existing entries unless the user explicitly asks; just stop adding it going forward.

## Step 5 — Confirm to the user

State plainly:

- Bilingual mode is now **ON (English + Spanish)** — or **OFF (English only)**.
- When on, it applies **everywhere** suggestions appear: the per-suggestion Accept/Reject prompts, the live suggestion-list view, the markdown source, and — because they reproduce that list — every XLSX export and the annotated carrier PDF. The Spanish sits inline next to the English; the format is otherwise unchanged.
- It **persists for the whole project** (across chats). Every stage from here on will honor it automatically.
- To change it later, re-run this skill (`/claim-bilingual-mode`) and pick the other option.

Do not start any audit stage or other next step.

## What this skill does NOT do

- It does not translate the carrier's quoted line items, quantities, prices, M/E/L, code citations, or dispositions — only the explanatory prose around each suggestion (per §2.11). Numbers and citations are preserved exactly in both languages.
- It does not change any suggestion's content or disposition.
- It does not advance audit-progress stage state or change the audit Mode (single/multi-session).
- It does not produce a separate translated file — Spanish appears inline alongside the existing English.

## Related skills

- `claim-audit-protocols` — §2.11 defines the bilingual rule this skill switches on. Read at Step 0.
- `claim-suggestion-list-export`, `claim-audit-finalizer`, `claim-pdf-annotator` — these reproduce the suggestion-list cells verbatim, so they become bilingual automatically once the list is bilingual; no separate setting is needed on them.

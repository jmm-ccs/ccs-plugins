---
name: claim-bilingual-mode
description: On-demand utility for the CCS forensic claim audit. Turns project-wide Spanish output on or off. When on, the English files stay English, the Spanish lives in separate duplicate files (a Spanish copy of the suggestion list, plus Spanish copies of the exports and the annotated PDF), and the per-suggestion approval prompts are shown in Spanish — for the rest of the project. Make sure to use this skill whenever the user says "show the suggestions in Spanish," "in English and Spanish," "make it bilingual," "translate the suggestions," "turn on Spanish," or wants to present the audit to a Spanish-speaking client or policyholder — even if they don't say the word "bilingual." Sets a persistent flag that sticks across chats; invoke again to switch Spanish back off.
---

# Claim Bilingual Mode — English + Spanish, project-wide

Goal: flip a single persistent setting that turns Spanish output on (or back off) for the entire project. It switches on the rule defined in §2.11 of the protocols: the English files are left untouched, the Spanish is kept in **separate duplicate files** (a Spanish copy of the suggestion list, plus Spanish copies of the exports and the annotated PDF), and the per-suggestion approval prompts are shown in **Spanish only** while your chat responses stay English.

The setting lives in the project's progress file and persists across chats, so once it's on, every stage and every other skill honors it for the rest of the audit.

## Step 0 — Read the protocols

Use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read it end-to-end before doing anything else. Pay particular attention to:

- **§2.11 — Bilingual output mode**: the exact rule this skill switches on (what gets translated, what stays verbatim, the `**Languages:**` flag and its values).
- **§2.6 — Audit progress tracking**: the structure of `outputs/audit-progress.md`, where the `**Languages:**` line lives (directly under `**Mode:**`).
- **§2.3 — the suggestion list and the per-suggestion flow**: the descriptive fields (Proposed change, Supporting evidence, Claude notes) translated in the Spanish duplicate, and the per-suggestion prompt the Spanish-only popup replaces.

Do this every time this skill is invoked, regardless of whether the protocols were loaded earlier in the conversation.

## Prerequisite — enforced gate (refuse until met)

Run this before changing anything, per §2.14 of the protocols. Re-check on every attempt.

**Active project.** `outputs/audit-progress.md` must exist (setup has run) — the `**Languages:**` flag lives in that file, and this skill does **not** create the workspace; setup does. If the file doesn't exist, refuse: tell the user to run `/claim-audit-setup` first, then send `/claim-bilingual-mode` again. Stop.

Proceed only when it passes.

## Step 1 — Locate the project state

The project folder is the Cowork workspace, already attached. Do not ask the user to identify it; operate inside the workspace. Ensure the `outputs/` sub-folder exists.

`Read` `outputs/audit-progress.md`:

- **If it exists**, find the current `**Languages:**` line (directly under `**Mode:**`). If there is no such line, the current setting is the default, **English** only.
- **If it does not exist**, the Prerequisite gate above has already refused and stopped — you never reach this step without an active project. (This is why the skill no longer pre-creates a bare progress file: per §2.14, the active-project signal must mean setup actually ran, so only setup creates `outputs/audit-progress.md`.)

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

## Step 4 — Build the Spanish duplicate from existing entries (only when turning ON)

`Read` `outputs/audit-suggestion-list.md`. If it has data rows beyond the header, those entries exist only in the English list. Use `AskUserQuestion`:

- `Build the Spanish copy of the existing [N] suggestions now` — create `outputs/audit-suggestion-list-es.md` as a row-for-row duplicate of the English list per §2.11: identical header, identical `#`, identical row order, every number/unit/price/code/carrier-line/label/disposition byte-for-byte identical, with only the descriptive fields (Proposed change, Supporting evidence, Claude notes) rendered in Spanish.
- `Only apply to new suggestions from here on` — create `outputs/audit-suggestion-list-es.md` with the header row only; rows are mirrored into it as new suggestions are added from here.

If the suggestion list is empty (header row only), just create the Spanish duplicate with its header row so it's ready.

When turning the mode **off**, leave the Spanish duplicate file in place (do not delete it unless the user asks); simply stop mirroring new rows into it.

## Step 5 — Confirm to the user

State plainly:

- Bilingual mode is now **ON (English + Spanish)** — or **OFF (English only)**.
- When on: your English files stay untouched; the Spanish lives in a parallel duplicate suggestion list (`outputs/audit-suggestion-list-es.md`), and the exports and the annotated PDF get Spanish `-es` copies alongside the English ones. The per-suggestion approval popups are shown in Spanish, while your chat responses stay in English.
- It **persists for the whole project** (across chats). Every stage from here on will honor it automatically.
- To change it later, re-run this skill (`/claim-bilingual-mode`) and pick the other option.

Do not start any audit stage or other next step.

## What this skill does NOT do

- It does not translate the carrier's quoted line items, quantities, prices, M/E/L, code citations, or dispositions — only the explanatory prose around each suggestion (per §2.11). Numbers and citations are preserved exactly in both languages.
- It does not change any suggestion's content or disposition.
- It does not advance audit-progress stage state or change the audit Mode (single/multi-session).
- It does not inject Spanish into the English files or surfaces — the English suggestion list, artifact, exports, and PDF stay English. The Spanish is kept in separate `-es` duplicate files.

## Related skills

- `claim-audit-protocols` — §2.11 defines the bilingual rule this skill switches on. Read at Step 0.
- `claim-suggestion-list-export`, `claim-audit-finalizer`, `claim-pdf-annotator` — when bilingual is on, each also emits a Spanish `-es` copy of its deliverable, built from the Spanish suggestion list (per §2.11), alongside the English one.

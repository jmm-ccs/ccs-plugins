---
name: claim-audit-setup
description: One-time setup for a CCS forensic claim audit that will run across multiple chats in the same Cowork project. Initializes the workspace (outputs/, suggestion list, progress file, all three live artifacts) and turns on multi-session mode so each stage runs in its own fresh chat. Use when the user says "set up a new audit," "start a multi-session audit," "I'll run this in separate chats," "initialize the project," "scaffold the audit workspace," or wants to prep a new claim without immediately starting Stage 1. After this skill runs, the user begins Stage 1 in a new chat by invoking `claim-scope-audit`.
---

# Claim Audit Setup (Multi-Session Initializer)

Goal: do all the one-time project setup the master orchestrator (`forensic-claim-audit`) does at the start of an audit, then **stop** without beginning Stage 1. This skill explicitly initializes the workspace files (`outputs/`, the suggestion list, the progress file, and all three live artifacts) and locks the audit mode at `multi-session` — each stage runs in its own fresh chat in the same Cowork project.

Multi-session is the **default mode** for this plugin (see §2.7 of the protocols), so a stage skill invoked in a brand-new project will also default to multi-session and create the workspace lazily. This skill is for users who prefer to do that initialization explicitly up front — e.g., to confirm the workspace is wired up correctly, to seed the audit-progress live artifact in the Cowork sidebar before Stage 1, or to flip an existing single-session project back to multi-session without re-running the orchestrator.

This skill is the multi-session counterpart to `forensic-claim-audit`. It writes `**Mode:** multi-session` into `outputs/audit-progress.md`; from that point on, every stage skill reads the mode at its end-of-stage gate (§4 of the protocols) and instructs the user to start the next stage in a fresh chat.

Setup only proceeds if the essential claim documents are in the project folder (Step 0.5). An empty folder, or one holding only the standard samples/templates, stops the skill before any file is created.

## Step 0 — Read the protocols

Use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read the entire file end-to-end before doing anything else. Pay particular attention to:

- §2.3 — suggestion list spec and Initialization sequence
- §2.6 — audit-progress file spec and Initialization sequence
- §2.7 — audit mode toggle (this is the section this skill operates against)

Do this every time this skill is invoked, regardless of whether the protocols were loaded earlier in the conversation.

## Step 0.5 — Pre-flight: essential claim documents (hard stop)

Before asking for confirmation and before creating any file or artifact, scan the project folder. This is read-only — list every file recursively (same exclusions as the inventory's Step 1: skip `outputs/`, `.DS_Store` and other OS/tool detritus, and hidden files). Using the categorization heuristics from `../claim-project-inventory/SKILL.md` Step 2, answer two questions:

1. Is there a **carrier estimate** (Xactimate PDF/ESX/XCEIF export or equivalent)?
2. Is there at least one piece of **project documentation** — photos, videos, sketches, or floor plans (video-derived frames in `video-intake/` count)?

**HARD STOP** if any of the following is true:

- The folder is empty (nothing besides `outputs/` and detritus).
- The folder contains only standard samples/templates — Sample supplement, CCS forensic checklists, CCS marketing sheet — and no claim documents.
- There is no carrier estimate.
- There is no project documentation.

On a hard stop:

1. Do **not** create `outputs/`, the suggestion list, the progress file, or any artifact. Do not run the inventory. Do not ask the Step 1 confirmation question.
2. Tell the user in a short message: setup stopped because essential claim documents are missing; then one bullet per missing essential, using the **What it is** descriptions from the inventory's Step 4 table (describe the thing concretely — never just a category label).
3. Close with one line: add the documents to the project folder, then send `/claim-audit-setup` again.
4. **Stop.** The skill ends here — no partial setup.

Conditionally-required items (drying log for water losses, third-party measurement report for roofing/exterior claims) do **not** trigger the hard stop — the loss type isn't established at setup. The Step 4 inventory still flags them.

## Step 1 — Confirm intent

Ask the user to confirm before any files are touched. The message:

- Is one or two short sentences.
- Says what's about to happen at a high level (setting up the project for the audit).
- Asks for the user to reply with "set up audit" (or equivalent) to go ahead.

No explanation of multi-session mode, the inventory, or what Stage 1 will look like.

Wait for "set up audit" (or equivalent) before continuing.

## Step 2 — Run the workspace initialization

The project folder is the Cowork workspace, already attached. Do not ask the user to identify it. Follow the **Initialization** sequences in §2.3 (suggestion list) and §2.6 (audit progress) of the protocols. These steps mirror them — and match exactly what the master orchestrator does at its Step 0.5, with one difference (Step 2.4 below):

1. **Create the `outputs/` sub-folder** inside the workspace if it doesn't already exist. If creation fails, use `AskUserQuestion` to ask the user where to place `outputs/` and create it there.

2. **Initialize `outputs/audit-suggestion-list.md`** with the table headers from §2.3 if the file doesn't already exist. If it already exists (resuming a prior audit), leave it as-is.

3. **Initialize `outputs/audit-progress.md`** with the structure from §2.6 if the file doesn't already exist. **Use `**Mode:** multi-session`** on the Mode line (the one place this skill diverges from the orchestrator's setup, which uses `single-session`). All 14 status rows start at `Not started`.

   If `outputs/audit-progress.md` already exists, do **not** overwrite the table — just update the Mode line to `multi-session` (see Step 3 below).

4. **Create this project's live suggestion-list artifact** if the project doesn't have one yet — the check is the backing file `outputs/audit-suggestion-list-artifact.html`, never the artifact list, and an artifact from another project is never "existing" (per-project rule, §2.3). Follow the §2.3 Initialization sequence: read the template at `forensic-claim-audit/assets/suggestion-list-artifact.html`, replace the two `{{PROJECT_NAME}}` placeholders with the workspace folder's name, embed the current suggestion-list rows as JSON in `<script id="suggestion-list-data">`, set the `<script id="last-updated-context">` block per §2.3's Initialization, write to `outputs/audit-suggestion-list-artifact.html`, and call `mcp__cowork__create_artifact` with this project's id (`claim-audit-suggestion-list--<project slug>`).

5. **Create this project's live audit-progress artifact** if the project doesn't have one yet (check: backing file `outputs/audit-progress-artifact.html`, same per-project rule). Follow the §2.6 Initialization sequence: read the template at `forensic-claim-audit/assets/audit-progress-artifact.html`, replace the two `{{PROJECT_NAME}}` placeholders with the workspace folder's name. Write to `outputs/audit-progress-artifact.html`, and call `mcp__cowork__create_artifact` with this project's id (`claim-audit-progress--<project slug>`).

6. **Create this project's consolidated audit-findings artifact** if the project doesn't have one yet (check: backing file `outputs/audit-findings-artifact.html`, same per-project rule; §2.9). Read the template at `forensic-claim-audit/assets/audit-findings-artifact.html`, replace both `{{PROJECT_NAME}}` placeholders with the workspace folder's name (the embedded `findings-data` starts empty), write to `outputs/audit-findings-artifact.html`, and call `mcp__cowork__create_artifact` with this project's id (`claim-audit-findings--<project slug>`). This single artifact is where every stage records its findings.

## Step 3 — Set the mode to multi-session

If Step 2.3 created `audit-progress.md` fresh, the Mode line is already `multi-session` — skip this step.

If `audit-progress.md` already existed (e.g., the user previously ran the orchestrator or set up the audit before), use `Edit` on `outputs/audit-progress.md` to replace the existing `**Mode:**` line with:

```
**Mode:** multi-session  <!-- single-session | multi-session — see §2.7 -->
```

Do not change any other content in the file. Existing stage statuses and Notes carry forward.

## Step 4 — Run the project-document inventory

After the workspace is initialized and the mode is `multi-session`, run the inventory so the user can see what's in the project folder before they start Stage 1.

1. Use `Read` on `../claim-project-inventory/SKILL.md` and read the entire file.
2. Execute every step of `claim-project-inventory` end-to-end (its Steps 1 through 6). It will walk the workspace, write `outputs/project-inventory.md` and `outputs/project-inventory.xlsx`, flag any missing expected items by what-they-are (not by category label), and print its own closing summary in chat — including a descriptive bullet for each missing item per the inventory's Step 6 template.
3. Do not collapse, summarize, or re-render the inventory's closing message. Let it speak for itself. Step 6 below is a separate hand-off message that does **not** repeat the missing-items list.

If the inventory skill fails, do **not** abort the setup — note the failure to the user in the Step 6 hand-off message and let them decide whether to fix it before starting Stage 1. (An empty or claim-document-less workspace can't reach this step; the Step 0.5 pre-flight already hard-stops on that.)

## Step 5 — Divide the property into macro-areas

Establish the macro-area map (§2.8 of the protocols) so every stage has its unit of work before Stage 1 begins.

1. Use `Read` on whatever project docs the Step 4 inventory found — the carrier estimate (including its sketch/diagram pages, the best source for the room layout) if present, plus sketches, photos, and walkthrough-video frames (`video-intake/`). Propose a division of the property into macro-areas (large physical sections grouping rooms/categories — e.g., Main Floor Interior, Upper Floor Interior, Basement, Exterior & Roof, Detached Structures). Adapt to the property; don't force a fixed set.

2. Show the proposed division and ask the user to confirm or adjust it. This is the user's call — they have the final say on how the property is divided.

3. The Step 0.5 pre-flight guarantees a carrier estimate and project documentation exist, so a division can normally be proposed. If the docs are still too thin to support one, don't invent a division — ask the user to name the macro-areas for this claim, or note that the map will be set during the Scope Audit and move on.

4. Once confirmed, write `outputs/macro-areas.md` per the §2.8 structure, with the `**Last updated:**` stamp set to `at project setup`.

5. **Seed the progress sub-points and the stage-outputs folder** now that the macro-areas are known:
   - Edit `outputs/audit-progress.md` to add the confirmed macro-areas as sub-points under each stage (per §2.6) — every audit stage except Stage 1 (Scope) and Final Delivery, which stay without sub-points. Refresh the progress artifact (fill each applicable stage's `areas` array in the embedded JSON) and call `mcp__cowork__update_artifact` with this project's progress artifact id (per-project rule, §2.3).
   - Create the `outputs/stage-outputs/` sub-folder (per §2.9) so each stage has somewhere to write its work product.

## Step 6 — Hand off to Stage 1

The inventory's Step 6 closing message already printed the workspace summary and (if applicable) the missing-items list. Do not re-summarize that.

The hand-off message includes:

- That setup is done.
- How to start Stage 1: open a new chat in this same project and send `/claim-scope-audit`.

Nothing else. No explanation of how subsequent stages work, no restating what the inventory said.

If the inventory failed at Step 4, the message also names what went wrong in one sentence so the user can decide whether to fix it before Stage 1.

Then **stop**. Do not begin Stage 1 in this chat. Stage skills inside this plugin enforce the mode-routing themselves; this skill's job is purely setup + inventory.

## What this skill does NOT do

- Does not run any of the 13 audit stages.
- Does not produce any audit findings, suggestions, or recommendations.
- Does not proceed without the essential claim documents. The Step 0.5 pre-flight hard-stops — before any file is created — if the folder is empty, holds only samples/templates, or lacks a carrier estimate or project documentation. Conditionally-required items (drying log, measurement report) don't hard-stop; the Step 4 inventory flags those.
- Does not flip the mode back to `single-session`. That's the master orchestrator's job, and only after asking the user.

## Related skills

- `claim-project-inventory` — invoked automatically at Step 4. Walks the workspace, categorizes each file, and flags missing expected categories.
- `forensic-claim-audit` — single-session entry point. Runs all 13 stages back-to-back. When invoked while the Mode is `multi-session`, asks the user whether to switch.
- `claim-scope-audit` — Stage 1. Begin here in a fresh chat after this setup completes.
- `claim-audit-protocols` — the protocols this skill operates against. Read at Step 0.

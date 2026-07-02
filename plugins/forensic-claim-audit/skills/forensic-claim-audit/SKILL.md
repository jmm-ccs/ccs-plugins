---
name: forensic-claim-audit
description: Run the full 13-stage CCS forensic insurance claim audit end-to-end on a property insurance estimate. Use for any prompt like "audit this claim," "build a supplement," "run the full forensic audit," "review the carrier estimate," or whenever the user uploads a carrier estimate plus project files. Walks scope → line items → type-of-loss → code/ordinance → trades → sales tax with verify-then-advance gates between every stage. Hands off to claim-audit-finalizer at the end, which runs the Sanity Audit, resolves open flags, collects user-confirmed reason-box wording, and invokes claim-pdf-annotator to render and visually verify the marked-up copy of the carrier's estimate (the audit's end deliverable).
---

# Forensic Claim Audit — Master Orchestrator

This skill runs the complete CCS forensic claim audit. It chains the 13 stage skills in order, holds the verify-then-advance gates, and ends by handing off to `claim-audit-finalizer` for closing.

## Step 0 — Read the protocols in full

Before doing anything else, use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read the entire file end-to-end. Do this every time this skill is invoked, regardless of whether you read the protocols earlier in the conversation. Each new stage of the audit is also going to instruct you to re-read the protocols file in full — that is by design.

After reading the protocols, ask the user to confirm two things are in the project folder before the audit starts:

1. The carrier's estimate (PDF or Xactimate export).
2. Project files for the loss — photos, videos, sketches, contractor scope of work, measurement reports, drying logs, invoices, anything else they have.

The message should be short and ask them to reply with "begin audit" when ready. Nothing about what's *not* needed.

Do not proceed until the user replies "begin audit" (or equivalent).

## Step 0.5 — Set up the audit workspace

After the user replies "begin audit," set up the workspace before starting Stage 1. The project folder is the Cowork workspace — already attached. Do not ask the user to identify it. Follow the **Initialization** sequences in §2.3 (suggestion list) and §2.6 (audit progress) of the protocols, plus the audit-mode check below.

**Walkthrough videos get processed first.** If the project folder contains walkthrough videos (`.mov`, `.mp4`, etc.) without a matching `video-intake/<video name>/` folder, run the video intake (Read `../claim-video-intake/SKILL.md` and execute it) before Stage 1 starts — after the mode check, before or alongside Step 0.5.1. The audit stages read the extracted frames and narration transcript, never the raw video file.

> **Important — invocation vs. read.** The actions in this Step 0.5 (workspace creation, mode check, mode write) execute **only when this skill is the active skill** — i.e., the user just invoked `forensic-claim-audit` as the entry point. If another skill or tool happens to `Read` this file (e.g., the new-skill author looking up the stage list), do **not** perform these actions. Reading a SKILL.md is not the same as invoking the skill. See §2.7 of the protocols for the same distinction restated.

### Step 0.5.0 — Audit mode check (runs first, before file creation)

This skill is the single-session entry point. Before doing anything else, check the audit mode (§2.7 of the protocols):

1. Use `Read` on `outputs/audit-progress.md`. Determine the current mode:
   - **If the file exists and the `**Mode:**` line says `single-session`**: the project is already aligned with the orchestrator. Skip the question below and proceed directly to Step 0.5.1.
   - **Otherwise** (file doesn't exist, the Mode line is missing, the value is `multi-session`, or the value is anything else): treat the current mode as `multi-session` per §2.7's default. Continue to step 2 below.

2. Use `AskUserQuestion` to ask whether to switch to single-session for this run. The question must give the user enough to actually decide — what each mode buys them, in plain consequence terms:

   - Each stage in its own chat (current setting, default): each stage stays focused; suggestion list and progress carry over between chats automatically; you can step away and come back to a specific stage later. Cost: more chats to track.
   - All 13 stages here in one chat: faster end-to-end, everything in one place. Cost: one long chat to scroll/return to — and on anything but a small claim, one chat may not hold the whole audit, forcing a mid-audit move to fresh chats anyway. Multi-session is the safer choice for full-size claims.

   The actual choice goes last, in one sentence. Options (2 — list the "No" option first so it's the default):

   - `No — keep each stage in its own chat`
   - `Yes — run all 13 stages here`

   If the user picks **No**: tell them you'll leave things as they are. Tell them to open a new chat and send `/claim-scope-audit` when they're ready for Stage 1, and mention `/claim-audit-setup` if they want to seed the workspace files first. Then stop.

   If the user picks **Yes**: continue to Step 0.5.1. The Mode line gets set to `single-session` there.

3. If the user picked **No**, the orchestrator stops here. Do not run Step 0.5.1.

### Step 0.5.1 — Create the workspace files

**Idempotency (§2.14).** If `outputs/audit-progress.md` already exists with real audit state, you're resuming an existing audit — preserve it. The per-item "if it doesn't already exist" / "leave it as-is" guards below ensure re-running never clobbers prior work; the only field this orchestrator deliberately rewrites is the `**Mode:**` line (to `single-session`), per Step 0.5.0.

1. **Create the `outputs/` sub-folder** inside the workspace if it doesn't already exist. If the folder is not writable, use `AskUserQuestion` to ask the user where to put `outputs/` and create it there.

2. **Initialize `outputs/audit-suggestion-list.md`** with the table headers from §2.3 if the file doesn't already exist (resuming a prior audit, leave it as-is).

3. **Initialize `outputs/audit-progress.md`** per §2.6 if the file doesn't already exist — using `**Mode:** single-session` on the Mode line. The 14 status rows (Stages 1–13 + Final Delivery) all start at `Not started`.

   If `outputs/audit-progress.md` already exists, do **not** overwrite the table. Use `Edit` to replace the existing `**Mode:**` line with `**Mode:** single-session` (this is the orchestrator's commitment — it always runs in single-session mode after the Step 0.5.0 check above has either confirmed or switched the mode). Existing stage statuses and Notes carry forward.

4. **Create this project's live suggestion-list artifact** if the project doesn't have one yet — the check is the backing file `outputs/audit-suggestion-list-artifact.html`, never the artifact list, and an artifact from another project is never "existing" (per-project rule, §2.3 of the protocols). Read `forensic-claim-audit/assets/suggestion-list-artifact.html`, replace the two `{{PROJECT_NAME}}` placeholders with the workspace folder's name (e.g., `Greensboro Claim`), embed the current suggestion-list rows as JSON in the `<script id="suggestion-list-data">` block, set the `<script id="last-updated-context">` block per §2.3's Initialization, write to `outputs/audit-suggestion-list-artifact.html`, and call `mcp__cowork__create_artifact` with this project's id (`claim-audit-suggestion-list--<project slug>`).

5. **Create this project's live audit-progress artifact** if the project doesn't have one yet (check: backing file `outputs/audit-progress-artifact.html`, same per-project rule). Read `forensic-claim-audit/assets/audit-progress-artifact.html`, replace the two `{{PROJECT_NAME}}` placeholders with the workspace folder's name. The template already has all 14 stages embedded at status `Not started`, so no JSON edit is needed for a fresh audit. Write to `outputs/audit-progress-artifact.html`, and call `mcp__cowork__create_artifact` with this project's id (`claim-audit-progress--<project slug>`).

5b. **Create this project's consolidated audit-findings artifact** if the project doesn't have one yet (check: backing file `outputs/audit-findings-artifact.html`, same per-project rule; §2.9). Read `forensic-claim-audit/assets/audit-findings-artifact.html`, replace both `{{PROJECT_NAME}}` placeholders with the workspace folder's name (the embedded `findings-data` starts empty), write to `outputs/audit-findings-artifact.html`, and call `mcp__cowork__create_artifact` with this project's id (`claim-audit-findings--<project slug>`). Every stage records its findings into this one artifact.

6. **Divide the property into macro-areas** (§2.8 of the protocols). Read whatever project docs exist — the carrier estimate and its diagram pages, sketches, photos, walkthrough-video frames and transcript (`video-intake/`) — and propose a division of the property into macro-areas (large physical sections grouping rooms/categories). Show it, ask the user to confirm or adjust, then write `outputs/macro-areas.md` per the §2.8 structure with `**Last updated:** at project setup`. If no project docs are present, ask the user to name the macro-areas, or note the map will be set during the Scope Audit. Stage 1 will reconcile this map once the true scope is confirmed.

7. **Seed the progress sub-points and the stage-outputs folder.** Now that the macro-areas are known, edit `outputs/audit-progress.md` to add them as sub-points under each stage (per §2.6) — every audit stage except Stage 1 (Scope) and Final Delivery — and refresh the progress artifact (fill each applicable stage's `areas` array). Create the `outputs/stage-outputs/` sub-folder (per §2.9).

8. **Confirm and move on.** One short sentence: setup is done, Stage 1 is starting. No re-explanation of what got set up. Then proceed to Stage 1.

Workspace creation belongs to setup — this orchestrator (which runs setup inline) and `claim-audit-setup`. Individual stage skills **no longer** self-create the workspace: per §2.14 of the protocols, a stage invoked without an active project (no `outputs/audit-progress.md`) refuses and sends the user to `/claim-audit-setup` rather than initializing anything. Step 0.5 here is the orchestrator's inline setup, plus the mode-check specific to invoking the orchestrator (which writes `single-session` after the user confirms). The explicit multi-session counterpart, `claim-audit-setup`, runs the same workspace-creation up front and writes `multi-session` deliberately, then stops without starting Stage 1.

## How to walk the stages

For each stage below:

1. Use `Read` on `../claim-audit-protocols/SKILL.md` and read the full file again. The protocols must be actively in attention for the new stage — do not skip this read.
2. Use `Read` on the corresponding stage skill file (`../claim-<stage>-audit/SKILL.md`).
3. **Update the audit progress** (per §2.6 of the protocols): mark this stage's status as `In progress` in `outputs/audit-progress.md` and refresh the live artifact via `mcp__cowork__update_artifact`. Do not write a clock timestamp.
4. Execute the audit per the stage skill's instructions.
5. When you believe the stage is complete, mark the stage as `Awaiting verification` (refresh the artifact), then ask:
   > "Do you believe the [Stage Name] is complete? If not, please direct me to the incomplete item(s)."
6. Wait for explicit user confirmation.
7. After confirmation, mark the stage as `Complete` (refresh the artifact). Do not write a clock timestamp. Then route per §4 of the protocols (which honors the audit mode in `outputs/audit-progress.md`). Inside this orchestrator, Step 0.5.0 has already locked the mode at `single-session`, so §4's single-session branch will fire — i.e., prompt *"Ready for [Next Stage Name]."* and then chain into the next stage in this same chat.
8. Wait for the user to say "begin [next stage]" before reading the next stage skill.

If the user opts to skip a stage, mark it as `Skipped` (refresh the artifact) and proceed to the next stage.

If the user invokes HALT or pushes back on a finding, follow §6 of the protocols: stop, re-anchor against the carrier PDF using the `Read` tool, reissue only the corrected portion, do not move forward. Do not change the progress status during a HALT — the stage stays at whatever status it had before.

## The 13 stages — in order

1. **Scope Audit** → `../claim-scope-audit/SKILL.md`
2. **Line Item Audit** → `../claim-line-item-audit/SKILL.md`
3. **Line Item Completeness Audit** → `../claim-line-item-completeness-audit/SKILL.md`
4. **Related Items Audit** → `../claim-related-items-audit/SKILL.md`
5. **Type-of-Loss Audit** → `../claim-type-of-loss-audit/SKILL.md`
6. **Appurtenances Audit** → `../claim-appurtenances-audit/SKILL.md`
7. **Code, Ordinance & Law Audit** → `../claim-code-ordinance-law-audit/SKILL.md`
8. **Continuity / Room-Myopia Audit** → `../claim-continuity-audit/SKILL.md`
9. **Storage, Debris & Disposal Audit** → `../claim-storage-debris-audit/SKILL.md`
10. **Cleanup & Occupant Protection Audit** → `../claim-cleanup-protection-audit/SKILL.md`
11. **Trades Audit** → `../claim-trades-audit/SKILL.md`
12. **Permits & Contractor Cost Audit** → `../claim-permits-contractor-cost-audit/SKILL.md`
13. **Sales Tax Audit** → `../claim-sales-tax-audit/SKILL.md`

## Step 14 — Output

The Stage 13 gate (handled by the loop in "How to walk the stages" → §4 of the protocols → single-session branch) will have already issued the *"Ready for Output Process."* prompt. When the user replies "begin output process" (or equivalent), use `Read` on `../claim-audit-finalizer/SKILL.md` and execute it. The finalizer runs the Supplement Sanity Audit, flags items that might trigger insurance-fight or homeowner-negotiation friction (asks the user about each), resolves every open flag with the user, collects user-confirmed wording for every reason box, and invokes `claim-pdf-annotator` to render the marked-up copy of the carrier's estimate — the full carrier estimate reproduced with CCS's edits applied in-line (changed values and new lines in the CCS edit color, a justification box under each change/addition) — and visually verify it page by page against the carrier estimate and the sample supplements. The deliverable lands in `outputs/` in the project folder. For the XLSX working set, run `claim-suggestion-list-export` on demand.

The PDF annotator is also available as a standalone skill the user can invoke any time during the audit to get a current snapshot of the suggestion list rendered onto the carrier PDF.

## Tools you will use repeatedly during the audit

- **`Read`** — on the carrier PDF for every line-item anchor, on photo/sketch files for evidence, on the protocols file at every stage transition, on each stage skill file when starting it.
- **`WebSearch`** — for every "live-search verify" directive in the protocols (sales tax rates, jurisdiction codes, permit fees, IICRC formula values, code adoption status).
- **`bash`** with Python — for every multi-item sum, every percent calculation, every tax rate × line total computation. Do not predict math in your head.
- **`AskUserQuestion`** — used per-suggestion to gather Accept / Reject / Modify / Question decisions before any entry is added to the suggestion list (per §2.3 of the protocols).

If a stage seems to require a tool that isn't available, stop and tell the user — do not improvise.

## When the user wants to skip stages

Some claims don't need every stage. If the user wants to skip one (e.g., no appurtenances on a condo unit), confirm by reading back what they're skipping and why, then proceed to the next stage. Note the skip in the marked-up estimate so the carrier sees the audit was deliberate, not incomplete.

## When responses start drifting

If you notice your own responses showing the warning signs the protocols flag — hyperbolic language ("widespread," "excessive"), item numbers not matching the carrier PDF on a Ctrl+F check, math not bottom-up summing, the same correction proposed twice — stop and re-read `../claim-audit-protocols/SKILL.md` in full before continuing. Drift is the expected failure mode in long audits, and re-reading the protocols is the fix.

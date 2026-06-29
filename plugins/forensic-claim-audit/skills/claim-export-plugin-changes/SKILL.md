---
name: claim-export-plugin-changes
description: On-demand utility for the CCS forensic claim audit. Exports the auditor's on-device process-change-request log — the running list of "make the audit work this way by default" requests captured per protocols §2.16 — into a single shareable file to send to whoever maintains the audit process, so approved changes can be folded in for everyone. Trigger when the user says "export my change requests," "send my process changes," "export the change list," "send my requested tweaks to the process," or wants to contribute their requested process improvements. Independent of any audit stage.
---

# Claim Export Plugin Changes (On-Demand Utility)

Goal: produce a single shareable copy of the auditor's **process-change-request log** — the running list of "I'd like the audit to work this way by default" requests captured during audits (protocols §2.16) — so it can be sent to whoever maintains the audit process and folded in for the whole team.

This is the change-request counterpart to `claim-experience-export`. The experience log captures which suggestions get accepted or rejected; this captures how the process itself should change. Both are sent in the same way and reviewed by the maintainer.

This skill produces no audit findings and is independent of the 13 stages.

## Step 0 — Read the protocols

Use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read the entire file end-to-end before doing anything else. Pay particular attention to §2.16 (how change requests are captured), §2.15 (the PII-scrub rules these entries also follow), and §9 (voice). Do this every time this skill is invoked.

## Prerequisite — enforced gate (refuse until met)

Run this check before any work, per §2.14 of the protocols. Re-check on every attempt — never warn once and proceed.

**Something to export.** The change-request log `~/.ccs-audit/plugin-change-requests.md` must exist and hold at least one entry. If it's missing or empty, there are no process-change requests to send yet — say so plainly (and note that asking the audit to work differently, then choosing to make it permanent, is what adds to this list, per §2.16), then stop.

(No active-project gate: change requests live on-device, not inside a claim, so this can run anytime — inside an audit or not.)

## Step 1 — Read and sanity-check the log

`Read` `~/.ccs-audit/plugin-change-requests.md`. Confirm each entry is about the *process*, not a claim — run the §2.15 PII checklist over it; if any claim specifics slipped in (names, address, claim/policy numbers, file names, exact dollars, dates), generalize or strip them before exporting. This is a §2.15 loop: check → fix → re-check, until the log is clean.

## Step 2 — Write the file, then hand it to the user

Write a single shareable copy (keep the readable structure — a person reviews it and turns it into process edits), then **hand it directly to the user** so they actually receive the file, not just a path to it:

1. Write to `outputs/plugin-change-requests-export.md` if inside an active project (`outputs/audit-progress.md` exists), otherwise to `~/.ccs-audit/plugin-change-requests-export.md`.
2. **Present that file to the user** (the file-sharing / present-files step) so it is handed over directly for them to download and send on.

## Step 3 — Confirm to the user

State plainly, via `bash` count (§1.4): how many change requests are on the list, that the file has been handed to them, and that it's safe to send to whoever maintains the audit process.

Do not start any audit stage or other next step.

## What this skill does NOT do

- Does not change the installed audit process itself — it only exports the request list. Permanence is the maintainer's call (§2.16).
- Does not include claim PII — only process-level requests.
- Does not capture new requests — that happens inline during audits per §2.16. This skill only exports what's already on the list.

## Related skills

- `claim-experience-export` — the sibling: exports accepted/rejected suggestions for the learning set. Same send-it-to-the-maintainer pattern.
- `claim-audit-protocols` — §2.16 defines how change requests are captured; read at Step 0.

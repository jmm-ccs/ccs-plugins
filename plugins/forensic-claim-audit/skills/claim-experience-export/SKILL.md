---
name: claim-experience-export
description: On-demand utility for the CCS forensic claim audit. Rolls this claim's accepted and rejected suggestions into the auditor's durable on-device experience log (feature-light, PII-scrubbed) and writes a single shareable export file teammates can send in to be aggregated into the team's learning set. Trigger when the user says "export the experience log," "capture this claim's accept/reject experience," "give me the file to send for the learning set," "export accepted and rejected suggestions for learning," or wants to contribute this audit to the team's learning data. Part of the self-learning capture (protocols §2.15). Independent of any audit stage.
---

# Claim Experience Export (On-Demand Utility)

Goal: turn this claim's accept/reject outcomes into durable, shareable learning data. It does two things: (1) rolls the current claim's accepted and rejected suggestions into the auditor's **durable on-device experience log** — feature-light and PII-scrubbed, accumulating across every claim — and (2) writes a single **shareable export file** the auditor can send to whoever aggregates the team's learning set.

This is the capture half of the self-learning loop. The accepted suggestions are the positive signal, the rejected ones the negative signal; together they are how the goal-fit loop (protocols §2.15 keystone) gets better over time, and they are the labeled data a future scoring model would train on.

This skill produces no audit findings, changes no suggestion, and is independent of the 13 stages.

## Step 0 — Read the protocols

Use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read the entire file end-to-end before doing anything else. Pay particular attention to:

- §1 — Output Integrity (records must faithfully represent the source; never fabricate a feature)
- §2.3 — the suggestion list spec and disposition values (accepted suggestions live here)
- §2.15 — the feedback loops, especially loop 10 (the rejection log) and the keystone goal-fit loop this data feeds
- §9 — how to talk to the user

Do this every time this skill is invoked, regardless of whether the protocols were loaded earlier in the conversation.

## Prerequisite — enforced gate (refuse until met)

Run this check before any work, per §2.14 of the protocols. Re-check on every attempt — never warn once and proceed.

1. **Active project.** `outputs/audit-progress.md` must exist (setup has run). If it doesn't, refuse and tell the user to run `/claim-audit-setup` first, then stop.
2. **Something to capture.** There must be experience to export: `outputs/audit-suggestion-list.md` has at least one data row (accepted suggestions) **or** `outputs/rejected-suggestions.md` exists with at least one entry (rejected suggestions). If both are empty, there's nothing to learn from yet — say so plainly and stop.

Proceed only when both pass.

## What gets captured — and what never does

Each suggestion becomes one **feature-light, PII-scrubbed record.** The features are what generalize across claims; the identifying detail is what must never leave the claim.

**Keep — the generalizable features:**

| Field | Meaning |
|---|---|
| `outcome` | `accepted` or `rejected` |
| `disposition` | for accepted: `Agreed` / `Halted` / `Needs-info` (from the suggestion list) |
| `modified_before_accept` | for accepted: `true` if the user modified it before accepting, else `false` |
| `suggestion_type` | `Add` / `Correct` / `Flag` |
| `stage` | the originating stage number (1–13) |
| `loss_type` | the claim's peril — `fire` / `water` / `wind-hail` / etc. |
| `jurisdiction` | **state level only** (e.g., `FL`, `NC`) — never a city, address, or ZIP |
| `magnitude_band` | dollar-impact bucket, **not** the exact figure — `<$100` / `$100–$1k` / `$1k–$5k` / `>$5k` |
| `subject` | a **generalized** one-line description of what the suggestion was about — e.g., "subfloor companion item under flooring tear-out", "waste-factor correction on baseboard", "missing labor on a material-only line". Strip room names, item numbers, and any specific identifiers. |
| `reason` | for rejected: why (the user's reason, generalized); for accepted: optionally why it fit the goal |
| `claim_token` | a short, non-identifying hash of the project folder name (so re-running updates instead of duplicating, and the aggregator can count distinct claims without knowing which) |

**Never include — PII / identifying detail:** policyholder or contractor names, property address, city, ZIP, claim number, policy number, exact dollar amounts, dates, file names, carrier line numbers, and the carrier's identity. If a feature can't be generalized without leaking one of these, drop the feature rather than skip the scrub.

> If you can't determine `loss_type` or `jurisdiction` from the audit (stage outputs, the carrier estimate, the sales-tax stage), record them as `unknown` — never guess (§1).

## Step 1 — Gather this claim's suggestions

1. `Read` `outputs/audit-suggestion-list.md` — every row is an **accepted** suggestion (its disposition is in the Disposition column).
2. `Read` `outputs/rejected-suggestions.md` if it exists (§2.15 loop 10) — every line is a **rejected** suggestion with its reason.
3. Determine `loss_type` and `jurisdiction` (state) for the claim from the stage outputs / carrier estimate; compute each accepted suggestion's `magnitude_band` from its proposed change with `bash` (§1.4) — the **band**, never the exact figure.

## Step 2 — Reduce and scrub

Convert each suggestion to the record schema above. Generalize the `subject` and `reason` — describe the *kind* of suggestion, not the specific line. Then run the PII checklist against every record before it is written: no names, address, claim/policy numbers, exact dollars, dates, file names, carrier line numbers, or carrier identity. A record still carrying any of those is not ready — fix it, or drop the offending field. This is a §2.15 loop: scrub → check → fix → re-check, until every record is clean.

## Step 3 — Roll into the durable on-device experience log

The durable log is the auditor's own, on-device, and persists across **every** claim — it lives outside any single claim's project folder so it survives from one audit to the next, and outside the installed plugin so a plugin update can't wipe it: **`~/.ccs-audit/experience-log.jsonl`** (the auditor's on-device CCS data folder; create the folder and file if absent). One JSON record per line (JSONL) — the format that appends cleanly and doubles as a training set later.

- **Dedup by `claim_token`.** If records for this `claim_token` are already in the log, replace them (the user may re-run after more decisions) rather than appending duplicates.
- Append this claim's scrubbed records.

This file is the raw, accumulating experience. It is already PII-scrubbed, so it is safe to share as-is.

## Step 4 — Write the file, then hand it to the user

Write a single shareable copy to the claim's `outputs/`: **`outputs/experience-export-<project-slug>.jsonl`**, containing the auditor's **full** accumulated experience log (all claims to date) — that is what an aggregator wants from each teammate. Then **hand it directly to the user** (the file-sharing / present-files step) so they actually receive the file to send on, not just a path.

(If the user asks for only this claim's contribution, write just this claim's records as `outputs/experience-export-<project-slug>-thisclaim.jsonl` instead, and hand that over the same way.)

## Step 5 — Confirm to the user

State plainly, using `bash` counts (§1.4):

- How many records were captured from this claim (accepted vs. rejected).
- That they were rolled into the on-device experience log, and how many records the log now holds in total.
- That the file has been handed to them, and that it's PII-scrubbed and safe to send to whoever aggregates the team's learning set.

Do not start any audit stage or other next step.

## What this skill does NOT do

- Does not change the suggestion list, the rejection log, or any audit finding.
- Does not include any PII — only the generalizable features above.
- Does not aggregate other people's exports or build the curated exemplars — that's the human curation step (see `forensic-audit-self-learning-plan.md`).
- Does not train or score anything — it only captures and exports the data.

## Related skills

- `claim-suggestion-list-export` — different output: the `Agreed`-only working set CCS builds the supplement from. This skill instead captures *both* accepted and rejected suggestions, scrubbed, for learning.
- `claim-audit-protocols` — §2.15 (the loops this data feeds, including the keystone goal-fit loop and loop 10's rejection log). Read at Step 0.

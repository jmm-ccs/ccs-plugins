---
name: claim-continuity-audit
description: Stage 8 of the CCS forensic claim audit. Catch cross-room continuity issues — items that aren't tied to a single damaged room but affect undamaged adjacent rooms (line-of-sight floor refinishing, transit-path floor protection, paint continuity around openings, finish matching across continuous runs). Trigger after the Code/Ordinance Audit, or when the user mentions "matching across rooms," "line of sight," "we have to refinish this floor too because it's connected," or "protection of undamaged rooms during construction."
---

# Continuity / Room-Myopia Audit (Stage 8 of 13)

Goal: catch cross-room impacts the carrier missed because they scoped each room in isolation. Real construction does not respect room boundaries.

## Step 0 — Read the protocols

Use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read the entire file end-to-end before doing anything else in this stage. Do this every time this skill is invoked.

**§1.5 reminder — every suggestion this stage raises needs its plain-language Why + Source.** In basic language: what's wrong or missing and why the fix is justified, plus the basis it rests on — a named project file, a verified citation, or an openly flagged judgment call. No Why or no Source means it isn't ready: don't propose it and don't record it (§1.5 completeness gate, §2.3).

## Prerequisite

Stages 1–7 confirmed complete.

## What "room myopia" looks like

The carrier's adjuster scopes Room A because Room A had the loss. They write the line items for Room A. Then they move on. They miss the cross-room impacts.

Use `Read` on `references/cross-room-impacts.md` for the starting-point list of cross-room categories (line-of-sight refinishing, continuous-run material, wall paint, ceiling continuity, transit-path protection, stairs as transit, shared wall demolition, HVAC contamination, exterior finish matching). The reference is a **starting point, not exhaustive** — apply additional industry-standard cross-room considerations as the project warrants.

## Method

This stage is the **boundary-spanning exception** to the macro-area rule (§2.8). Every other stage works one macro-area at a time; this one exists precisely to catch impacts that *cross* boundaries, so its working unit is the adjacency/relationship **between** areas, not a single area in isolation. Read `outputs/macro-areas.md` and use it as your frame — pay special attention to where two macro-areas meet (e.g., interior-to-exterior transitions, floor-to-floor stairwells, a continuous floor running from one macro-area into the next), since those boundaries are exactly where the carrier's room-by-room scoping breaks down.

Use `Read` on the carrier PDF, the project sketches, Matterport scans, and walkthrough-video frames (`video-intake/<video name>/frames/`). A walkthrough video is the strongest adjacency evidence in the project folder: consecutive frames show the camera physically traveling from one room into the next, which is exactly the line-of-sight and transit-path relationship this stage audits. Cite a frame *range* for adjacency (e.g., *"frames frame-00210 through frame-00216 — the camera moves from the hallway into the living room over the same continuous oak floor, no threshold"*), and pair it with the narration transcript (`video-intake/<video name>/transcript.md`) where the narrator calls out a transition. If a raw video exists with no `video-intake/<video name>/` folder, run `claim-video-intake` before starting this stage.

Walk every room and every transit path on the project, including the transitions between macro-areas. For each adjacency, ask:

1. Does damage in Room A force work in Room B? (Material continuity, finish match, sightline.)
2. Does the construction in Room A traverse Room B? (Transit protection.)
3. Does demolition in Room A propagate stress into Room B? (Cracks, popped seams.)
4. Does the HVAC return path connect Room A to other rooms?
5. Does any finish run continuously through both rooms? (Trim, paint, flooring.)

Inventory each cross-room item, note its source and destination rooms, and recommend supplement line items.

## Audit-Myopia check

This stage's name and the protocol's name are similar but different. The Audit-Myopia *check* (from protocols §2.4) is about not double-counting between stages of *this audit*. The Room-Myopia *audit* (this stage) is about the carrier's tendency to scope each room in isolation. Both apply here. Run the Audit-Myopia check on every cross-room recommendation against everything previously added.

## Output

Substantive — four-section format. **Recommendations** organized by cross-room item with source room → impacted room mapping.

## Stage output (§2.9)

This stage's deliverable is the **cross-area continuity record** — each impact that crosses a boundary, mapped source area/room → impacted area/room, with the recommended supplement line. Because this stage works the boundaries between areas (not one area in isolation), organize the file by **boundary/relationship** rather than by single macro-area. Record it in `outputs/stage-outputs/08-continuity.md` and record its findings in the consolidated audit-findings artifact (`claim-audit-findings`, §2.9) — this stage's entry, one group per boundary or cross-area relationship. Markdown is canonical.

## Stay in this stage's lane

Per §2.10 of the protocols, this stage decides only **impacts that cross room or area boundaries (line-of-sight floor refinishing, continuous-run finish matching, transit-path protection of undamaged rooms)**. Its working unit is the boundary *between* areas, not a single room.

While doing it you will see things that belong to other stages — corrections confined to one room's line items (Stages 2–4) or peril-specific items (Stage 5). Do not mention them, do not ask whether to flag them, and do not record them anywhere. Drop them; the owning stage re-examines the whole estimate and will catch them. Noticing an out-of-stage item and asking whether to flag it is the §2.10 violation to avoid.

## Recording suggestions in the suggestion list

For every cross-room suggestion this stage produces (line-of-sight floor refinishing, transit-path protection, continuous-run trim, etc.), walk each one through the per-suggestion confirmation flow defined in §2.3 of the protocols: call `AskUserQuestion` per suggestion with options Accept / Reject / Modify / Ask a question. Only Accepted entries get appended to `outputs/audit-suggestion-list.md` (disposition `Agreed`). Refresh the live artifact after each append.

**Strict per-suggestion flow (§2.3).** Every suggestion above gets its **own** `AskUserQuestion` call — one suggestion per call. Do not batch them, do not replace them with a single "shall I add these?" question, and do not ask the verification gate until every suggestion this stage produced has been individually Accepted, Rejected, or Modified-then-Accepted.

## Verification gate

> "Do you believe the Continuity / Room-Myopia Audit is complete? If not, please direct me to the incomplete item(s)."

After the user confirms, route per §4 of the protocols (which honors the audit mode in `outputs/audit-progress.md`). The next stage is **Storage, Debris, and Disposal Audit** (skill: `claim-storage-debris-audit`).

In single-session mode, §4 prompts *"Ready for Storage, Debris, and Disposal Audit."* and waits for "begin storage audit" (or equivalent) before chaining. In multi-session mode, §4 prints the multi-session hand-off and stops here — the user begins the Storage, Debris, and Disposal Audit in a fresh chat in this same Cowork project.

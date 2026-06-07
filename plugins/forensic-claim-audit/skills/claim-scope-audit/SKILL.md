---
name: claim-scope-audit
description: Stage 1 of the CCS forensic claim audit. Audit the overall scope of a property insurance estimate — the rooms and categories included — to flag any rooms or categories the carrier missed. Trigger when the user says "is the scope complete," "did the carrier miss any rooms," "compare the carrier's room list against my photos / sketch / Matterport," or starts a fresh audit. Does not touch line items inside rooms (that's Stage 2).
---

# Scope Audit (Stage 1 of 13)

Goal: produce an authoritative list of rooms and categories that should appear in the supplement, comparing the carrier's estimate against project documentation.

## Step 0 — Read the protocols

Use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read the entire file end-to-end before doing anything else in this stage. Do this every time this skill is invoked, regardless of whether the protocols were loaded earlier in the conversation. The Factual Integrity rules, the Carrier Estimate Protocol, the Audit-Myopia check, the HALT response pattern, and the Tool Usage table must all be actively in attention for this stage.

**§1.5 reminder — every suggestion this stage raises needs its plain-language Why + Source.** In basic language: what's wrong or missing and why the fix is justified, plus the basis it rests on — a named project file, a verified citation, or an openly flagged judgment call. No Why or no Source means it isn't ready: don't propose it and don't record it (§1.5 completeness gate, §2.3).

## Inputs you need

- Carrier's estimate (Xactimate PDF or export). Use `Read` on it.
- Project documentation: photos, video walkthroughs, sketches, Matterport scans, contractor's scope of work, FNOL narrative, third-party measurement reports (EagleView, HOVER, etc.). Use `Read` on each file.
  - **Walkthrough videos are read through their intake output, not the raw file.** If the project folder has a video with a matching `video-intake/<video name>/` folder, `Read` the extracted frames (`frames/`), the narration transcript (`transcript.md`), and the manifest there. If a video has **no** intake folder, run `claim-video-intake` (Read `../claim-video-intake/SKILL.md` and execute it) before starting this stage — the raw video file itself is not readable.
- The Forensic Claim Analysis Checklists, especially Checklist 2 (Field Scoping) — note that Checklist 2 is a **starting-point guide, not an exhaustive list**; supplement with any reliable, independently-verifiable, industry-standard guidance.
- The macro-area map (`outputs/macro-areas.md`, §2.8 of the protocols). Use `Read` on it. If it doesn't exist (setup was skipped), establish it first per §2.8 — propose a division from the docs + estimate and confirm with the user — before walking the scope.

If any of the inputs above other than the macro-area map are missing, list what's missing and stop.

## Method

Work **one macro-area at a time** (§2.8 of the protocols). Walk the macro-areas in the order the map lists them; produce the cross-walk for one macro-area, ask the per-macro-area gate, then move to the next. Don't dump the whole-property cross-walk in one pass.

1. **Extract the carrier's room/category list.** Use `Read` on the carrier PDF. Preserve order and titles exactly as the PDF has them — room names must match the PDF. Group the rooms under the macro-area each belongs to.

2. **Build an independent room/category list from the project documentation.** Use `Read` on photos, sketches, Matterport, walkthrough-video frames and transcript (`video-intake/<video name>/`), and the contractor's scope. For each room you identify, note the source evidence (file name, Matterport floor, sketch reference, video frame filename, or transcript timestamp). A walkthrough video is especially strong here: the frame sequence covers the property in walk order, so rooms the narrator passed through appear even if nobody photographed them — and a narration line naming the room (e.g., *"transcript.md [04:31] — 'this is the master toilet'"*) pairs with the frames at the same timestamp.

3. **Cross-walk the two lists.** Output a side-by-side table:
   - Column 1: Carrier's list (in carrier order)
   - Column 2: Independent list
   - Column 3: Match status (Match / Missing from carrier / Missing from project docs / Naming discrepancy)

4. **For each "Missing from carrier" finding,** cite the specific evidence (e.g., *"Master Toilet — visible in PHOTO-2026-02-28-12-37-10-15.jpg, also Floor2 Matterport bottom-left quadrant; not listed on carrier estimate"*).

5. **For naming discrepancies,** propose the carrier's naming convention — do not rename the carrier's rooms. The carrier's titles are preserved per the Carrier Estimate Protocol.

## Checklist 2 cues — starting points, not exhaustive

These are scoping cues from Checklist 2 (a starting-point guide). Apply additional industry-standard scoping considerations as warranted by the specific project.

- Structural integrity (foundations, walkways, patios, roof pitch / multiple roofing layers)
- Material degradation (curled/loose shingles, algae, granule loss, flashing, pipe boots, gutters)
- Interior systems (hidden moisture, mold, electrical compromised by water/heat, water heater strapping in seismic zones)
- Testing protocols (10×10 hail test squares, moisture meters, ITEL samples on carpet/vinyl)

These are scoping cues, not line items. If you spot evidence of structural cracking or hidden moisture in the photos, the *room* containing that evidence belongs on the scope list — the actual line items come in Stage 2.

## Stay in this stage's lane

Per §2.10 of the protocols, this stage decides only **which rooms and categories belong on the estimate**. It builds the room/category cross-walk — nothing about what goes *inside* a room.

While doing it you will see things that belong to other stages — a line item that looks underpriced or mis-quantified (Stage 2), a missing Material/Equipment/Labor component (Stage 3), a missing companion item like subfloor or a transition strip (Stage 4), peril-specific items (Stage 5), exterior structures like siding, fencing, or decks (Stage 6), or code upgrades (Stage 7). Do not mention them, do not ask whether to flag them, and do not record them anywhere. Drop them; the owning stage re-examines the whole estimate and will catch them. Noticing an out-of-stage item and asking whether to flag it is the §2.10 violation to avoid.

## Output

This is a substantive analytical response — produce the four-section format from §3 of the protocols (Analysis / Recommendations / Challenge to AI's Analysis / Challenge to User's Thinking) plus the verified/unverified facts section.

The **Recommendations** section must contain:

- The carrier's room/category list, in carrier order, unchanged
- Any rooms/categories you believe are missing, each with cited evidence
- Any naming discrepancies flagged for user awareness (carrier's name is retained either way)

## Stage output file & artifact

Per §2.9 of the protocols, this stage records its work product as a visible file: `outputs/stage-outputs/01-scope.md`. It contains the four-section findings above plus the scope cross-walk **organized by macro-area** (one section per macro-area, each listing the carrier rooms, the independent room list, and the match status for that area). Build it incrementally — append each macro-area's section as you confirm that area at its per-area gate — and finalize it at the stage-end gate.

Also record this stage's findings in the consolidated audit-findings artifact (id `claim-audit-findings`, §2.9): add/refresh the Scope Audit entry with one `group` per macro-area (columns: Carrier list / Independent list / Match status / Evidence), update the `updated` stamp, and call `update_artifact` after each macro-area. If the artifact doesn't exist yet (setup was skipped), create it from `forensic-claim-audit/assets/audit-findings-artifact.html` first. The markdown is canonical.

This is separate from updating the macro-area map (below) and from the suggestion list — the cross-walk file is *what the scope audit found*; the map is the divided list of areas the rest of the audit walks; the suggestion list holds the accepted scope additions.

## Recording suggestions in the suggestion list

For every suggestion this stage produces (missing rooms, naming flags, scope additions), walk each one through the per-suggestion confirmation flow defined in §2.3 of the protocols: call `AskUserQuestion` per suggestion with options Accept / Reject / Modify / Ask a question. Only Accepted entries get appended to `outputs/audit-suggestion-list.md` (disposition `Agreed`). Refresh the live artifact after each append.

**Strict per-suggestion flow (§2.3).** Every suggestion above gets its **own** `AskUserQuestion` call — one suggestion per call. Do not batch them, do not replace them with a single "shall I add these?" question, and do not ask the verification gate until every suggestion this stage produced has been individually Accepted, Rejected, or Modified-then-Accepted.

## Per-macro-area gate

After finishing the cross-walk for each macro-area, ask the short procedural gate (§2.8) before moving to the next one:

> "Do you believe the Scope Audit for [Macro-area] is complete? If not, please direct me to the incomplete item(s)."

## Update the macro-area map

Once the user has confirmed the scope at the stage-end gate below, reconcile `outputs/macro-areas.md` (§2.8) so it reflects the true scope before the next stage uses it:

- Assign any newly-found rooms to the macro-area they belong to.
- Add a new macro-area if a whole new section surfaced (e.g., a crawlspace or detached structure nobody had scoped).
- Update the `**Last updated:**` stamp to `after Stage 1 (Scope) confirmation`.

Then bring the progress sub-points into line with the confirmed map (§2.6): make sure every audit stage (2–13) carries the current macro-areas as sub-points in `outputs/audit-progress.md` — seed them if setup was skipped and they're absent, or add the new macro-area's sub-point to each stage if one surfaced here. Refresh the progress artifact. Also create `outputs/stage-outputs/` if it doesn't exist.

This is a file update, not a suggestion — it doesn't go through the per-suggestion flow. The scope additions themselves still go through the suggestion-list flow above.

## Verification gate

When you believe this stage is complete, ask:

> "Do you believe the Scope Audit is complete? If not, please direct me to the incomplete item(s)."

After the user confirms, update the macro-area map (above), then route per §4 of the protocols (which honors the audit mode in `outputs/audit-progress.md`). The next stage is **Line Item Audit** (skill: `claim-line-item-audit`).

In single-session mode, §4 prompts *"Ready for Line Item Audit."* and waits for "begin line item audit" (or equivalent) before chaining. In multi-session mode, §4 prints the multi-session hand-off and stops here — the user begins the Line Item Audit in a fresh chat in this same Cowork project.

(The gate response is procedural — short and direct, not 4-section. See §3 of the protocols.) Do not proceed to Stage 2 in this chat until §4's routing has fired and the user has either confirmed (single-session) or started a fresh chat (multi-session).

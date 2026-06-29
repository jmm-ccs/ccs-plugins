---
name: claim-scope-audit
description: Stage 1 of the CCS forensic claim audit. Audit the overall scope of a property insurance estimate — every "folder" on the estimate, meaning every room AND every non-room category (debris removal, general conditions, dumpster, permits, roofing, detached structures, labor minimums, etc.) — to flag any folder the carrier missed. The moment it reads the estimate it generates a complete folder list of every category present, then runs a missing-category self-check ("what folders might be missing"), then compares against every other file in the project folder and applies the CCS folder-inclusion rule. Trigger when the user says "is the scope complete," "did the carrier miss any rooms or categories," "compare the carrier's folder list against the project files," or starts a fresh audit. Does not touch line items inside folders (that's Stage 2).
---

# Scope Audit (Stage 1 of 13)

Goal: produce an authoritative list of **every folder** that should appear in the corrected estimate — rooms and non-room categories alike — comparing the carrier's estimate against project documentation, and self-checking for categories the estimate looks like it's missing.

## What counts as a "room" in this stage — every folder on the estimate

On an Xactimate estimate a **folder** is any titled section that holds line items. CCS treats **every folder as a "room" for scope purposes**, whether or not it is a physical space. This stage's "room list" is really a **folder list**, and it must contain *all* of them:

- **Physical rooms / spaces** — Kitchen, Master Bath, Hall, Attic, Crawlspace, Roof, an exterior elevation, etc.
- **Non-room categories** — any folder that groups work rather than a place: **Debris Removal**, **General Conditions**, **Dumpster / Hauling**, **Permits & Fees**, **Roofing**, **Detached Structure / Outbuilding**, **Labor Minimums**, **Content Manipulation / Pack-out**, **Mitigation / Drying**, **Temporary Repairs**, **Overhead items**, and the like. These are sections with items, not places — but they are folders, so they are part of the scope and go on the list exactly like rooms.

When this skill says "room," read it as **"folder (room or category)."** The match/missing/naming logic, the cross-walk, the suggestion flow, and the gates all apply to every folder the same way. Wherever a step is specific to a physical space (diagram adjacency, the photo map), it is noted as such; non-room categories simply don't have those attributes and skip them.

## Step 0 — Read the protocols

Use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read the entire file end-to-end before doing anything else in this stage. Do this every time this skill is invoked, regardless of whether the protocols were loaded earlier in the conversation. The Factual Integrity rules, the Carrier Estimate Protocol, the Audit-Myopia check, the HALT response pattern, and the Tool Usage table must all be actively in attention for this stage.

**§1.5 reminder — every suggestion this stage raises needs its plain-language Why + Source.** In basic language: what's wrong or missing and why the fix is justified, plus the basis it rests on — a named project file, a verified citation, or an openly flagged judgment call. No Why or no Source means it isn't ready: don't propose it and don't record it (§1.5 completeness gate, §2.3).

## Prerequisite — enforced gate (refuse until met)

Run this check before any Scope Audit work, per §2.14 of the protocols. Re-check on every attempt — never warn once and proceed.

**Active project.** `outputs/audit-progress.md` must exist (setup has run). The Scope Audit does **not** create the workspace — setup does. If that file doesn't exist, refuse: tell the user to run `/claim-audit-setup` first, then stop. Keep refusing every time until setup has actually run.

Scope is Stage 1, so it has no prior audit stage — setup having run is its only sequencing precondition. Once it passes, proceed.

## Inputs you need

- Carrier's estimate (Xactimate PDF or export), **including its sketch/diagram pages**. Use `Read` on it. The estimate is always present, and its diagram pages are the geometric baseline for the whole audit: every room the carrier drew, with dimensions and which rooms adjoin which. The scope walk is based on these diagrams.
- **Every other file in the project folder.** The comparison set is all of them — photos, video walkthroughs, sketches and floor plans, contractor's scope of work, FNOL narrative, third-party measurement reports (EagleView, HOVER, etc.), drying logs, correspondence, invoices. Don't pre-filter to "visual" documents: a denial letter, an invoice, or the contractor's scope can name a room no photo shows. Use `Read` on each file.
  - **Walkthrough videos are read through their intake output, not the raw file.** If the project folder has a video with a matching `video-intake/<video name>/` folder, `Read` the extracted frames (`frames/`), the narration transcript (`transcript.md`), and the manifest there. If a video has **no** intake folder, run `claim-video-intake` (Read `../claim-video-intake/SKILL.md` and execute it) before starting this stage — the raw video file itself is not readable.
- The Forensic Claim Analysis Checklists — **optional**: the Checklist 2 (Field Scoping) cues this stage needs are inline below, so a folder without the checklist PDF is fine. If the PDF is present, read it as a supplement to the inline cues (it's a **starting-point guide, not an exhaustive list**; supplement with any reliable, independently-verifiable, industry-standard guidance).
- The macro-area map (`outputs/macro-areas.md`, §2.8 of the protocols). Use `Read` on it. Setup creates it, and the Prerequisite gate above guarantees setup has run — so it will be present. If `outputs/audit-progress.md` exists but the map doesn't, setup didn't finish: stop and route the user to re-run `/claim-audit-setup` (per §2.14), rather than building the map here.

If the carrier's estimate or the project files are missing, list what's missing and stop. (The checklists are not a blocker — the cues are inline. The macro-area map comes from setup, which the Prerequisite gate above has already confirmed ran.)

## Method

Steps 1–2 (extract the complete folder list and run the missing-category self-check) are **one-time whole-estimate passes** done up front, the moment you read the estimate — they aren't the cross-walk, so they don't loop by area. From step 3 on, work **one macro-area at a time** (§2.8 of the protocols): walk the macro-areas in the order the map lists them, produce the cross-walk for one macro-area, ask the per-macro-area gate, then move to the next. Don't dump the whole-property cross-walk in one pass.

1. **Start with the carrier's estimate — generate the complete folder list, then its diagrams.** Use `Read` on the carrier PDF. The instant you read it, extract **every folder on the estimate** — every room *and* every non-room category (Debris Removal, General Conditions, Dumpster, Permits, Roofing, Detached Structures, Labor Minimums, etc.) — preserving order and titles exactly as the PDF has them. Folder titles must match the PDF. This is the authoritative starting folder list; nothing on the estimate is dropped from it because it "isn't a room." Group each folder under the macro-area it belongs to (non-room categories that aren't tied to one area — e.g., project-wide General Conditions or Permits — go under a single **Project-wide / General** macro-area grouping). Then, **for the physical rooms only**, read the estimate's sketch/diagram pages and note for each: its drawn dimensions and which rooms adjoin it. If the diagrams draw a space that never appears as a folder in the line items (a closet, hallway, stairwell, or chase drawn but not scoped), that is a finding backed by the carrier's own document — carry it into the cross-walk.

2. **Missing-category self-check — run this immediately, right after the folder list is built.** Before comparing against the project files, ask yourself: *given this loss type and the folders that are present, what categories/folders look like they might be missing from this estimate?* Reason from what the present folders imply — e.g., demolition or replacement line items imply a **Debris Removal** / **Dumpster** folder; any sizeable interior job implies **General Conditions**; permit-triggering work implies a **Permits & Fees** folder; a multi-trade job implies items that roll up under categories the estimate hasn't opened; contents in the work area imply **Content Manipulation / Pack-out**; a water or fire loss implies **Mitigation / Drying** or **Cleaning** categories. Each plausibly-missing category becomes a **scope suggestion** and is run through the per-suggestion flow in the "Recording suggestions" section below — exactly like a missing room — with its §1.5 Why (what implies it) and Source (the present folders/line items or verified standard that point to it). This is a self-generated finding: it does not require a project file to name the category, but the Why must explain what on the estimate implies it. Do not pre-judge it as out of scope because the carrier didn't open the folder — that omission is the finding.

3. **Compare against every other file in the folder.** Build an independent room/category list from **all** project files, not a visual subset. Use `Read` on photos, sketches, walkthrough-video frames and transcript (`video-intake/<video name>/`), the contractor's scope, measurement reports, drying logs, correspondence, and invoices. For each room you identify, note the source evidence (file name, sketch reference, video frame filename, transcript timestamp, or document + page). A walkthrough video is especially strong here: the frame sequence covers the property in walk order, so rooms the narrator passed through appear even if nobody photographed them — and a narration line naming the room (e.g., *"transcript.md [04:31] — 'this is the master toilet'"*) pairs with the frames at the same timestamp.

4. **Apply the folder-inclusion rule** (next section) to every folder on either list, to every adjoining room the diagrams show, and to every category surfaced by the step-2 self-check. For physical rooms, build the Tier-1 baseline first (every damaged room + every room adjoining one, mechanically off the diagrams), then run the Tier-2 judgment pass. For non-room categories, apply the category-inclusion test in that section. The carrier's list tells you what they scoped; the rule tells you what *belongs*.

5. **Cross-walk the two lists.** Output a side-by-side table covering **all folders** (rooms and categories):
   - Column 1: Carrier's list (in carrier order)
   - Column 2: Independent list
   - Column 3: Match status (Match / Missing from carrier / Missing from project docs / Naming discrepancy)

6. **For each "Missing from carrier" finding,** cite the specific evidence — for a room, e.g., *"Master Toilet — drawn on the carrier estimate's page-3 diagram adjoining the Master Bath, visible in PHOTO-2026-02-28-12-37-10-15.jpg; not listed as a room in the estimate"*; for a category, e.g., *"Debris Removal — the estimate scopes tear-out of drywall and flooring across three rooms but opens no debris/dumpster folder"* — and name which clause of the folder-inclusion rule pulls it in.

7. **For naming discrepancies,** propose the carrier's naming convention — do not rename the carrier's folders. The carrier's titles are preserved per the Carrier Estimate Protocol.

## When a folder belongs on the estimate — the CCS folder-inclusion rule

A folder is either a **physical room** or a **non-room category**. Rooms go through the two-tier room test below; categories go through the category-inclusion test that follows it.

### Physical rooms — the two-tier room test

The room test has two tiers: a mechanical baseline, then a judgment pass that looks beyond it.

**Tier 1 — the baseline (industry standard, applied mechanically).** *Any room with damage, and the room next to it.* Build this minimum set first, straight off the carrier's diagram pages:

1. **It has damage** — it's on the list.
2. **It is adjacent to a room that has damage** — it's on the list. Adjacency is drawn right on the diagram pages; mark every damaged room, then add every room the diagrams show adjoining one. No judgment involved at this tier. The adjacent room goes on so its shared surfaces, openings, and continuous finishes get examined; what (if anything) is owed inside it is a later stage's question.

This baseline is the industry's own standard, so a carrier estimate that doesn't meet it is missing rooms by the carrier's own rules — the strongest kind of scope finding. Check the baseline completely before moving to Tier 2.

**Tier 2 — look for damage and impact beyond the baseline.** Two more cases, requiring judgment:

3. **It might have damage.** The evidence is suggestive but unconfirmed — a stain at the edge of a photo, a drying log naming a room no photo covers, a likely moisture-migration path. Flag the room for inspection rather than dropping it.
4. **It has no damage, but the construction affects it in any way** — crews and materials move through it, it needs protection during the work, demolition dust reaches it, or it loses use while work is underway. These construction-affected rooms are the ones carriers most consistently leave off.

**The chimney is a room on every floor it's on.** A chimney (GSO) appears in the room list as its own room on **each** floor it passes through — e.g., *Chimney — Main Floor*, *Chimney — Second Floor*, *Chimney — Attic* — each entry grouped under that floor's macro-area, never as a feature of whichever room it happens to be photographed from. The same goes for similar vertical elements that span floors (chases, stairwells): one room entry per floor. Add these entries to the independent room list (Method step 3) whenever the diagrams, photos, or any project file show the element exists; each floor's entry then goes through the room test like any other room.

### Non-room categories — the category-inclusion test

A non-room folder (Debris Removal, General Conditions, Dumpster, Permits, Roofing, Detached Structure, Labor Minimums, Content Manipulation, Mitigation/Drying, Temporary Repairs, etc.) belongs on the estimate when **the work already scoped, or the loss type, requires it.** Don't ask "is there a damaged space" — ask "does the body of work imply this category":

1. **The scoped work generates it.** Tear-out/demolition line items → a **Debris Removal** / **Dumpster / Hauling** folder is required; the debris has to leave the site. Replacement of finishes → disposal of the old material.
2. **The job's size or nature requires it.** Any non-trivial interior or multi-trade job → **General Conditions** (and, downstream, supervision/O&P). Permit-triggering work → a **Permits & Fees** folder. Contents in the work zone → **Content Manipulation / Pack-out**.
3. **The peril requires it.** Water loss → **Mitigation / Drying** and antimicrobial/cleaning categories (IICRC). Fire/smoke → **Cleaning / Deodorization**. These are confirmed in Stage 5, but the *folder* belongs on the scope now.
4. **A project file or the carrier's own diagram names it.** A detached garage on the sketch, an outbuilding in a photo, a permit in the documents → the corresponding folder.

A category that any of these pulls in but the carrier didn't open is a **Missing-from-carrier** finding, exactly like a missing room. The step-2 self-check is the proactive form of this test; this test is also applied to anything the project files or the cross-walk surface.

Applying this rule — to rooms and to categories — is Stage 1's job; pricing what goes *inside* an included folder belongs to Stages 2+.

## Checklist 2 cues — starting points, not exhaustive

These are scoping cues from Checklist 2 (a starting-point guide). Apply additional industry-standard scoping considerations as warranted by the specific project.

- Structural integrity (foundations, walkways, patios, roof pitch / multiple roofing layers)
- Material degradation (curled/loose shingles, algae, granule loss, flashing, pipe boots, gutters)
- Interior systems (hidden moisture, mold, electrical compromised by water/heat, water heater strapping in seismic zones)
- Testing protocols (10×10 hail test squares, moisture meters, ITEL samples on carpet/vinyl)

These are scoping cues, not line items. If you spot evidence of structural cracking or hidden moisture in the photos, the *room* containing that evidence belongs on the scope list — the actual line items come in Stage 2.

## Stay in this stage's lane

Per §2.10 of the protocols, this stage decides only **which folders — rooms and non-room categories — belong on the estimate**. It builds the folder cross-walk — nothing about what goes *inside* a folder.

The folder/line-item line is what keeps this stage in its lane. Stage 1 decides a **folder** belongs (e.g., a *Debris Removal* category, a *Permits & Fees* category, a *Detached Garage*); it does **not** scope or price the line items inside that folder — that is the owning stage's job (debris quantities/tonnage in Stage 9, permit fees in Stage 12, exterior-structure line items in Stage 6, and so on). Flagging a missing *folder* is in-lane scope work; flagging a missing *line item within a folder* is not.

So: while doing this stage you will see things that belong to other stages — a line item that looks underpriced or mis-quantified (Stage 2), a missing Material/Equipment/Labor component (Stage 3), a missing companion item like subfloor or a transition strip (Stage 4), peril-specific items (Stage 5), exterior-structure line items (Stage 6), or specific code upgrades (Stage 7), the dumpster *tonnage* (Stage 9), the *amount* of a permit fee (Stage 12). Do not mention those, do not ask whether to flag them, and do not record them anywhere. Drop them; the owning stage re-examines the whole estimate and will catch them. Noticing an out-of-stage **line item** and asking whether to flag it is the §2.10 violation to avoid — but identifying that an entire **folder/category is missing** is exactly what this stage is for.

## Output

This is a substantive analytical response — produce the four-section format from §3 of the protocols (Analysis / Recommendations / Challenge to AI's Analysis / Challenge to User's Thinking) plus the verified/unverified facts section.

The **Recommendations** section must contain:

- The carrier's complete folder list (every room **and** every non-room category), in carrier order, unchanged
- Any folders you believe are missing — missing rooms **and** missing categories (including everything the step-2 self-check surfaced) — each with cited evidence or the implication that justifies it
- Any naming discrepancies flagged for user awareness (carrier's name is retained either way)

## Stage output file & artifact

Per §2.9 of the protocols, this stage records its work product as a visible file: `outputs/stage-outputs/01-scope.md`. It contains the four-section findings above plus the scope cross-walk **organized by macro-area** (one section per macro-area, each listing the carrier rooms, the independent room list, and the match status for that area). Build it incrementally — append each macro-area's section as you confirm that area at its per-area gate — and finalize it at the stage-end gate.

Also record this stage's findings in the consolidated audit-findings artifact (base id `claim-audit-findings`, suffixed with this project's slug per §2.3 of the protocols, §2.9): add/refresh the Scope Audit entry with one `group` per macro-area (columns: Carrier list / Independent list / Match status / Evidence), update the `updated` stamp, and call `update_artifact` after each macro-area. If this project doesn't have the artifact yet — no `outputs/audit-findings-artifact.html` backing file (setup was skipped; never judge by the artifact list or another project's artifacts) — create this project's own from `forensic-claim-audit/assets/audit-findings-artifact.html` first. The markdown is canonical.

This is separate from updating the macro-area map (below) and from the suggestion list — the cross-walk file is *what the scope audit found*; the map is the divided list of areas the rest of the audit walks; the suggestion list holds the accepted scope additions.

## Recording suggestions in the suggestion list

For every suggestion this stage produces (missing rooms, missing non-room categories from the step-2 self-check or the cross-walk, naming flags, scope additions), walk each one through the per-suggestion confirmation flow defined in §2.3 of the protocols: call `AskUserQuestion` per suggestion with options Accept / Reject / Modify / Ask a question. Only Accepted entries get appended to `outputs/audit-suggestion-list.md` (disposition `Agreed`). Refresh the live artifact after each append.

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

## Photo map & coverage check

This step runs on **every claim** — with or without a walkthrough video — after the last macro-area's cross-walk is confirmed and **before the stage-end verification gate**. It does two jobs at once: ties every photo to a room so later stages can cite photos by room, and verifies the photos don't show more property than the room list covers. It sits before the gate precisely because the second job can produce scope findings.

Run it as a loop (§2.15, loop 6): a photo or frame that maps to no listed room is a signal the room list is incomplete — resolve it as a scope finding, add the room, and re-check coverage. Repeat until every photo and frame maps to a confirmed room or is marked Unidentifiable.

1. Use `Read` on each photo — but photos already examined during Method step 3 are still in context; don't re-read those, only `Read` photos not yet looked at. Use capture timestamps where available — people photograph room by room, so time order approximates the walk path — together with the cross-walked room list and the diagram adjacencies.
2. Build the full mapping in one pass: a table of photo filename → room → one-line note of what the photo shows.
3. Every photo must land in exactly one of three places:
   - **A room on the list** — the normal case.
   - **Unidentifiable** — too tight, dark, or ambiguous to place. Goes under an **Unidentifiable** heading; never guess a room (§1).
   - **Shows a space that is not on the room list** — a room, area, or structure visible in the photo that nothing on the cross-walked list accounts for. This is a **scope finding, not a mapping note**: run it through the folder-inclusion rule and the per-suggestion flow (§2.3) like any other missing-room finding, citing the photo. If accepted, add the room to the list and map the photo to it.
4. Show the proposed mapping and ask the user to confirm or correct it. One confirmation for the whole table — the scope findings from step 3 have already gone through their own per-suggestion calls; the mapping itself is working state, not a suggestion.
5. After the stage-end gate is confirmed, write the confirmed table to `outputs/photo-map.md` with `**Last updated:** after Stage 1 (Scope) confirmation` (stage context, never a clock time).

Walkthrough-video frames don't need rows in this map — they're already timestamped and ordered in `video-intake/<video name>/`, and Method step 3 already walked them for unlisted rooms; reference that folder once in the map's header instead. If new photos land in the project folder mid-audit, any stage may propose additions to the map the same way: propose, user confirms, append.

Later stages cite mapped photos as *"PHOTO-2026-02-28-12-37-10-15.jpg (Master Bath, per the photo map)"*.

## Verification gate

The photo map & coverage check (above) must be done — every photo mapped, unidentifiable, or resolved as a scope finding — before this gate is asked. When you believe this stage is complete, ask:

> "Do you believe the Scope Audit is complete? If not, please direct me to the incomplete item(s)."

After the user confirms, update the macro-area map (above) and write the confirmed photo map to `outputs/photo-map.md` (above), then route per §4 of the protocols (which honors the audit mode in `outputs/audit-progress.md`). The next stage is **Line Item Audit** (skill: `claim-line-item-audit`).

In single-session mode, §4 prompts *"Ready for Line Item Audit."* and waits for "begin line item audit" (or equivalent) before chaining. In multi-session mode, §4 prints the multi-session hand-off and stops here — the user begins the Line Item Audit in a fresh chat in this same Cowork project.

(The gate response is procedural — short and direct, not 4-section. See §3 of the protocols.) Do not proceed to Stage 2 in this chat until §4's routing has fired and the user has either confirmed (single-session) or started a fresh chat (multi-session).

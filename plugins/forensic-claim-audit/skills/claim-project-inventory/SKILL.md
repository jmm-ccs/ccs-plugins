---
name: claim-project-inventory
description: On-demand utility for the CCS forensic claim audit. Walks the project workspace, categorizes every file by audit-relevance (carrier estimate, photos, sketches/floor plans, contractor scope of work, measurement reports, drying logs, invoices, permits/code documents, correspondence, contracts, other), flags expected-but-missing categories, and writes both a markdown inventory and an XLSX inventory to the outputs folder. Trigger when the user says "what files do I have," "inventory the project," "list project documents," "what's in the workspace," "what am I missing," "do I have everything to start the audit," or wants a pre-audit sanity check on inputs. Independent of any audit stage.
---

# Claim Project Inventory

Goal: produce a categorized inventory of every file in the project workspace, flag any audit-expected category that has no files, and deliver both a markdown summary and an XLSX file in `outputs/`. This is the pre-flight check the user runs before invoking `forensic-claim-audit` or `claim-audit-setup` — it confirms the workspace has what the audit needs.

This skill is independent of the 13 audit stages. It does not produce audit findings, suggestions, or recommendations — only an inventory of the files the audit will operate on.

## Step 0 — Read the protocols

Use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read the entire file end-to-end before doing anything else. Pay particular attention to:

- §2.3 — Carrier Estimate Protocol (lists the inputs each audit stage expects)
- §1 — Output Integrity (the inventory must be factually accurate; if a file's purpose isn't determinable, leave it as *Uncategorized* rather than guess)
- §9 — How to talk to the user (the missing-items output goes to the user; descriptions, not labels)

Do this every time this skill is invoked, regardless of whether the protocols were loaded earlier. The canonical expected-items list for the missing-flag check is this skill's own Step 4 table — no other file needs to be read for it.

## Precondition (refuse until met)

Per §2.14 of the protocols. This is the **pre-audit pre-flight**, so it deliberately does **not** require an active claim project — it is exactly what the user runs *before* `/claim-audit-setup` to see whether the workspace has what the audit needs. Its only precondition is the workspace itself: if it holds no files at all, say so plainly and stop (Step 1's file count surfaces this). Re-check on every attempt. (Writing its inventory files into `outputs/` does not make the project "set up" — only setup creates the `outputs/audit-progress.md` that the §2.14 active-project gate looks for.)

## Step 1 — Walk the workspace

The project folder is the Cowork workspace, already attached. Use `bash` with `find` (or equivalent) to list every file in the workspace recursively. For each file, capture:

- **Path** — relative path from the workspace root
- **Filename** — leaf name
- **Extension** — file extension, lowercased
- **Size** — in bytes (for sanity-checking; e.g., a 0-byte PDF is suspicious)
- **Last modified date** — the file's mtime, date only (no clock time). This is external file metadata, useful for spotting stale folders.

Skip:

- The `outputs/` sub-folder (audit-generated content — not input documentation)
- `.DS_Store`, `Thumbs.db`, `.git/`, `__pycache__/`, and other OS/tool detritus
- Hidden files starting with `.` unless the user explicitly says to include them

Show the count of files found in chat before proceeding.

## Step 2 — Categorize each file

For each file, assign exactly one category based on filename and extension. The category names below are the **plain-English labels** used in the inventory output and any user-facing message — do not invent hyphenated/snake-case IDs (e.g., write *"Carrier estimate"*, never `carrier-estimate`). Categories are listed in priority order; assign the first match.

| Category | Heuristics |
|---|---|
| Video-derived frames and transcripts | Any file inside a `video-intake/` folder (extracted walkthrough frames, `transcript.md`, `intake-manifest.md`) — path match beats every other heuristic |
| Sample supplement | Any filename containing `supplement`. The canonical sample going forward is CCS's own marked-up-estimate format — the file **`sample supplement v1`** — which supersedes past-claim examples (e.g., the older "Chattanooga Lake Supplement"). The current claim's supplement doesn't exist yet, so the sample is the format reference. Ranked above Carrier estimate so a supplement named with "estimate" doesn't mis-match |
| Carrier estimate | Filenames containing `xactimate`, `estimate`, `carrier`, `adjuster`, `xc4`/`.esx`/`xceif` extensions; PDFs with `estimate` in the name |
| CCS forensic checklists | Filenames containing `checklist`, `forensic claim analysis`, `field scoping` |
| CCS marketing sheet | Filenames containing `marketing`, `1-sheet`, `one-sheet`, `CCS sheet` |
| Photos | Image extensions (`.jpg`, `.jpeg`, `.png`, `.heic`, `.tif`, `.tiff`, `.webp`); also iPhone photo patterns (`IMG_*`, `PHOTO-*`, etc.) |
| Videos | Video extensions (`.mov`, `.mp4`, `.m4v`, `.avi`, `.mkv`); walk-through videos |
| Sketches and floor plans | Filenames containing `sketch`, `floor plan`, `floorplan`, `cubicasa`; CAD extensions (`.dwg`, `.dxf`) |
| Measurement reports | Filenames containing `eagleview`, `hover`, `roof report`, `measurement`, `aerial`, `drone`, `EV-`, `HV-` |
| Contractor scope of work | Filenames containing `scope`, `SOW`, `contractor scope`, `proposal`, `bid` |
| Drying logs | Filenames containing `drying`, `moisture`, `psychrometric`, `MICA`, `iicrc log`, `daily log` |
| Invoices and receipts | Filenames containing `invoice`, `receipt`, `bill`, `payment`, `purchase order`, `PO-` |
| Permits and code documents | Filenames containing `permit`, `code`, `ordinance`, `inspection report` |
| Correspondence | Email exports, letters from carrier/homeowner/contractor; filenames containing `email`, `letter`, `correspondence`, `denial`, `coverage` |
| Contracts | Filenames containing `contract`, `AOB` (assignment of benefits), `agreement` |
| Uncategorized | Anything that doesn't match above. Do NOT guess — leave as *Uncategorized* and let the user re-categorize. |

**Important** — per §1 of the protocols, do not guess at a category if the filename is ambiguous. If two heuristics match, pick the higher-priority row in the table above. If none match, the category is *Uncategorized*.

For each file, also note any **integrity flag**:

- `zero-bytes` if size is 0
- `suspiciously-small` if a file in a category that's normally substantial (e.g., a *Carrier estimate* PDF under 50 KB) is unusually small
- `duplicate-filename` if two files in different folders share the exact filename
- (otherwise blank)

## Step 3 — Write `outputs/project-inventory.md`

Create `outputs/` if it doesn't exist (per §2.3 / §2.6). Then write `outputs/project-inventory.md` with this structure:

```markdown
# Project Inventory — [Workspace Folder Name]

Total files inventoried: [N]
Categories present: [count of distinct categories]

## Summary by category

| Category | File count | Notable items |
|---|---|---|
| Carrier estimate | 1 | carrier-estimate-2026.pdf |
| Photos | 87 | (87 image files) |
| ... | ... | ... |

## All files

| Category | Path | Filename | Size (KB) | Last modified | Integrity flag |
|---|---|---|---|---|---|
| Carrier estimate | / | carrier-estimate-2026.pdf | 4203 | 2026-04-15 | |
| Photos | photos/exterior/ | IMG_2845.heic | 4112 | 2026-04-12 | |
| ... | ... | ... | ... | ... | ... |

## Missing items — expected but not found

[Filled in at Step 4]

## Notes

- The `outputs/` folder is excluded from this inventory (audit-generated content).
- Files in the *Uncategorized* category were not auto-categorized because the filename did not match any heuristic. Re-categorize manually if any of them belong to a known category.
```

Sort the "All files" table by **Category**, then by **Path**, then by **Filename**. Use the plain-English category labels from Step 2 — never hyphenated IDs.

**Video-derived frames are summarized, not listed row-by-row.** A processed walkthrough video can produce hundreds of frames; listing each one would drown the table. In the "All files" table, roll each video's `frames/` folder into a single row (Filename: `frames/ (N files)`, Size: the folder total) while `transcript.md` and `intake-manifest.md` keep their own rows. The Summary table counts the actual file totals.

## Step 4 — Flag missing expected items

The audit expects each of the following in the project folder. Each entry below is **a thing the audit was expecting** — when one is missing, the user-facing message should describe that thing concretely (what it is, what it usually looks like, why the audit needs it), not just label it. The user knows forensic claim auditing; they don't know which abstract bucket your classifier put a file in.

| Expected item | Severity | What it is — say it like this when flagging it missing |
|---|---|---|
| Carrier estimate | Required | The insurance carrier's Xactimate estimate (or PDF/ESX/XCEIF export of it). This is the document the audit reviews against. The audit cannot start without it. |
| Project documentation (photos, videos, sketches, or floor plans) | Required (at least one) | Visual record of the loss — phone photos from the site walk, the contractor's walk-through video, a hand sketch, a Cubicasa floor plan, or similar. The audit reads these to confirm scope room-by-room (the carrier estimate's own diagram pages carry the room geometry, but an independent visual record of the damage is still needed). At least one of these is required. |
| Third-party measurement report | Required for roofing / exterior-appurtenance claims | An aerial roof-measurement report from EagleView, HOVER, drone imagery, or equivalent. The audit uses it to cross-check the carrier's roof dimensions, pitch, and exterior-appurtenance quantities against an independent measurement. Required when the loss involves roofing or exterior structures. **Before flagging this missing, `Read` the carrier estimate PDF** — carriers frequently attach the EagleView/HOVER pages inside the estimate itself. If measurement pages are embedded there, it is not missing: note "measurement report included in the carrier estimate (pages N–M)" in the inventory instead. |
| Contractor scope of work | Strongly recommended | The contractor's own SOW, proposal, or bid for the repair. The audit cross-walks it against the carrier's estimate to surface scope gaps. |
| Sample supplement | Recommended | The canonical sample is **`sample supplement v1`** — CCS's own finished marked-up-estimate format (cover letter + in-line green corrections), i.e. what the standard deliverable now looks like. It is the format reference for the marked-up copy of the carrier's estimate, and the markup tool prepends a cover letter templatized from this sample. (Supersedes the older Chattanooga past-claim sample, and the legacy Word `claim-supplement-package`, which is retained only for projects that specifically want that legacy document.) |
| Drying log | Required for water-loss claims | An IICRC S500 drying log — daily atmospheric readings (temperature, relative humidity, GPP), moisture-meter readings, equipment-on-site dates. Required for water losses so Stage 5 (Type-of-Loss Audit, water branch) can verify mitigation scope. Skip this row entirely if this is not a water-loss claim. |
| Invoices / receipts | Recommended | Receipts or invoices for items already incurred — debris hauling, emergency board-up, temporary fencing, contents handling, etc. Useful for documenting actual costs. |
| Permits and code documents | Recommended | Pulled permits, inspection reports, jurisdiction code-adoption notices, anything establishing what the locality requires. Useful when the scope likely triggers code upgrades (Stage 7). |
| Correspondence | Recommended | Letters or emails between carrier, homeowner, and contractor — denial letters, coverage decisions, scope agreements, demand letters. Useful for establishing timeline and prior positions. |

**Not flagged as missing — codified into the plugin.** The following categories are still recognized at Step 2 (so files of those types get categorized correctly if they happen to be in the workspace), but their absence is **never** flagged as missing because the plugin already encodes the relevant content into its skills:

- **CCS forensic checklists** — Checklist 2 (Field Scoping) cues are inline in `claim-scope-audit`; protocol material from the checklists is in `claim-audit-protocols`. The user is welcome to drop an updated checklist PDF in the workspace, but they are not required to.
- **CCS marketing sheet** — the CCS objective ("Getting Contractors the Funds to Rebuild Properly Without Insurance Fights or Homeowner Negotiation") that drives the Sanity Audit is already baked into `claim-audit-finalizer` Phase 1 Goal 2.

For each expected item the inventory could not find a file for, add a row to the **Missing items** section of `project-inventory.md`:

```markdown
## Missing items — expected but not found

| Item | Severity | What it is |
|---|---|---|
| Carrier estimate | Required | The insurance carrier's Xactimate estimate (or PDF/ESX/XCEIF export of it). This is the document the audit reviews against. The audit cannot start without it. |
| Drying log | Required for water-loss claims | An IICRC S500 drying log — daily atmospheric readings (temperature, relative humidity, GPP), moisture-meter readings, equipment-on-site dates. Required for water losses so Stage 5 can verify mitigation scope. Skip if this is not a water-loss claim. |
| ... | ... | ... |
```

Severity column values: `Required`, `Required for water-loss claims`, `Required for roofing / exterior-appurtenance claims`, `Strongly recommended`, `Recommended`. No other values.

Use the **What it is** description from the Step 4 table above as the description in this row. Never substitute a category-name label for the description — the description IS the point.

If every expected item is present, write a single line in place of the table:

```
All expected items are present. Workspace is ready for the audit.
```

Do **not** flag items the user explicitly said don't apply (e.g., a condo unit with no appurtenances). If the user has not given that signal, flag the gap — they can dismiss it.

**Unprocessed walkthrough videos.** Separately from the missing-items table: if any file in the *Videos* category has no matching `video-intake/<video filename without extension>/intake-manifest.md`, add a short note after the Missing items section (and a line in the Step 6 closing message) saying the walkthrough video hasn't been turned into readable evidence yet — the audit reads extracted stills and the narration transcript, not the raw video — and that sending `/claim-video-intake` will do it. This is a not-yet-processed input, not a missing one, so it never goes in the missing-items table.

## Step 5 — Write `outputs/project-inventory.xlsx`

Use the `xlsx` skill to convert the file table from `project-inventory.md` into a spreadsheet at `outputs/project-inventory.xlsx`. Three sheets:

1. **Summary** — the "Summary by category" table from Step 3
2. **Files** — the "All files" table from Step 3, sorted the same way
3. **Missing** — the "Missing items" table from Step 4 (or the single "all expected items are present" line if none missing)

Freeze the header row in each sheet. Apply column widths to fit content. Sort the Files sheet by Category → Path → Filename.

## Step 6 — Hand the files to the user and confirm

**Hand the user the two inventory files** (the file-sharing / present-files step) so they receive `outputs/project-inventory.md` and `outputs/project-inventory.xlsx` directly. The chat message is the user's first look at what's missing — they should be able to act on it without opening either file.

The closing message includes:

- The total file count and the number of categories present.
- That the two inventory files have been handed to them.
- If every expected item is present: a single line saying the workspace has everything the audit needs, ready for Stage 1.
- If anything's missing: a header like "Things the audit was expecting and didn't find:" followed by one bullet per missing item. Each bullet uses the **What it is** description from Step 4 — the description, not the label. End with a one-line note that the user should add what applies and skip what doesn't (e.g., the drying-log line is only relevant if this is a water-loss claim).

Do not start any audit stage from this skill.

## What this skill does NOT do

- Does not run any audit stage.
- Does not interpret or analyze file contents (it categorizes by filename and extension) — with one deliberate exception: the Step 4 measurement-report check looks inside the carrier estimate PDF before flagging the report missing, because carriers often embed the EagleView/HOVER pages there.
- Does not download or pull files from any external service.
- Does not modify the suggestion list, audit progress, or any other audit state.

## Related skills

- `forensic-claim-audit` — invoke after this inventory looks complete to start the single-session audit.
- `claim-audit-setup` — invoke after this inventory looks complete to start the multi-session audit.
- `claim-audit-protocols` — the protocols this skill operates against. Read at Step 0.

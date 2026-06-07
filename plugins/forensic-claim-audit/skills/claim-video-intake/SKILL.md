---
name: claim-video-intake
description: On-demand utility for the CCS forensic claim audit. Converts walkthrough videos in the project folder into audit-readable evidence — examines every frame of the video and saves each visually distinct one as a timestamped still, transcribes the narration into a timestamped transcript, and writes a per-video manifest. Trigger when the user says "process the video," "pull frames from the walkthrough," "transcribe the video," "get the video ready for the audit," or whenever the project folder contains walkthrough videos that haven't been processed yet. Run before Stage 1 so the scope and continuity audits can cite frames and narration as evidence. Independent of any audit stage.
---

# Claim Video Intake (On-Demand Utility)

Goal: turn each walkthrough video in the project folder into evidence the audit can actually read and cite — a set of timestamped still frames, a timestamped transcript of the narration, and a manifest tying them together.

The audit stages read files with the `Read` tool, which handles images and PDFs but not video. This skill is the bridge: after it runs, the walkthrough video exists as individually citable frames and transcript lines, and every audit stage treats them exactly like photos and project documents.

This skill produces no audit findings, no suggestions, and no recommendations. It only prepares inputs. The original video file is never modified, moved, or deleted.

## Step 0 — Read the protocols

Use the `Read` tool on `../claim-audit-protocols/SKILL.md` and read the entire file end-to-end before doing anything else. Do this every time this skill is invoked. Pay particular attention to §1.4 (every count and number reported to the user must have provenance — frame counts and durations come from the actual ffmpeg/Whisper run, never estimated) and §9 (how to talk to the user — outcomes, not process narration).

## The every-frame rule

Every frame of the video gets decoded and examined — no sampling, no fixed-interval skipping. What gets *saved* is every visually distinct frame: consecutive near-duplicate frames (the camera holding still on the same view) are dropped, because they add file count without adding evidence. Nothing visible in the video is lost; the audit just isn't handed thousands of copies of the same view. This is implemented with ffmpeg's `mpdecimate` filter, which decodes the full frame stream and emits only frames that differ materially from the one before.

## Output layout

For each video, everything lands in a `video-intake/` folder at the project-folder root (NOT in `outputs/` — these are audit *inputs*, derived from project documentation, and the project inventory must see them as such):

```
video-intake/
  <video filename without extension>/
    frames/
      frame-00001_00m00s.jpg
      frame-00002_00m03s.jpg
      ...
    transcript.md
    intake-manifest.md
```

Frame filenames carry a sequential index (preserves walk order) and the frame's timestamp in the video (rounded to the nearest second; the manifest holds the exact value). Both parts matter: the index is what makes adjacency readable (frame N+1 is what the camera saw immediately after frame N), and the timestamp is what links a frame to the transcript.

## Step 1 — Find unprocessed videos

Use `bash` to list video files in the project folder (extensions: `.mov`, `.mp4`, `.m4v`, `.avi`, `.mkv`, case-insensitive), excluding anything already inside `video-intake/` or `outputs/`. A video is **unprocessed** if there is no `video-intake/<its basename>/intake-manifest.md`.

- If every video is already processed, say so and stop — re-processing is wasteful and renumbers frames other documents may already cite. Re-process a video only if the user explicitly asks (e.g., the video file was replaced); in that case delete that video's `video-intake/<basename>/` folder first so stale frames don't linger.
- If there are no videos at all, say so plainly and stop.
- Otherwise, list the unprocessed videos found (filename, size, and duration via `ffprobe`) and proceed.

## Step 2 — Extract the distinct frames

For each unprocessed video, via `bash`:

1. Create `video-intake/<basename>/frames/`.
2. Run ffmpeg with `mpdecimate` + `showinfo`, capturing the filter log:

   ```
   ffmpeg -i "<video>" -vf "mpdecimate,showinfo" -vsync vfr -qscale:v 2 \
     "video-intake/<basename>/frames/tmp-%05d.jpg" 2> "video-intake/<basename>/showinfo.log"
   ```

3. Parse the `pts_time:` values out of `showinfo.log` with Python — one per emitted frame, in order — and rename each `tmp-%05d.jpg` to `frame-%05d_MMmSSs.jpg` using its timestamp. Keep the exact `pts_time` for the manifest. Delete `showinfo.log` when done.
4. Record, from the actual run output: total frames decoded/examined, distinct frames saved, and video duration. These numbers are copied from the tool output (§1.4) — never estimate them.

**Long videos.** The `bash` tool has a per-call timeout, and a long walkthrough can exceed it. If the video is more than a couple of minutes, run the ffmpeg command in the background (`nohup ... > log 2>&1 &`) and poll for completion (process gone and frame count stable) across subsequent `bash` calls. The same applies to transcription in Step 3.

**Sanity check.** After extraction, `Read` two or three frames spread across the video (first, middle, last). If they're black, corrupt, or unreadable, stop and tell the user what you found before continuing.

## Step 3 — Transcribe the narration

For each video:

1. Check for an audio stream with `ffprobe`. If the video has **no audio track**, skip transcription, note "no audio track — no transcript produced" in the manifest, and move on. Do not fail.
2. Extract the audio: `ffmpeg -i "<video>" -vn -ac 1 -ar 16000 audio.wav`.
3. Transcribe with Whisper (install if needed: `pip install --break-system-packages openai-whisper`; the `base` model is the default — step up to `small` if the result is visibly garbled). Whisper auto-detects the spoken language; keep the transcript in whatever language was spoken — do not translate it.
4. Write `video-intake/<basename>/transcript.md`: a title line naming the source video, then one line per segment in the form `**[MM:SS]** <text>`.
5. Delete the intermediate `audio.wav`.

The transcript timestamps and the frame timestamps share the same clock, so any narration line can be paired with the frames around it.

## Step 4 — Write the manifest

Write `video-intake/<basename>/intake-manifest.md`:

```markdown
# Video Intake — <video filename>

Source video: <relative path, exactly as found>
Duration: <H:MM:SS, from ffprobe>
Frames examined: <total decoded, from the run>
Distinct frames saved: <count, from the run>
Transcript: transcript.md  (or: no audio track — no transcript produced)

## Frame index

| Frame file | Timestamp |
|---|---|
| frame-00001_00m00s.jpg | 0.000 s |
| frame-00002_00m03s.jpg | 3.337 s |
| ... | ... |
```

The manifest is the provenance record for the whole intake (§1.4): every count in it comes from the actual run.

## Step 5 — Confirm to the user

One short message per the §9 voice — outcomes, not process. For each video: its name, how many distinct stills came out of it, whether there's a transcript, and that the audit will read and cite these directly. If this ran before Stage 1, close with the next step (e.g., "Ready to start the Scope Audit when you are"). No ffmpeg/Whisper narration, no command output dumps.

## How the audit cites video evidence

(For the audit stages reading this; the citation rules of §1.5 apply unchanged.)

- A **frame** is cited like a photo, by its exact filename: *"frame-00214_04m32s.jpg — the hallway oak floor running through the doorway into the living room with no threshold."*
- A **narration line** is cited by transcript + timestamp, quoted: *"transcript.md [04:31] — 'this same oak runs all the way into the living room.'"*
- The strongest form pairs the two: the frame shows it, the narration says it, and the shared timestamp ties them together.
- **Adjacency/sequence** evidence (continuity audit) cites a frame *range*: consecutive frames showing the camera traveling from one room into the next document that the rooms connect.

## What this skill does NOT do

- Does not run any audit stage, produce findings, or add suggestions to the suggestion list.
- Does not analyze damage — it prepares evidence; the stages do the analysis.
- Does not modify, move, or delete the original video files.
- Does not translate the transcript (bilingual output is governed by §2.11 and applies to suggestions, not source evidence).

## Related skills

- `claim-project-inventory` — categorizes the extracted frames and transcripts, and flags any video that hasn't been through intake yet.
- `claim-scope-audit` — builds the independent room list from these frames and the transcript.
- `claim-continuity-audit` — uses frame sequences as adjacency and line-of-sight evidence.
- `forensic-claim-audit` — the orchestrator runs this intake before Stage 1 when unprocessed videos are present.

#!/usr/bin/env python3
"""
build_annotated_estimate.py — CCS forensic claim audit.

Produces the audit's end deliverable: a marked-up COPY of the carrier's estimate.
The full carrier estimate is reproduced page-for-page (black, untouched), and each
suggestion-list entry is drawn ON TOP in green:

  * a green box around the exact carrier line the suggestion attaches to,
  * a short green note beneath that line ("> CCS #N [Type/Disp]: ..."),
  * a green justification appendix at the end with the full
    "[x] changed from [old] to [new] for [reason]" plus disposition / type / label.

This is a deterministic tool. The claim-pdf-annotator skill calls it; it never
re-derives the PDF logic by hand. Carrier content is reproduced faithfully — green
is the only thing added.

Usage:
    python3 build_annotated_estimate.py <carrier.pdf> <suggestion-list.md> <out.pdf>

Requires: PyMuPDF (fitz).
"""

import sys
import os
import re
import textwrap

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("ERROR: PyMuPDF not installed. Run: pip install pymupdf --break-system-packages")

GREEN = (0.0, 0.55, 0.0)
WHITE = (1.0, 1.0, 1.0)
PAGE_W, PAGE_H = 612.0, 792.0
LEFT_X = 34.0          # left margin for boxes/notes
RIGHT_X = 578.0        # right margin
LEFT_COL_MAX = 160.0   # item-number tokens live left of this x

# ---- transliteration: the base-14 PDF fonts can't render these; map to ASCII ----
TRANS = {
    "≈": "~", "→": "->", "←": "<-", "↔": "<->",
    "—": "-", "–": "-", "−": "-", "•": "-",
    "…": "...", "×": "x", "÷": "/", "≥": ">=", "≤": "<=",
    "°": " deg", "‘": "'", "’": "'", "“": '"', "”": '"',
    " ": " ", "½": "1/2", "¼": "1/4", "¾": "3/4",
    "′": "'", "″": '"', "²": "2", "³": "3",
}
def tr(s):
    if s is None:
        return ""
    for k, v in TRANS.items():
        s = s.replace(k, v)
    # drop anything else outside printable Latin-1 so nothing renders as "?"
    return "".join(ch if 32 <= ord(ch) <= 255 else "?" for ch in s)


# --------------------------------------------------------------------------- #
# 1. Parse the suggestion-list markdown table into a list of dict rows.
# --------------------------------------------------------------------------- #
def parse_suggestions(md_path):
    rows = []
    with open(md_path, encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f]
    header = None
    for ln in lines:
        if not ln.strip().startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if header is None:
            header = [c.lower() for c in cells]
            continue
        if set("".join(cells)) <= set("-: "):   # the |---|---| separator row
            continue
        if len(cells) < len(header):
            cells += [""] * (len(header) - len(cells))
        rows.append(dict(zip(header, cells)))
    return header, rows


def get(row, *names):
    for n in names:
        for k in row:
            if k == n or k.startswith(n):
                return row[k]
    return ""


# --------------------------------------------------------------------------- #
# 2. Index every carrier line item: item number -> (page_index, rect of the line)
#    Uses left-column word tokens that look like "194." so dollar amounts
#    such as "194.64" (in the right-hand columns) are never matched.
# --------------------------------------------------------------------------- #
ITEMNUM_RE = re.compile(r"^(\d{1,4})\.$")

def index_items(doc):
    index = {}
    for pno in range(doc.page_count):
        for (x0, y0, x1, y1, word, *_rest) in doc[pno].get_text("words"):
            m = ITEMNUM_RE.match(word)
            if m and x0 < LEFT_COL_MAX:
                num = int(m.group(1))
                if num not in index:          # first (earliest) occurrence wins
                    index[num] = (pno, fitz.Rect(x0, y0, x1, y1))
    return index


# --------------------------------------------------------------------------- #
# 3. Helpers to extract the carrier item number(s) referenced by a suggestion.
# --------------------------------------------------------------------------- #
ITEM_REF_RE = re.compile(r"\bItems?\s+(\d{1,4})", re.I)

def primary_item(row):
    cl = get(row, "carrier line")
    m = ITEM_REF_RE.search(cl)
    return int(m.group(1)) if m else None


def short_summary(row, limit=170):
    pc = tr(get(row, "proposed change")).strip()
    if len(pc) > limit:
        pc = pc[:limit].rstrip() + "..."
    return pc


# --------------------------------------------------------------------------- #
# 4. Draw a green note box (white fill so green text stays legible over the
#    carrier's black text), returning the height used.
# --------------------------------------------------------------------------- #
def draw_note(page, x0, y_top, text, fontsize=7.0, pad=2.5):
    """White-filled green-bordered note; insert_textbox wraps to width, we size
    height from the measured text length (generously) and grow if it still
    overflows. Returns the box height used."""
    text = tr(text)
    line_h = fontsize + 2.0
    usable = RIGHT_X - x0 - 2 * pad
    tw = fitz.get_text_length(text, fontname="helv", fontsize=fontsize)
    nlines = max(1, int(tw / usable) + 2)
    box_h = line_h * nlines + 2 * pad
    for _ in range(5):
        box_h = line_h * nlines + 2 * pad
        rect = fitz.Rect(x0, y_top, RIGHT_X, y_top + box_h)
        page.draw_rect(rect, color=GREEN, fill=WHITE, width=0.8)
        rc = page.insert_textbox(
            fitz.Rect(x0 + pad, y_top + pad, RIGHT_X - pad, y_top + box_h - pad),
            text, fontname="helv", fontsize=fontsize, color=GREEN, align=0,
        )
        if rc >= 0:
            break
        nlines += 1
    return box_h


# --------------------------------------------------------------------------- #
# 5. Main build.
# --------------------------------------------------------------------------- #
def _safe_save(doc, out_pdf):
    """Save to out_pdf. The project folder may block overwriting an existing file
    (mounted-folder unlink restriction); if so, fall back to a versioned name so the
    tool never hard-fails. Returns the path actually written."""
    target = out_pdf
    if os.path.exists(target):
        try:
            os.remove(target)
        except OSError:
            root, ext = os.path.splitext(out_pdf)
            n = 2
            while os.path.exists("%s (%d)%s" % (root, n, ext)):
                n += 1
            target = "%s (%d)%s" % (root, n, ext)
    doc.save(target, garbage=3, deflate=True)
    return target


def build(carrier_pdf, suggestion_md, out_pdf):
    header, rows = parse_suggestions(suggestion_md)
    doc = fitz.open(carrier_pdf)
    index = index_items(doc)

    applied, unlocated = [], []
    # track how far down each page we've already drawn a note, to stack cleanly
    page_cursor = {}

    for row in rows:
        num = get(row, "#")
        stype = get(row, "suggestion type")
        disp = get(row, "disposition")
        label = get(row, "label")
        item = primary_item(row)

        if item is not None and item in index:
            pno, line_rect = index[item]
            page = doc[pno]
            # green box around the whole carrier line
            box = fitz.Rect(LEFT_X, line_rect.y0 - 2, RIGHT_X, line_rect.y1 + 2)
            page.draw_rect(box, color=GREEN, width=1.1)
            # note goes below the line (or below the last note already on this page band)
            y_top = max(line_rect.y1 + 3, page_cursor.get((pno, round(line_rect.y1)), 0))
            tag = "/".join([t for t in (stype, label if label and label != "—" else "", disp) if t])
            note = "> CCS #%s [%s]: %s" % (num, tr(tag), short_summary(row))
            h = draw_note(page, LEFT_X, y_top, note)
            page_cursor[(pno, round(line_rect.y1))] = y_top + h + 1
            applied.append((num, pno + 1, item))
        else:
            unlocated.append((num, stype, tr(get(row, "carrier line"))[:90]))

    # ----- justification appendix (full detail, grouped by carrier page) ----- #
    def page_key(row):
        m = re.search(r"p+\.?\s*(\d{1,3})", get(row, "carrier line"))
        return int(m.group(1)) if m else 999
    ordered = sorted(rows, key=lambda r: (page_key(r), int(get(r, "#") or 0)))

    appx = doc.new_page(width=PAGE_W, height=PAGE_H)
    appx.insert_textbox(fitz.Rect(LEFT_X, 36, RIGHT_X, 60),
                        "CCS Audit — Justification Appendix",
                        fontname="hebo", fontsize=13, color=GREEN)
    y = 70.0
    for row in ordered:
        num = get(row, "#"); stype = get(row, "suggestion type")
        disp = get(row, "disposition"); label = get(row, "label")
        cl = tr(get(row, "carrier line"))
        pc = tr(get(row, "proposed change"))
        prov = tr(get(row, "number provenance"))
        ev = tr(get(row, "supporting evidence"))
        head = "CCS #%s  [%s]  %s  Label: %s  (%s)" % (
            num, stype, disp, (label or "-"), tr(get(row, "stage of origin")))
        body = "Carrier line: %s\nChange: %s\nProvenance: %s\nWhy / Source: %s" % (
            cl, pc, prov, ev)
        # measure
        bw = RIGHT_X - LEFT_X - 12
        cpl = max(30, int((bw) / (7 * 0.50)))
        nlines = 1
        for para in body.split("\n"):
            nlines += max(1, len(textwrap.wrap(para, cpl)))
        box_h = 16 + (7 + 2) * nlines + 8
        if y + box_h > PAGE_H - 36:
            appx = doc.new_page(width=PAGE_W, height=PAGE_H)
            y = 40.0
        rect = fitz.Rect(LEFT_X, y, RIGHT_X, y + box_h)
        appx.draw_rect(rect, color=GREEN, width=1.0)
        appx.insert_textbox(fitz.Rect(LEFT_X + 6, y + 4, RIGHT_X - 6, y + 18),
                            head, fontname="hebo", fontsize=8, color=GREEN)
        appx.insert_textbox(fitz.Rect(LEFT_X + 6, y + 18, RIGHT_X - 6, y + box_h - 4),
                            body, fontname="helv", fontsize=7, color=GREEN, align=0)
        y += box_h + 6

    saved = _safe_save(doc, out_pdf)
    doc.close()
    return applied, unlocated, saved


def main():
    if len(sys.argv) != 4:
        sys.exit("Usage: build_annotated_estimate.py <carrier.pdf> <suggestions.md> <out.pdf>")
    carrier_pdf, suggestion_md, out_pdf = sys.argv[1:4]
    applied, unlocated, saved = build(carrier_pdf, suggestion_md, out_pdf)
    print("Saved:", saved)
    print("Applied (anchored on a carrier line): %d" % len(applied))
    for num, page, item in applied:
        print("  #%s -> page %d (carrier item %d)" % (num, page, item))
    if unlocated:
        print("Not anchored to a carrier line (appendix only): %d" % len(unlocated))
        for num, stype, cl in unlocated:
            print("  #%s [%s] %s" % (num, stype, cl))


if __name__ == "__main__":
    main()

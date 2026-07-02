#!/usr/bin/env python3
"""
build_spec.py — CCS marked-up-estimate renderer, driven by an encoded FORMAT SPEC.

Same job as build_general.py (reproduce the carrier estimate with CCS's green edits),
but every layout/structure decision now comes from an explicit per-format spec
(XACTIMATE, SYMBILITY) instead of being detected from each carrier PDF. The carrier's
own line CONTENT is still clip-composed (descriptions/numbers stay exact, corrupt-safe);
only the layout is encoded.

Usage:
    python3 build_spec.py <edit-plan.json> <out.pdf> [cover.pdf]
The plan may set "format": "xactimate" | "symbility"; otherwise it is auto-detected.

Requires: PyMuPDF (fitz).
"""
import sys, os, re, math, json
try:
    import fitz
except ImportError:
    sys.exit("ERROR: PyMuPDF not installed. Run: pip install pymupdf --break-system-packages")

# ---- generic constants (format-independent) ----
W, H = 612, 792
pad = 3; gap = 8; usable = (W - 72) - 2 * pad
GREEN_STD = (0.0, 0.55, 0.0)              # CCS standard green (the default for our edits)
TERRACOTTA = (0.808, 0.486, 0.420)        # #CE7C6B — used ONLY when the carrier itself uses green/teal in its lines
GREEN = GREEN_STD                         # reassigned once the carrier is loaded (see below)
WHITE = (1, 1, 1); BLACK = (0, 0, 0)
TRANS = {"≈": "~", "—": "-", "–": "-", "→": "->", "“": '"', "”": '"', "’": "'", "‘": "'", " ": " ", "…": "..."}

def tr(s):
    for k, v in TRANS.items(): s = s.replace(k, v)
    return "".join(c if 32 <= ord(c) <= 255 else "?" for c in s)
def strip_cite(s):
    s = re.sub(r"\bcarrier PDF\b", "", s, flags=re.I)
    s = re.sub(r"\bpp?\.\s*\d+(?:\s*-\s*\d+)?", "", s, flags=re.I)
    s = re.sub(r"Source:\s*[-,;:]+\s*", "Source: ", s)
    s = re.sub(r"\(\s*[-,;:]\s*", "(", s)
    s = re.sub(r"\s+([,;.)])", r"\1", s); s = re.sub(r"\s{2,}", " ", s)
    return s.strip()
def clean(s): return strip_cite(tr(s or ""))

# =====================================================================================
# FORMAT SPECS — everything layout/structure-specific to each estimating platform.
# =====================================================================================
XACTIMATE = {
    "name": "xactimate",
    # vertical geometry
    "content_top": 90.0, "content_bottom": 737.0,       # output content band (header band above)
    "extract_top": 68.0, "extract_bottom": 740.0,       # carrier extraction band (incl. top-of-page folder titles)
    "footer_top": 738.0, "header_band_h": 90.0, "header_clear_below": 67.0,  # keep only State Farm + name/claim line; drop any folder text the template page had in its band
    "line_height": 13.7, "room_gap": 0.15 * 13.7, "totals_gap": 14.0, "folder_gap": 34.0,
    # header rebrand
    "name_box": (228, 33, 384, 55), "company_box": (0, 38, W, 57), "company_align": 1, "company_size": 11,
    "colhdr_mode": "folder",
    # fonts
    "body_font": "tiro", "bold_font": "tibo", "body_size": 9.7,
    # line-item identification
    "item_re": re.compile(r'^\d{1,4}\.$'),              # "186."
    "item_token_fmt": "%d.", "item_lines": 2,           # carrier item = description line + numbers line
    # room / folder
    "room_marker": "Height",                            # a token starting with this => room header block
    "is_totals": (lambda toks: bool(toks) and toks[0] == "Totals:"),
    "totals_room": (lambda toks: _name_before_number(toks[1:]) if (toks and toks[0] == "Totals:") else None),
    # column header (two rows) + continuation marker
    "colhdr_row1": "QUANTITY", "colhdr_row2": "CONDITION",
    "continued_marker": "CONTINUED", "continued_fmt": "CONTINUED - %s", "has_continued": True,
    "continued_detect": (lambda t: t.startswith("CONTINUED")), "continued_style": "centered",
    # add-line layout (qty number right-aligned to qty_right; unit + unit-price columns)
    "columns": {"qty_right": 79, "unit": 82, "unit_price": 139},
    "addline_two_line": True, "desc_max_x": 560,        # render add as desc line + indented numbers line
    # in-place description rewrite geometry (relative to the description baseline ty)
    "desc_whiteout": (54, -9, 405, 3), "desc_x": 58,
    # new-room folder header, styled like a carrier Xactimate room: diagram (left), name + Height + rule under it,
    # then a 2-column value-then-label dimension block
    "folder_header": {
        "style": "room", "row_h": 13.7, "label_font": "tiro", "label_size": 9.7,
        "title_font": "tibo", "title_size": 10, "height_size": 9.6,
        "diagram_x": [47, 144], "diagram_h": 100,
        "title_x_diag": 165, "title_x_nodiag": 37, "height_x": 533, "rule_x1": 576, "rule_x0_nodiag": 37,
        "dim_cols": [243, 443], "dim_top": 20,
        "fields": [["Walls", 0, 0], ["Ceiling", 1, 0], ["Walls & Ceiling", 0, 1],
                   ["Floor", 1, 1], ["Ceil. Perimeter", 0, 2], ["Floor Perimeter", 1, 2]],
    },
}
SYMBILITY = {
    "name": "symbility",
    # vertical geometry: CCS header band (0-86), page furniture (column header + ESTIMATE line)
    # stamped at 86, then content below.
    "content_top": 140.0, "content_bottom": 734.0,
    "extract_top": 142.0, "extract_bottom": 736.0,      # content only (page furniture excluded)
    "footer_top": 736.0, "header_band_h": 86.0,
    "pagefurn_y": (90.0, 142.0),                         # carrier column header + ESTIMATE/Claim/In progress (full)
    "line_height": 11.5, "room_gap": 4.0, "totals_gap": 10.0,
    # header rebrand — white out the whole Safeco block (logo + name + address + fax), CCS at top-left
    "name_box": (5, 28, 272, 86), "company_box": (8, 34, 272, 50), "company_align": 0, "company_size": 13,
    # footer matches the carrier: reproduce its claim# / date band, replace the page number
    "footer_mode": "carrier", "footer_band": (737.0, 753.0),
    "footer_pagenum_box": (270, 737, 348, 753), "footer_pagenum_xy": (278, 747.5), "footer_pagenum_size": 9,
    # fonts (Symbility is sans-serif)
    "body_font": "helv", "bold_font": "hebo", "body_size": 9.9,
    # line items: bare number, variable-height block (numbers on line 1, wrapped desc/notes follow)
    "item_re": re.compile(r'^\d{1,4}$'), "item_token_fmt": "%d", "item_block": "var",
    # room / folder
    "room_marker": "Height",
    "is_totals": (lambda toks: "Subtotal" in toks and "-" in toks),
    "totals_room": (lambda toks: (" ".join(toks[:toks.index("-")]) or None)
                    if ("-" in toks and "Subtotal" in toks) else None),
    # column header is PAGE furniture (top of every content page)
    "colhdr_mode": "page", "colhdr_row1": "Description", "colhdr_row2": None,
    # room continuation marker is "Room(con't)" at each page top; strip the carrier's, regenerate at our breaks
    "has_continued": True, "continued_fmt": "%s(con't)", "continued_style": "room",
    "continued_detect": (lambda t: "(con't)" in t or "(con’t)" in t),
    "continued_x": 49, "continued_size": 10,
    # add-line layout (1-line; Symbility column grid; desc wraps before the Quantity column)
    "columns": {"qty_right": 224, "unit_price": 274, "unit": 302.8},
    "unit_price_right": 293.4,                          # carrier right-aligns the unit price to the grey column's right edge
    "grey_cols": [[239.4, 293.4]], "grey_shade": 0.945,   # Unit Price column stripe (carrier also greys ACV, but our adds leave ACV empty)
    "addline_two_line": False, "desc_max_x": 185,
    "desc_whiteout": (47, -8, 240, 3), "desc_x": 49,
    # new-room folder title, styled to match the carrier's own folder titles (Helvetica-bold at the left margin)
    "room_title_font": "hebo", "room_title_size": 8.5, "room_title_x": 38,
    "room_note_font": "helv", "room_note_size": 7.5,
    # full bordered folder header (name row + dimension grid + diagram column) reproducing the carrier's folder boxes;
    # a CCS new room has no measurements yet, so value cells are left blank for the auditor and the diagram is a placeholder
    "folder_header": {
        "style": "box",
        "x0": 22.8, "x1": 604.8, "div_x": 503.2, "row_h": 14.5, "grey": 0.945, "name_gap": 3.5,
        "label_font": "hebo", "label_size": 8.0, "name_x": 42.8, "name_size": 8.5,
        "note_font": "helv", "note_size": 7.0,
        "rows": [
            [("Length:", 38.4), ("Width:", 132.0), ("Height:", 225.6)],
            [("Walls:", 38.4), ("Walls-subs:", 132.0), ("Walls-subs-cas-bsbd:", 225.6)],
            [("Doors:", 38.4), ("Windows:", 132.0), ("Openings:", 225.6), ("Missing Walls:", 319.2)],
            [("Floor:", 38.4), ("Ceiling:", 132.0), ("Perim (F):", 225.6), ("Perim (C):", 319.2)],
        ],
        "diagram_label": "Room diagram\n(to be added —\nsupplemental room)",
    },
}

def wrap_text(text, fn, size, width):                      # break a long string into lines that fit `width`
    out = []; cur = ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if fitz.get_text_length(t, fn, size) <= width or not cur:
            cur = t
        else:
            out.append(cur); cur = w
    if cur: out.append(cur)
    return out or [""]

def is_category(toks):                                     # ALL-CAPS sub-header, e.g. "LAMINATE FLOORING EXTRAS"
    al = [t for t in toks if any(c.isalpha() for c in t)]
    return bool(al) and all(t.isupper() for t in al) and any(len(t) >= 3 for t in al)

def _name_before_number(toks):
    nm = []
    for t in toks:
        if re.match(r'^[\d(]', t): break
        nm.append(t)
    return " ".join(nm) or None

def detect_format(C):
    """Auto-detect the platform from the carrier PDF's line-item / subtotal style."""
    for pno in range(C.page_count):
        t = C[pno].get_text()
        if re.search(r'\bTotals:\s', t) and re.search(r'^\s*\d{1,4}\.\s', t, flags=re.M):
            return XACTIMATE
        if re.search(r'-\s*Subtotal\s*\(\d+\s*items?\)', t):
            return SYMBILITY
    return XACTIMATE

# ---- load plan ----
if len(sys.argv) < 3:
    sys.exit("Usage: python3 build_spec.py <edit-plan.json> <out.pdf> [cover.pdf]")
PLAN_PATH = sys.argv[1]; OUT = sys.argv[2]; COVER = sys.argv[3] if len(sys.argv) > 3 else None
plan = json.load(open(PLAN_PATH, encoding="utf-8"))
base = os.path.dirname(os.path.abspath(PLAN_PATH))
carrier_path = plan["carrier_pdf"]
if not os.path.isabs(carrier_path):
    cand = os.path.join(base, carrier_path)
    carrier_path = cand if os.path.exists(cand) else carrier_path
C = fitz.open(carrier_path)
SPECS = {"xactimate": XACTIMATE, "symbility": SYMBILITY}
SP = SPECS.get(plan.get("format", "").lower()) or detect_format(C)
if SP.get("name") == "symbility" and "content_top" not in SP:
    sys.exit("Symbility spec not yet authored — run an Xactimate plan, or finish the Symbility spec.")

# spec shortcuts
CTOP, CBOT = SP["content_top"], SP["content_bottom"]
EX_TOP, EX_BOT = SP["extract_top"], SP["extract_bottom"]
FTR_TOP, HDR_BAND = SP["footer_top"], SP["header_band_h"]
LH, ROOM_GAP, TOTALS_GAP = SP["line_height"], SP["room_gap"], SP["totals_gap"]
FOLDER_GAP = SP.get("folder_gap", 0.0)                     # whitespace before a new folder (Xactimate inter-folder spacing)
FB, BB, FS = SP["body_font"], SP["bold_font"], SP["body_size"]
ITEM = SP["item_re"]; ITEM_LINES = SP.get("item_lines", 1)
COLX = SP["columns"]
COMPANY = plan.get("company_name", "Construction Claim Services")
BREAKDOWN = range(*plan["pages"]["breakdown"])
DIAG = range(*plan["pages"]["diagrams"])
HDR_TPL = plan["pages"].get("header_template", BREAKDOWN.start)

# CCS edit color: green by default; switch to terracotta ONLY if the carrier itself uses a green/teal
# color in its line items (so our green can't be confused with the carrier's). Overridable.
def carrier_uses_green(pages):
    for pno in pages:
        for b in C[pno].get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                for s in l.get("spans", []):
                    col = s.get("color", 0)
                    r, g, bl = (col >> 16 & 255) / 255, (col >> 8 & 255) / 255, (col & 255) / 255
                    if g > 0.45 and r < 0.5 and g + 0.10 >= bl:   # green or green-adjacent (incl. teal/cyan)
                        return True
    return False
_ec = (plan.get("edit_color") or "").strip().lower()
if os.environ.get("CCS_COLOR"):
    GREEN = tuple(float(x) for x in os.environ["CCS_COLOR"].split(","))
elif _ec.startswith("#") and len(_ec) == 7:
    GREEN = tuple(int(_ec[1:][i:i + 2], 16) / 255 for i in (0, 2, 4))
elif _ec == "terracotta":
    GREEN = TERRACOTTA
elif _ec == "green":
    GREEN = GREEN_STD
else:
    GREEN = TERRACOTTA if carrier_uses_green(BREAKDOWN) else GREEN_STD

# ---- index the plan ----
CORRECTS = {}
for e in plan.get("corrects", []):
    d = {"reason": clean(e.get("reason", ""))}
    if "swaps" in e: d["swaps"] = [tuple(s) for s in e["swaps"]]
    if "desc" in e:  d["desc"]  = [tuple(s) for s in e["desc"]]
    CORRECTS[e["item"]] = d
ADDS = {}
for e in plan.get("adds", []):
    ADDS[e["item"]] = [{"label": a["label"], "desc": a["desc"],
                        "cells": [(c[0], c[1]) for c in a["cells"]],
                        "reason": clean(a.get("reason", ""))} for a in e["lines"]]
NR_TOTALS = {}; NR_ITEM = {}; NR_ROOM = {}
for r in plan.get("new_rooms", []):
    a = r["anchor"]; entry = (r["name"], clean(r.get("reason", "")), r.get("items", []), r.get("dims") or {}, r.get("diagram"))
    if a["type"] == "totals":  NR_TOTALS.setdefault((a["pno"], a["room"]), []).append(entry)
    elif a["type"] == "item":  NR_ITEM.setdefault(a["item"], []).append(entry)
    elif a["type"] == "room":  NR_ROOM.setdefault((a["pno"], a["match"]), []).append(entry)

# ---- CCS green annotations (format-independent) ----
def box_h(rs):
    return 15 + 9 * (max(1, math.ceil(fitz.get_text_length(rs, "tiro", 7.5) / usable)) + 1) + pad
def draw_box(pg, top, label, rs):
    bh = box_h(rs)
    pg.draw_rect(fitz.Rect(36, top, W - 36, top + bh), color=GREEN, fill=WHITE, width=0.9)
    pg.insert_text((36 + pad, top + 11), label, fontname="tibo", fontsize=8.5, color=GREEN)
    pg.insert_textbox(fitz.Rect(36 + pad, top + 14, W - 36 - pad, top + bh - pad), rs,
                      fontname="tiro", fontsize=7.5, color=GREEN)
    return bh
def dash(s): return s.replace("—", " - ").replace("–", "-")   # em/en-dash -> hyphen (base-14 fonts render them as a dot/?)
def draw_room_title(pg, top, name):                            # simple new-room title (Xactimate)
    tf = SP.get("room_title_font", "tibo"); tsz = SP.get("room_title_size", 10); tx = SP.get("room_title_x", 37)
    pg.insert_text((tx, top + 11), dash(name), fontname=tf, fontsize=tsz, color=GREEN)
    return 16
def folder_header_h(fh):
    return fh["row_h"] * (1 + len(fh["rows"])) + fh.get("name_gap", 0)
def draw_room_sketch(pg, cell, dia):                           # a simple room outline scaled to the given measurements
    L = float(dia.get("length_ft") or 1) or 1.0; Wd = float(dia.get("width_ft") or 1) or 1.0
    pad = 9.0; labh = 9.0
    bw = cell.width - 2 * pad; bh = cell.height - 2 * pad - labh
    ar = Wd / L                                                 # height:width of the drawn rectangle = room W:L
    w = bw; h = w * ar
    if h > bh: h = bh; w = h / ar if ar else bw
    cx = cell.x0 + cell.width / 2.0; ytop = cell.y0 + pad
    rect = fitz.Rect(cx - w / 2.0, ytop, cx + w / 2.0, ytop + h)
    pg.draw_rect(rect, color=GREEN, fill=None, width=0.8)
    lbl = dia.get("label", "")
    if lbl:
        tw = fitz.get_text_length(lbl, "helv", 6)
        pg.insert_text((cx - tw / 2.0, rect.y1 + 8), lbl, fontname="helv", fontsize=6, color=GREEN)
def draw_folder_header(pg, top, name, dims=None, diagram=None):  # folder header matching the carrier's folder boxes
    fh = SP["folder_header"]; rh = fh["row_h"]; grey = (fh["grey"],) * 3; bord = GREEN
    x0, x1, dv = fh["x0"], fh["x1"], fh["div_x"]
    lf, ls = fh["label_font"], fh["label_size"]
    has_dia = bool(diagram)
    px1 = dv if has_dia else x1                                 # dimension panel right edge (leaves room for the sketch box)
    total = folder_header_h(fh)
    name_bot = top + rh; dim_top = name_bot + fh.get("name_gap", 0); dim_bot = top + total
    pg.draw_rect(fitz.Rect(x0, top, px1, name_bot), color=None, fill=grey)      # name row fill
    pg.draw_rect(fitz.Rect(x0, dim_top, px1, dim_bot), color=None, fill=grey)   # dimension panel (small white gap above, like the carrier)
    if has_dia:
        pg.draw_rect(fitz.Rect(dv, top, x1, dim_bot), color=None, fill=WHITE)   # sketch cell
        pg.draw_line(fitz.Point(dv, top), fitz.Point(dv, dim_bot), color=bord, width=0.6)
    pg.draw_rect(fitz.Rect(x0, top, x1, dim_bot), color=bord, fill=None, width=0.6)   # outer border (no separator line under the name)
    pg.insert_text((fh["name_x"], top + rh - 4), dash(name), fontname=lf, fontsize=fh["name_size"], color=GREEN)
    yy = dim_top
    for r in fh["rows"]:                                        # the whole new-room folder is a CCS addition -> all text in the CCS edit color
        for lbl, lx in r:
            pg.insert_text((lx, yy + rh - 4), lbl, fontname=lf, fontsize=ls, color=GREEN)
            val = (dims or {}).get(lbl.rstrip(":"))             # fill the measured value after the label, when known
            if val:
                vx = lx + fitz.get_text_length(lbl + " ", lf, ls)
                pg.insert_text((vx, yy + rh - 4), val, fontname=FB, fontsize=ls, color=GREEN)
        yy += rh
    if has_dia:
        draw_room_sketch(pg, fitz.Rect(dv, top, x1, dim_bot), diagram)
    return total

# ---- carrier block extraction (spec-aware) ----
def page_blocks(pno):
    ws = [w for w in C[pno].get_text("words") if EX_TOP <= w[1] <= EX_BOT]
    ws.sort(key=lambda w: (w[1], w[0]))
    lines = []; cur = []; ref = None
    for w in ws:
        if ref is None or w[1] - ref <= 3.0:
            cur.append(w); ref = ref if ref is not None else w[1]
        else:
            lines.append(cur); cur = [w]; ref = w[1]
    if cur: lines.append(cur)
    L = [{"y0": min(x[1] for x in ln), "y1": max(x[3] for x in ln), "x0": min(x[0] for x in ln),
          "first": sorted(ln, key=lambda x: x[0])[0][4],
          "toks": [w[4] for w in sorted(ln, key=lambda w: w[0])],
          "ty": sorted(ln, key=lambda x: x[0])[0][3]} for ln in lines]
    isroom = lambda d: any(t.startswith(SP["room_marker"]) for t in d["toks"])
    isitem = lambda d: bool(ITEM.match(d["first"])) and d["x0"] < 60   # item numbers live at the left margin (not "318." inside a dim block)
    B = []; i = 0
    while i < len(L):
        d = L[i]
        if isroom(d):
            j = i + 1                                          # room header runs up to the next item / room / column header
            while j < len(L) and not isitem(L[j]) and not isroom(L[j]) and L[j]["first"] != SP.get("colhdr_row1"): j += 1
            B.append({"pno": pno, "y0": d["y0"] - 1.5, "y1": L[j - 1]["y1"] + 1.5,
                      "first": d["first"], "kind": "room", "text": " ".join(d["toks"])}); i = j
        elif isitem(d) and (SP.get("item_block") == "var" or i + 1 < len(L)):
            if SP.get("item_block") == "var":                # item = number line .. until next item/room/subtotal/category (may be last on page)
                j = i + 1
                while (j < len(L) and not isitem(L[j]) and not isroom(L[j])
                       and not SP["is_totals"](L[j]["toks"]) and not is_category(L[j]["toks"])):
                    j += 1
                last = j - 1
            else:
                last = i + ITEM_LINES - 1
            B.append({"pno": pno, "y0": d["y0"] - 1.5, "y1": L[last]["y1"] + 1.5,
                      "first": d["first"], "kind": "item", "ty": d["ty"]}); i = last + 1
        else:
            B.append({"pno": pno, "y0": d["y0"] - 1.5, "y1": d["y1"] + 1.5,
                      "first": d["first"], "kind": "line", "text": " ".join(d["toks"])}); i += 1
    # re-attach horizontal rules sitting in gaps to the nearest block (else the reflow drops them)
    rules = []
    for dr in C[pno].get_drawings():
        for it in dr["items"]:
            if it[0] == "l" and abs(it[1].y - it[2].y) < 0.6 and abs(it[2].x - it[1].x) > 120 and CTOP <= it[1].y <= CBOT:
                rules.append(it[1].y)
            elif it[0] == "re" and it[1].height < 2.5 and it[1].width > 120 and CTOP <= it[1].y0 <= CBOT:
                rules.append(it[1].y0)
    for yr in rules:
        if any(b["y0"] <= yr <= b["y1"] for b in B): continue
        above = [b for b in B if b["y1"] <= yr]
        if above:
            b = max(above, key=lambda b: b["y1"])
            cap = min([bb["y0"] for bb in B if bb["y0"] > b["y1"]], default=yr + 0.6)
            b["y1"] = min(yr + 0.6, cap)
        else:
            below = [b for b in B if b["y0"] >= yr]
            if below:
                b = min(below, key=lambda b: b["y0"]); b["y0"] = yr - 0.6
    # reserve full height for a folder-header sketch (e.g. the R13 roof diagram): absorb the blocks it overlaps
    # into one, extended to the diagram's full extent, so the reflow doesn't pack over it and clip it.
    for img in C[pno].get_images(full=True):
        for r in C[pno].get_image_rects(img[0]):
            if not (30 < r.height < 400 and r.width < 320 and r.x0 < 320): continue   # a left-column sketch, not the full-page background
            ov = [b for b in B if b["kind"] != "item" and b["y1"] > r.y0 + 2 and b["y0"] < r.y1 - 2]
            if not ov: continue
            first = min(ov, key=lambda b: b["y0"])
            first["y0"] = min(first["y0"], r.y0 - 1.5); first["y1"] = max(max(b["y1"] for b in ov), r.y1 + 1.5)
            for b in ov:
                if b is not first and b in B: B.remove(b)
    B.sort(key=lambda b: b["y0"])
    return B

def swap_targets(pno, item, changes):
    words = C[pno].get_text("words")
    t = next(w[1] for w in words if w[4] == SP.get("item_token_fmt", "%d.") % item and w[0] < 60)
    nxt = sorted(w[1] for w in words if ITEM.match(w[4]) and w[0] < 60 and w[1] > t + 4)   # item numbers live at the left margin
    bot = nxt[0] if nxt else t + 30
    blk = [w for w in words if t - 2 <= w[1] < bot]
    def run(tg):
        tk = tg.split(); n = len(tk); row = sorted(blk, key=lambda w: (round(w[1]), w[0]))
        for i in range(len(row) - n + 1):
            if [s[4] for s in row[i:i + n]] == tk:
                seq = row[i:i + n]
                return fitz.Rect(min(s[0] for s in seq), min(s[1] for s in seq),
                                 max(s[2] for s in seq), max(s[3] for s in seq))
    return [(run(o), nw) for o, nw in changes]

# ---- column-header template + continuation stamps (spec-aware) ----
def find_colhdr():
    for pno in BREAKDOWN:
        ws = C[pno].get_text("words")
        h = [w for w in ws if w[4] == SP["colhdr_row1"]]
        if not h: continue
        hy = h[0][1]
        row = [w for w in ws if hy - 2 <= w[1] <= hy + 14]      # both header rows when present
        top = min(w[1] for w in row); bot = max(w[3] for w in row)
        rl = [it[1].y for dr in C[pno].get_drawings() for it in dr["items"]
              if it[0] == "l" and abs(it[1].y - it[2].y) < 0.6 and abs(it[2].x - it[1].x) > 120 and bot < it[1].y < bot + 6]
        return pno, top - 1.5, (max(rl) + 1.2 if rl else bot + 1.5)
    return BREAKDOWN.start, 239.0, 265.0
if SP.get("pagefurn_y"):                                   # Symbility: fixed page-furniture band (col header + ESTIMATE line)
    CH_PNO, (CH_Y0, CH_Y1) = HDR_TPL, SP["pagefurn_y"]
else:
    CH_PNO, CH_Y0, CH_Y1 = find_colhdr()
CH_H = CH_Y1 - CH_Y0

# ---- reflow ----
est = fitz.open(); pg = est.new_page(width=W, height=H); y = CTOP
def newpage():
    global pg, y; pg = est.new_page(width=W, height=H); y = CTOP
SUPP_N = [0]                                                   # output-order counter: added line items are labeled Supp-1., Supp-2., ...
def _addline_layout(a, lbl):                                   # label/desc geometry, shared by height calc and render
    two = SP["addline_two_line"]
    if two:                                                     # Xactimate: label in margin, desc pushed after it
        labx, lblfs = 37, FS
        descx = max(59, 37 + fitz.get_text_length(lbl, BB, FS) + 5)
        dlines = [a["desc"]]
    else:                                                       # Symbility: desc fixed at the carrier's description column; label right-aligned just before it
        lblfs = FS; descx = SP["desc_x"]
        labx = max(8.0, descx - 2 - fitz.get_text_length(lbl, BB, lblfs))
        dlines = wrap_text(a["desc"], FB, FS, SP.get("desc_max_x", 185) - descx)
    return labx, lblfs, descx, dlines
def addline_rows(a):                                           # height (in 14pt rows) a rendered add line occupies (label-independent)
    return max(len(_addline_layout(a, "Supp-88.")[3]), 2 if SP["addline_two_line"] else 1)
def emit_add_line(a, box_label="Supp-new", paginate=False):    # draw one CCS add line + its justification box at y; advance y
    global y
    two = SP["addline_two_line"]
    SUPP_N[0] += 1; lbl = "Supp-%d." % SUPP_N[0]               # sequential in order of appearance on the output
    labx, lblfs, descx, dlines = _addline_layout(a, lbl)
    rows = max(len(dlines), 2 if two else 1)
    if paginate and y + rows * 14 + 2 + box_h(a["reason"]) + gap > CBOT: newpage()
    for gx0, gx1 in SP.get("grey_cols", []):                    # carrier-style grey column stripes behind the numbers row
        pg.draw_rect(fitz.Rect(gx0, y + 0.5, gx1, y + 14.0), color=None, fill=(SP.get("grey_shade", 0.945),) * 3)
    pg.insert_text((labx, y + 10), lbl, fontname=BB, fontsize=lblfs, color=GREEN)
    for k, dl in enumerate(dlines):
        pg.insert_text((descx, y + 10 + k * 14), dl, fontname=FB, fontsize=FS, color=GREEN)
    cy = y + (24 if two else 10); upr = SP.get("unit_price_right")
    for col, ct in a["cells"]:
        if col == "qty":                                    # "13.00 LF" -> number right-aligned + unit
            qn, un = (ct.split(None, 1) + [""])[:2]
            pg.insert_text((COLX["qty_right"] - fitz.get_text_length(qn, FB, FS), cy), qn, fontname=FB, fontsize=FS, color=GREEN)
            if un.strip(): pg.insert_text((COLX["unit"], cy), un, fontname=FB, fontsize=FS, color=GREEN)
        elif col == "unit_price" and upr:                   # right-align the unit price to the carrier's column edge
            pg.insert_text((upr - fitz.get_text_length(ct, FB, FS), cy), ct, fontname=FB, fontsize=FS, color=GREEN)
        elif col in COLX:
            pg.insert_text((COLX[col], cy), ct, fontname=FB, fontsize=FS, color=GREEN)
        else:
            pg.insert_text((COLX["qty_right"], cy), ct, fontname=FB, fontsize=FS, color=GREEN)
    y += rows * 14 + 2
    y += draw_box(pg, y, box_label, a["reason"]) + gap
def draw_xact_room_header(pg, top, name, dims, diagram):       # Xactimate room-style header: diagram (left) + name/Height + rule + 2-col dims
    fh = SP["folder_header"]; rh = fh["row_h"]
    has_dia = bool(diagram)
    tx = fh["title_x_diag"] if has_dia else fh["title_x_nodiag"]
    pg.insert_text((tx, top + 11), dash(name), fontname=fh["title_font"], fontsize=fh["title_size"], color=GREEN)
    if dims and dims.get("Height"):
        pg.insert_text((fh["height_x"], top + 11), "Height: %s" % dims["Height"], fontname=fh["title_font"], fontsize=fh["height_size"], color=GREEN)
    rx0 = tx if has_dia else fh["rule_x0_nodiag"]
    pg.draw_line(fitz.Point(rx0, top + 14.5), fitz.Point(fh["rule_x1"], top + 14.5), color=GREEN, width=0.6)   # rule under the room title
    dcols = fh["dim_cols"]; lf, ls = fh["label_font"], fh["label_size"]; dtop = top + fh["dim_top"]; nrows = 0
    for label, ci, ri in fh["fields"]:
        val = dims.get(label) if dims else None
        if not val: continue
        pg.insert_text((dcols[ci], dtop + 11 + ri * rh), "%s %s" % (val, label), fontname=lf, fontsize=ls, color=GREEN)
        nrows = max(nrows, ri + 1)
    dim_h = (fh["dim_top"] + nrows * rh + 3) if nrows else 16
    dia_h = 0
    if has_dia:
        dx0, dx1 = fh["diagram_x"]; dia_h = fh["diagram_h"]
        cp = diagram.get("copy")
        if cp:                                                 # clip-compose an existing carrier room sketch (e.g. copy the top-floor chimney)
            r = cp["rect"]
            pg.show_pdf_page(fitz.Rect(dx0, top + 2, dx1, top + 2 + dia_h), C, cp["pno"], clip=fitz.Rect(r[0], r[1], r[2], r[3]))
        elif diagram.get("length_ft"):
            draw_room_sketch(pg, fitz.Rect(dx0, top + 2, dx1, top + 2 + dia_h), diagram)
    return max(dim_h, dia_h) + 4
def insert_newroom(name, rs, items=(), dims=None, diagram=None):
    global y
    fh = SP.get("folder_header"); style = fh.get("style") if fh else None
    if style == "box":   head_h = folder_header_h(fh)
    elif style == "room": head_h = (fh["diagram_h"] + 4) if diagram else (fh["dim_top"] + 3 * fh["row_h"] + 4 if dims else 16)
    else:                head_h = 16
    if y + head_h + box_h(rs) + gap > CBOT: newpage()
    if style == "box":
        y += draw_folder_header(pg, y, name, dims, diagram)
    elif style == "room":
        y += draw_xact_room_header(pg, y, name, dims, diagram)
    else:
        y += draw_room_title(pg, y, name)
    y += draw_box(pg, y, "Supp-new", rs) + gap
    for a in items:                                            # the room's own CCS-added line items, each with its box
        emit_add_line(a, box_label="Supp-new", paginate=True)
def stamp_colhdr():
    global y
    pg.show_pdf_page(fitz.Rect(0, y, W, y + CH_H), C, CH_PNO, clip=fitz.Rect(0, CH_Y0, W, CH_Y1)); y += CH_H
def stamp_continued(folder):
    global y
    if SP.get("continued_style") == "room":          # Symbility: "Room(con't)" left, bold
        sz = SP.get("continued_size", 10)
        pg.insert_text((SP.get("continued_x", 49), y + sz - 1), SP["continued_fmt"] % folder, fontname=BB, fontsize=sz, color=BLACK)
        y += sz + 5
    else:                                            # Xactimate: centered "CONTINUED - X" + column header
        txt = SP["continued_fmt"] % folder
        tw = fitz.get_text_length(txt, BB, FS)
        pg.insert_text(((W - tw) / 2.0, y + 11), txt, fontname=BB, fontsize=FS, color=BLACK)
        y += 16; stamp_colhdr()

stream = []
for pno in BREAKDOWN: stream += page_blocks(pno)
# Strip the carrier's page-break artifacts (CONTINUED markers + repeated column headers); folder-start
# headers stay. We regenerate CONTINUED + header at OUR page breaks. Label each block by its folder.
R1, R2 = SP["colhdr_row1"], SP.get("colhdr_row2")
cont_detect = SP.get("continued_detect")
folder_colhdr = SP.get("colhdr_mode") == "folder"
clean_s = []; colhdr_at = []; i = 0
while i < len(stream):
    t = stream[i].get("text", "")
    if cont_detect and cont_detect(t):                 # carrier continuation marker (CONTINUED.. / Room(con't))
        i += 1                                         # strip it AND the repeated column header that follows it
        if i < len(stream) and stream[i].get("text", "").startswith(R1): i += 1
        if R2 and i < len(stream) and stream[i].get("text", "").startswith(R2): i += 1
        continue
    if folder_colhdr and t.startswith(R1):             # Xactimate: drop EVERY carrier column header (row1[+row2]) and
        colhdr_at.append(len(clean_s))                 # regenerate exactly one before the next block (the folder body start)
        i += 1
        if R2 and i < len(stream) and stream[i].get("text", "").startswith(R2): i += 1
        continue
    if R2 and t.startswith(R2) and not (clean_s and clean_s[-1].get("text", "").startswith(R1)):
        i += 1; continue
    if folder_colhdr and clean_s and stream[i]["kind"] == "line" and t and t == clean_s[-1].get("text", ""):
        i += 1; continue                               # dedup a repeated running-header label (e.g. "Source - Eagle View" twice)
    clean_s.append(stream[i]); i += 1
stream = clean_s
folders = [None] * len(stream); _cur = None
for i in range(len(stream) - 1, -1, -1):
    nm = SP["totals_room"](stream[i].get("text", "").split())
    if nm: _cur = nm
    folders[i] = _cur

# Folder layout (Xactimate). `colhdr_at` are the stream indices that need a regenerated column header
# stamped just before them (the folder body start). The folder TITLE (name + dim block) is the block(s)
# above, back to the previous item / Totals line — it gets the inter-folder gap and MAY sit at the bottom
# of a page. The regenerated column header + its first line item are kept together, so if they don't fit,
# only they move to the next page (the title/dims stay behind) — matching the carrier.
folder_start = [False] * len(stream); colhdr_keep = {}
colhdr_set = set(colhdr_at)
if folder_colhdr:
    TOTALSISH = re.compile(r'^(Totals?:|Area Totals:)')
    BARE = re.compile(r'^[A-Za-z][A-Za-z &/]*$')
    closer = [False] * len(stream)                             # folder closers: a Totals line + a bare-name wrap of its (long) folder name
    for k in range(len(stream)):
        t = stream[k].get("text", "")
        if TOTALSISH.match(t):
            closer[k] = True
        elif (k > 0 and TOTALSISH.match(stream[k - 1].get("text", "")) and stream[k]["kind"] == "line" and BARE.match(t.strip())
              and stream[k]["pno"] == stream[k - 1]["pno"] and stream[k]["y0"] - stream[k - 1]["y1"] < LH * 1.5):
            closer[k] = True                                   # a WRAP of the totals name is the very next text line (measured −2.0pt
                                                               # block gap on State Farm); a next-folder TITLE sits ~44–46pt below or on
                                                               # the next page. Threshold 1.5×line-height (~20.6) splits the dead zone.
    for p in colhdr_at:
        gs = 0
        for k in range(p - 1, -1, -1):
            if stream[k]["kind"] == "item" or closer[k]:
                gs = k + 1; break
        folder_start[gs] = True
        last = p                                               # the folder's first line item (skip a trade sub-header if present)
        k = p
        while k < len(stream) and k <= p + 3 and stream[k]["kind"] != "item":
            k += 1
        if k < len(stream) and stream[k]["kind"] == "item": last = k
        colhdr_keep[p] = CH_H + sum(stream[m]["y1"] - stream[m]["y0"] for m in range(p, last + 1))

bd_start = est.page_count - 1
prev_folder = None; pending_nr = []
for idx, blk in enumerate(stream):
    folder = folders[idx]
    toks = blk.get("text", "").split()
    is_totals = SP["is_totals"](toks)
    # Xactimate section-total lines ("Total: Source - Eagle View", "Total: 2nd Level") aren't caught by
    # is_totals ("Totals:" with an s) but close a section the same way — give them the same gap after,
    # so the next folder's lead-in matches the others (was 37pt above General Items vs ~51 elsewhere)
    if folder_colhdr and not is_totals and blk["kind"] == "line" and blk.get("text", "").startswith("Total:"):
        is_totals = True
    h = blk["y1"] - blk["y0"]
    fstart = folder_start[idx]
    needs_colhdr = idx in colhdr_set
    if fstart and pending_nr:                                  # flush deferred new rooms after the closing folder (incl. any wrapped totals name), before the next folder
        for args in pending_nr: insert_newroom(*args)
        pending_nr = []
    extra = (FOLDER_GAP if y > CTOP + 1 else 0.0) if fstart else (ROOM_GAP if blk["kind"] == "room" else 0.0)
    itno = None
    if blk["kind"] == "item":
        m = re.match(r'^(\d+)', blk["first"])
        if m: itno = int(m.group(1))
    need = extra + h
    if itno in CORRECTS: need += box_h(CORRECTS[itno]["reason"]) + gap
    if itno in ADDS:
        for a in ADDS[itno]:
            need += addline_rows(a) * 14 + 2 + box_h(a["reason"]) + gap
    if is_totals: need += TOTALS_GAP
    if needs_colhdr: need = max(need, extra + colhdr_keep[idx])   # regenerated column header + first item kept together
    if y + need > CBOT:
        newpage()
        # a regenerated folder column header renders itself — no "CONTINUED" before it (the title is on the
        # previous page); a true mid-folder break (items continuing) does get CONTINUED + header
        if SP.get("has_continued") and folder is not None and folder == prev_folder and not fstart and not needs_colhdr:
            stamp_continued(folder)
        if fstart: extra = 0.0                                 # folder now begins at the top of the page; drop the lead gap
    y += extra
    if needs_colhdr: stamp_colhdr()                            # regenerate this folder's column header in place
    pg.show_pdf_page(fitz.Rect(0, y, W, y + h), C, blk["pno"], clip=fitz.Rect(0, blk["y0"], W, blk["y1"]))
    shift = y - blk["y0"]
    if itno in CORRECTS:
        cc = CORRECTS[itno]
        if "swaps" in cc:
            for rect, new in swap_targets(blk["pno"], itno, cc["swaps"]):
                if rect:
                    pg.draw_rect(fitz.Rect(rect.x0 - 1, rect.y0 + shift - 1, rect.x1 + 1, rect.y1 + shift + 1), color=WHITE, fill=WHITE)
                    pg.insert_text((rect.x0, rect.y1 + shift - 2), new, fontname=FB, fontsize=FS, color=GREEN)
        if "desc" in cc:
            ty = blk.get("ty", blk["y0"] + 11) + shift
            wx0, wy0, wx1, wy1 = SP["desc_whiteout"]
            pg.draw_rect(fitz.Rect(wx0, ty + wy0, wx1, ty + wy1), color=WHITE, fill=WHITE); x = SP["desc_x"]
            for text, col in cc["desc"]:
                pg.insert_text((x, ty), text, fontname=FB, fontsize=FS, color=(GREEN if col == "g" else BLACK))
                x += fitz.get_text_length(text, FB, FS)
    y += h
    if is_totals: y += TOTALS_GAP
    if itno in CORRECTS: y += draw_box(pg, y, "Supp-changed", CORRECTS[itno]["reason"]) + gap
    if itno in ADDS:
        for a in ADDS[itno]: emit_add_line(a)
    if itno in NR_ITEM:
        for name, rs, items, dims, diagram in NR_ITEM[itno]: insert_newroom(name, rs, items, dims, diagram)
    if blk["kind"] == "line":
        rm = SP["totals_room"](toks)
        if rm:                                              # plan anchors by the first word of the room name
            for entry in NR_TOTALS.get((blk["pno"], rm.split()[0]), []):
                if folder_colhdr: pending_nr.append(entry)  # Xactimate: defer past any wrapped totals name to the next folder
                else: insert_newroom(*entry)                # Symbility: single-line subtotals, insert inline
    if blk["kind"] == "room":
        for (apno, sub), lst in NR_ROOM.items():
            if blk["pno"] == apno and sub in blk.get("text", ""):
                for name, rs, items, dims, diagram in lst: insert_newroom(name, rs, items, dims, diagram)
    prev_folder = folder
for args in pending_nr: insert_newroom(*args)               # flush any new rooms anchored to the final folder

# ---- CCS header on every breakdown page; drop timestamps ----
nb = SP["name_box"]; cb = SP["company_box"]
co_font = SP["bold_font"]; co_size = SP.get("company_size", 11); co_align = SP.get("company_align", 1)
NPAGES = est.page_count                                     # breakdown page count (diagrams added after this loop)
for i in range(bd_start, est.page_count):
    p = est[i]
    p.show_pdf_page(fitz.Rect(0, 0, W, HDR_BAND), C, HDR_TPL, clip=fitz.Rect(0, 0, W, HDR_BAND))
    p.draw_rect(fitz.Rect(*nb), color=WHITE, fill=WHITE)
    if co_align == 1:
        p.insert_textbox(fitz.Rect(*cb), COMPANY, fontname=co_font, fontsize=co_size, color=BLACK, align=1)
    else:
        p.insert_text((cb[0], cb[1] + co_size), COMPANY, fontname=co_font, fontsize=co_size, color=BLACK)
    if SP.get("header_clear_below"):        # drop any folder text (e.g. "Source - Eagle View") the template page carried in its band
        p.draw_rect(fitz.Rect(0, SP["header_clear_below"], W, HDR_BAND), color=WHITE, fill=WHITE)
    if SP.get("colhdr_mode") == "page":     # Symbility: column header is page furniture, stamp it on every page
        p.show_pdf_page(fitz.Rect(0, HDR_BAND, W, HDR_BAND + CH_H), C, CH_PNO, clip=fitz.Rect(0, CH_Y0, W, CH_Y1))
    if SP.get("footer_mode") == "carrier":  # reproduce carrier footer (claim#/date), replace the page number
        fb = SP["footer_band"]
        p.show_pdf_page(fitz.Rect(0, fb[0], W, fb[1]), C, HDR_TPL, clip=fitz.Rect(0, fb[0], W, fb[1]))
        p.draw_rect(fitz.Rect(*SP["footer_pagenum_box"]), color=WHITE, fill=WHITE)
        px, py = SP["footer_pagenum_xy"]
        p.insert_text((px, py), "Page %d of %d" % (i - bd_start + 1, NPAGES), fontname=SP["body_font"],
                      fontsize=SP.get("footer_pagenum_size", 9), color=BLACK)
        if SP.get("footer_claim_box"):              # drop the carrier claim number from the footer
            p.draw_rect(fitz.Rect(*SP["footer_claim_box"]), color=WHITE, fill=WHITE)
    else:
        p.draw_rect(fitz.Rect(0, FTR_TOP, W, H), color=WHITE, fill=WHITE)

# ---- diagrams carried whole, footer whited ----
for idx in DIAG:
    r = C[idx].rect; p = est.new_page(width=r.width, height=r.height)
    p.show_pdf_page(fitz.Rect(0, 0, r.width, r.height), C, idx)
    p.draw_rect(fitz.Rect(0, r.height - 20, r.width, r.height), color=WHITE, fill=WHITE)

if SP.get("footer_mode") != "carrier":                     # Xactimate: simple bottom-right page number
    for i in range(est.page_count):
        r = est[i].rect
        est[i].insert_text((r.width - 92, r.height - 12), "Page: %d" % (i + 1), fontname="tiro", fontsize=9.7, color=BLACK)

# ---- cover letter (CCS boilerplate, all-placeholder) ----
def build_cover():
    LX, RX, FSc, LH2 = 72, 540, 11, 14
    doc = fitz.open(); p = doc.new_page(width=W, height=H)
    def Ltxt(t, yy, bold=False): p.insert_text((LX, yy), t, fontname=("tibo" if bold else "tiro"), fontsize=FSc, color=BLACK)
    def LV(label, val, yy):
        p.insert_text((LX, yy), label, fontname="tibo", fontsize=FSc, color=BLACK)
        p.insert_text((LX + fitz.get_text_length(label + " ", "tibo", FSc), yy), val, fontname="tiro", fontsize=FSc, color=BLACK)
    def Rtxt(t, yy, bold=False):
        fn = "tibo" if bold else "tiro"
        p.insert_text((RX - fitz.get_text_length(t, fn, FSc), yy), t, fontname=fn, fontsize=FSc, color=BLACK)
    TY = 72; ly = TY
    Ltxt("Property Address:", ly, True); ly += LH2
    Ltxt("[PROPERTY ADDRESS]", ly); ly += LH2
    Ltxt("[CITY, STATE ZIP]", ly); ly += LH2 + 8
    LV("Insured:", "[INSURED NAME(S)]", ly); ly += LH2
    Ltxt("([INSURED ENTITY, if applicable])", ly); ly += LH2 + 8
    LV("Policy Number:", "[POLICY NUMBER]", ly); ly += LH2
    LV("Claim Number:", "[CLAIM NUMBER]", ly); ly += LH2
    ry = TY
    Rtxt("[CONTRACTOR COMPANY]", ry, True); ry += LH2
    for t in ["[CONTRACTOR CONTACT NAME]", "[CONTRACTOR ADDRESS]", "[CONTRACTOR CITY, STATE ZIP]", "[CONTRACTOR EMAIL]", "[CONTRACTOR PHONE]"]:
        Rtxt(t, ry); ry += LH2
    Y = [max(ly, ry) + 30]
    def wrap(txt, fn, size, width):
        out = []; cur = ""
        for w in txt.split():
            t = (cur + " " + w).strip()
            if fitz.get_text_length(t, fn, size) <= width: cur = t
            else: out.append(cur); cur = w
        if cur: out.append(cur)
        return out or [""]
    def emit(txt, bold=False, g=0, nowrap=False):
        fn = "tibo" if bold else "tiro"
        for ln in ([txt] if nowrap else wrap(txt, fn, FSc, RX - LX)):
            p.insert_text((LX, Y[0]), ln, fontname=fn, fontsize=FSc, color=BLACK); Y[0] += LH2
        Y[0] += g
    sp = lambda d: Y.__setitem__(0, Y[0] + d)
    emit("[CARRIER COMPANY]", nowrap=True)
    emit("Attn: Claim Representative and Estimator [ADJUSTER NAME]", nowrap=True)
    emit("[ADJUSTER EMAIL] | [ADJUSTER PHONE]", nowrap=True)
    sp(12); emit("RE: Updates to [ESTIMATE DATE] Estimated Cost of Repairs", bold=True, nowrap=True); sp(10)
    emit("Dear Representative [ADJUSTER LAST NAME],", nowrap=True); sp(6)
    emit("First, thank you for your initial estimate dated [ESTIMATE DATE]. I appreciate the baseline provided to get this claim moving forward.", g=8)
    emit("I recognize that many contractor supplement requests are nothing more than attempts to negotiate additional funds and many start from the presumption that a fight is forthcoming. That is neither my approach with, nor my experience of the supplements I submit.", g=8)
    emit("To the contrary, to the best of my ability, everything contained in this supplement (and every supplement I submit) is a factual, industry-standard justified, accurate assessment of corrections needed to meet the mitigation and reconstruction requirements, as established by best-practice construction and market pricing, and reflect the actual steps and materials required to restore the property to its pre-loss state.", g=8)
    emit("If I have achieved the objective I articulated, the result should be a collaborative, efficient, and accurate service to the insured. That is my goal.", g=8)
    emit("Since I am not a professional adjuster, I account for the possibility of me being incorrect. Therefore, for each of the items detailed in the following pages, I request that you either:", g=4)
    emit("     a.  Correct the item, if there is in fact an error, or", nowrap=True)
    emit("     b.  Provide a note why that item was in fact correct on the estimate.", nowrap=True, g=8)
    emit("Thank you for your partnership and [CARRIER]'s continued support of the insured.", g=16)
    emit("With appreciation,", nowrap=True); sp(22)
    emit("[CONTRACTOR CONTACT NAME]", nowrap=True); emit("[CONTRACTOR COMPANY]", nowrap=True)
    return doc

# ---- assemble ----
fin = fitz.open()
if COVER and os.path.exists(COVER): fin.insert_pdf(fitz.open(COVER))
elif plan.get("cover"): fin.insert_pdf(build_cover())
fin.insert_pdf(est)
fin.save(OUT)
print("saved", OUT, "| format:", SP["name"], "| pages:", fin.page_count,
      "| corrects:", len(CORRECTS), "| add-lines:", sum(len(v) for v in ADDS.values()),
      "| new-rooms:", sum(len(v) for v in list(NR_TOTALS.values()) + list(NR_ITEM.values()) + list(NR_ROOM.values())))

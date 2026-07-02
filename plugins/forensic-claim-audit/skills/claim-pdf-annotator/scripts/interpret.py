#!/usr/bin/env python3
"""
interpret.py — CCS forensic claim audit: suggestion list  ->  edit-plan JSON.

Turns the markdown suggestion list into the structured edit plan that build_spec.py
renders. It does the MECHANICAL work deterministically (parse the table, filter to
Agreed, classify, copy reasons verbatim, find item anchors, index the carrier PDF)
and BEST-EFFORT extraction of the interpretive fields (Correct field swaps, Add
cells, new-room anchors), flagging anything it isn't sure about. It validates every
entry against the carrier PDF so a bad anchor or a swap whose old-value isn't on the
page is caught BEFORE rendering.

Format-aware: detects whether the carrier estimate is Xactimate or Symbility and
indexes/anchors accordingly, so it produces a plan for either platform.

Usage:
    python3 interpret.py <suggestion-list.md> <carrier.pdf> <out-plan.json> [--truth known-plan.json]

Requires: PyMuPDF (fitz).
"""
import sys, os, re, json
try:
    import fitz
except ImportError:
    sys.exit("ERROR: PyMuPDF not installed. Run: pip install pymupdf --break-system-packages")

# =============================== format specs (structure only) ===============================
def is_category(toks):                                     # ALL-CAPS sub-header, e.g. "LAMINATE FLOORING EXTRAS"
    al = [t for t in toks if any(c.isalpha() for c in t)]
    return bool(al) and all(t.isupper() for t in al) and any(len(t) >= 3 for t in al)

XACT = {
    "name": "xactimate", "colhdr_row1": "QUANTITY",
    "item_re": re.compile(r'^\d{1,4}\.$'), "item_token": "%d.", "item_block": "fixed2",
    "ex_top": 68.0, "ex_bot": 740.0, "room_marker": "Height",
    "is_totals": (lambda toks: bool(toks) and toks[0] == "Totals:"),
    "totals_room": (lambda toks: toks[1] if (len(toks) > 1 and toks[0] == "Totals:") else None),
    "section_totals": True,                                # apply the "Main Level / 2nd Level / ..." filter
}
SYMB = {
    "name": "symbility", "colhdr_row1": "Description",
    "item_re": re.compile(r'^\d{1,4}$'), "item_token": "%d", "item_block": "var",
    "ex_top": 106.0, "ex_bot": 736.0, "room_marker": "Height",
    "is_totals": (lambda toks: "Subtotal" in toks and "-" in toks),
    "totals_room": (lambda toks: (" ".join(toks[:toks.index("-")]) or None) if ("-" in toks and "Subtotal" in toks) else None),
    "section_totals": False,
}
def detect_format(C):
    for pno in range(C.page_count):
        t = C[pno].get_text()
        if re.search(r'-\s*Subtotal\s*\(\d+\s*items?\)', t): return SYMB
        if re.search(r'\bTotals:\s', t) and re.search(r'^\s*\d{1,4}\.\s', t, flags=re.M): return XACT
    return XACT

# section-subtotal "Totals:" lines (Xactimate, NOT a room): "Totals: Main Level", "Totals: Labor Minimums", ...
SECTION_WORDS = {"Source", "Subtotal", "Line"}
SECTION_NEXT = {"Level", "Minimums"}
def is_section_totals(toks):
    if "Totals:" not in toks: return False
    ti = toks.index("Totals:")
    room = toks[ti + 1] if ti + 1 < len(toks) else ""
    nxt = toks[ti + 2] if ti + 2 < len(toks) else ""
    return room in SECTION_WORDS or nxt in SECTION_NEXT

# ---------- markdown table ----------
def parse_table(md):
    rows = []; hdr = None
    for ln in open(md, encoding="utf-8"):
        if not ln.strip().startswith("|"): continue
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        if hdr is None: hdr = [x.lower() for x in c]; continue
        if set("".join(c)) <= set("-: "): continue
        rows.append(dict(zip(hdr, c)))
    return rows

# ---------- carrier PDF blocks (spec-aware) ----------
def page_blocks(C, pno, SP):
    ITEM = SP["item_re"]
    ws = [w for w in C[pno].get_text("words") if SP["ex_top"] <= w[1] <= SP["ex_bot"]]
    ws.sort(key=lambda w: (w[1], w[0]))
    lines = []; cur = []; ref = None
    for w in ws:
        if ref is None or w[1] - ref <= 3.0:
            cur.append(w); ref = ref if ref is not None else w[1]
        else:
            lines.append(cur); cur = [w]; ref = w[1]
    if cur: lines.append(cur)
    L = [{"first": sorted(ln, key=lambda x: x[0])[0][4],
          "x0": min(s[0] for s in ln),
          "toks": [s[4] for s in sorted(ln, key=lambda x: x[0])]} for ln in lines]
    isroom = lambda d: any(t.startswith(SP["room_marker"]) for t in d["toks"])
    isitem = lambda d: bool(ITEM.match(d["first"])) and d["x0"] < 60      # item numbers live at the left margin
    room_bound = lambda d: isitem(d) or isroom(d)                        # room block = up to next item/room (absorbs $0 totals)
    item_bound = lambda d: isitem(d) or isroom(d) or SP["is_totals"](d["toks"]) or is_category(d["toks"])
    B = []; i = 0
    while i < len(L):
        d = L[i]
        if isroom(d):
            j = i + 1
            while j < len(L) and not room_bound(L[j]): j += 1
            B.append({"pno": pno, "kind": "room", "toks": d["toks"]}); i = j
        elif isitem(d) and (SP["item_block"] == "var" or i + 1 < len(L)):
            if SP["item_block"] == "var":                       # var item may be the last line on a page (1-line complete)
                j = i + 1
                while j < len(L) and not item_bound(L[j]): j += 1
            else:
                j = i + 2
            B.append({"pno": pno, "kind": "item", "first": d["first"]}); i = j
        else:
            B.append({"pno": pno, "kind": "line", "toks": d["toks"]}); i += 1
    return B

def build_index(C, SP):
    item_page = {}; totals_anchors = []; room_anchors = []; detail_pages = []; page_blk = {}
    sect = SP["section_totals"]
    colhdr = SP.get("colhdr_row1")
    for pno in range(C.page_count):
        blocks = page_blk[pno] = page_blocks(C, pno, SP)
        # a breakdown page has numbered line items AND the column header (excludes cover/explanation pages
        # whose stray numbered text would otherwise look like items — e.g. the first folder header page)
        detail = any(b["kind"] == "item" for b in blocks) and bool(colhdr) and colhdr in C[pno].get_text()
        for b in blocks:
            if b["kind"] == "room": detail = True
            elif b["kind"] == "line" and SP["is_totals"](b["toks"]) and not (sect and is_section_totals(b["toks"])):
                detail = True
        if detail: detail_pages.append(pno)
    if detail_pages:
        lo, hi = min(detail_pages), max(detail_pages); detail_set = set(range(lo, hi + 1))
    else:
        detail_set = set()
    for pno in sorted(detail_set):
        for b in page_blk.get(pno, []):
            if b["kind"] == "item":
                n = int(re.match(r'^(\d+)', b["first"]).group(1)); item_page.setdefault(n, pno)
            elif b["kind"] == "line" and SP["is_totals"](b["toks"]) and not (sect and is_section_totals(b["toks"])):
                rm = SP["totals_room"](b["toks"])
                if rm: totals_anchors.append((pno, rm.split()[0]))     # anchor key = first word of the room name
            elif b["kind"] == "room":
                title = []
                for t in b["toks"]:
                    if t.startswith(SP["room_marker"]): break
                    title.append(t)
                if title: room_anchors.append((pno, title))
    breakdown = [min(detail_pages), max(detail_pages) + 1] if detail_pages else [0, C.page_count]
    diagrams = [pno for pno in range(breakdown[1], C.page_count) if C[pno].get_images() and len(C[pno].get_text()) < 300]
    diag_range = [min(diagrams), max(diagrams) + 1] if diagrams else [C.page_count, C.page_count]
    return {"item_page": item_page, "totals": totals_anchors, "rooms": room_anchors,
            "pages": {"breakdown": breakdown, "diagrams": diag_range, "header_template": breakdown[0]}}

def words_on_item(C, item, idx, SP):
    pno = idx["item_page"].get(item)
    if pno is None: return None, []
    words = C[pno].get_text("words")
    tok = SP["item_token"] % item
    ts = [w[1] for w in words if w[4] == tok and w[0] < 60]
    if not ts: return pno, []
    t = ts[0]
    nxt = sorted(w[1] for w in words if SP["item_re"].match(w[4]) and w[0] < 60 and w[1] > t + 4)
    bot = nxt[0] if nxt else t + 30
    return pno, [w for w in words if t - 2 <= w[1] < bot]

def run_found(blk, target):
    tk = target.split(); n = len(tk)
    row = sorted(blk, key=lambda w: (round(w[1]), w[0]))
    for i in range(len(row) - n + 1):
        if [s[4] for s in row[i:i + n]] == tk:
            return True
    return False

# ---------- prose extraction (format-independent) ----------
UNIT = r'(?:LF|SF|SY|CY|EA|HR|DA|WK|MO|GAL|RM)'
def extract_swaps(prop):
    swaps = []
    for m in re.finditer(r'(\d+(?:\.\d+)?)\s*' + UNIT + r'?\s+(?:toward|to)\s+(\d+(?:\.\d+)?)', prop):
        swaps.append((m.group(1), m.group(2)))
    for m in re.finditer(r'"?(\d(?:\s*\d/\d)?\s*")"?\s*(?:→|->|—>)\s*"?([A-Za-z][A-Za-z ]*?)"?(?=[\s,.;)]|$)', prop):
        swaps.append((m.group(1).strip(), m.group(2).strip()))
    for m in re.finditer(r'(\d+(?:\.\d+)?)\s*(?:→|->)\s*(\d+(?:\.\d+)?)', prop):
        swaps.append((m.group(1), m.group(2)))
    seen = set(); out = []
    for s in swaps:
        if s not in seen: seen.add(s); out.append(s)
    return out

def extract_desc(prop):
    m = re.search(r'[Uu]pgrade(?:\s+grade)?\s+to\s+"([^"]+)"', prop) or re.search(r'[Uu]pgrade to\s+"([^"]+)"', prop)
    return m.group(1) if m else None

def extract_room_name(prop):
    m = re.search(r'Add (?:room |grounds |space )?"([^"]+)"', prop)
    if m:
        name = m.group(1)
        lvl = re.search(r'"\s*\(([^)]+)\)', prop)
        if lvl and lvl.group(1) not in name: name = "%s (%s)" % (name, lvl.group(1))
        return name
    m = re.search(r'Add (?:room )?([A-Z][^,(]+?)\s+to the', prop)
    return m.group(1).strip() if m else None

def extract_cells(prop):
    cells = []
    mq = re.search(r'(\d+(?:\.\d+)?)\s*(' + UNIT + r')\b', prop)
    if mq: cells.append(["qty", "%s %s" % (mq.group(1), mq.group(2))])
    mp = re.search(r'\$?(\d+(?:\.\d+)?)\s*/\s*' + UNIT, prop)
    if mp: cells.append(["unit_price", mp.group(1)])
    return cells

def parse_dims(prop):                                      # "Dimensions [Length: 5'2"; Width: 4'0"; ...]" -> {label: value}
    m = re.search(r'Dimensions\s*\[([^\]]+)\]', prop, flags=re.I)
    if not m: return {}
    out = {}
    for part in m.group(1).split(";"):
        if ":" in part:
            k, v = part.split(":", 1); out[k.strip()] = v.strip()
    return out
def _feet(v):                                              # "5'2"" -> 5.17 ; "8'" -> 8.0 ; "12.5" -> 12.5
    m = re.search(r"(\d+)\s*'\s*(\d+)?", v)
    if m: return round(int(m.group(1)) + (int(m.group(2)) / 12.0 if m.group(2) else 0.0), 3)
    m2 = re.search(r"([\d.]+)", v); return float(m2.group(1)) if m2 else 0.0
def parse_diagram(prop, dims):                             # a sketch is drawn only if asked for AND Length+Width are given in the list
    if not re.search(r'sketch|diagram|drawing', prop, flags=re.I): return None
    if "Length" not in dims or "Width" not in dims: return None   # the interpreter never derives — the footprint must be in the suggestion list
    return {"length_ft": _feet(dims["Length"]), "width_ft": _feet(dims["Width"]),
            "label": "%s x %s" % (dims["Length"], dims["Width"])}

def resolve_anchor(cline, idx):
    mi = re.search(r'item\s+(\d{1,4})', cline, flags=re.I)
    if mi and re.search(r'\bitem\b', cline, flags=re.I):
        return {"type": "item", "item": int(mi.group(1))}, "item %s" % mi.group(1)
    mp = re.search(r'p\.?\s*(\d+)', cline); N = int(mp.group(1)) - 1 if mp else None
    ma = re.search(r'after\s+(?:the\s+)?(.+?)\s*\(carrier', cline)
    phrase = (ma.group(1) if ma else cline).lower()
    tc = [(pno, room) for (pno, room) in idx["totals"] if room.lower() in phrase]
    if tc:
        pno, room = min(tc, key=lambda x: (abs(x[0] - (N if N is not None else x[0])), -(x[0] >= (N or 0))))
        return {"type": "totals", "pno": pno, "room": room}, "totals '%s' p%d" % (room, pno + 1)
    rc = [(pno, title) for (pno, title) in idx["rooms"] if any(t.lower() in phrase for t in title)]
    if rc:
        pno, title = min(rc, key=lambda x: abs(x[0] - (N if N is not None else x[0])))
        return {"type": "room", "pno": pno, "match": title[0]}, "room '%s' p%d" % (title[0], pno + 1)
    return None, "UNRESOLVED"

# ---------- main ----------
def main():
    if len(sys.argv) < 4:
        sys.exit("Usage: python3 interpret.py <suggestion-list.md> <carrier.pdf> <out-plan.json> [--truth plan.json]")
    SUG, PDF, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
    truth = json.load(open(sys.argv[sys.argv.index("--truth") + 1], encoding="utf-8")) if "--truth" in sys.argv else None
    C = fitz.open(PDF)
    SP = detect_format(C)
    idx = build_index(C, SP)
    rows = parse_table(SUG)

    corrects = []; adds_by_item = {}; new_rooms = []; excluded = []; review = []
    def cited_item(row):
        for fld in (row.get("carrier line", ""), row.get("label", "")):
            m = re.search(r'[Ii]tem\s+(\d{1,4})', fld) or re.search(r'^\s*(\d{1,4})b', fld)
            if m: return int(m.group(1))
        return None
    def is_room_creation(prop, cline):                     # creates a new folder (vs. an item that belongs to one)
        if re.search(r'\bAdd\s+(?:a\s+)?(?:room|grounds|space)\b', prop, flags=re.I):
            return True                                     # explicit room creation (may carry dimensions, which look like cells)
        # implicit: the carrier line flags a new room/space and the row is not an item (no qty/unit cells)
        return bool(re.search(r'\bnew\s+(?:room|grounds|space)\b', cline, flags=re.I)) and not extract_cells(prop)
    def base_name(nm):                                     # "Storage Closet (Main Level)" -> "storage closet"
        return nm.split(" (")[0].strip().lower()

    # PASS 1 — create the new rooms first, so add-rows in PASS 2 can attach their items by room name
    nr_by_name = {}; creation_rows = set()
    for ri, row in enumerate(rows):
        if row.get("disposition", "").lower() != "agreed" or row.get("suggestion type", "").lower() != "add": continue
        prop = row.get("proposed change", ""); cline = row.get("carrier line", "")
        if not is_room_creation(prop, cline): continue
        creation_rows.add(ri)
        num = row.get("#", "?"); cline = row.get("carrier line", "")
        name = extract_room_name(prop); anchor, how = resolve_anchor(cline, idx)
        dims = parse_dims(prop); diagram = parse_diagram(prop, dims)
        nr = {"name": name or "[ROOM NAME]", "anchor": anchor or {"type": "UNRESOLVED"},
              "reason": row.get("supporting evidence", ""), "dims": dims, "diagram": diagram,
              "suggestion": int(num) if num.isdigit() else num, "items": []}
        new_rooms.append(nr)
        if name: nr_by_name[base_name(name)] = nr
        flags = []
        if not name: flags.append("could not extract room name from 'Proposed change'")
        if not anchor: flags.append("could not resolve anchor from 'Carrier line': %r" % cline)
        review.append((num, "New-room", flags or ["anchor -> %s (confirm)" % how]))

    for ri, row in enumerate(rows):
        num = row.get("#", "?"); typ = row.get("suggestion type", "").lower()
        disp = row.get("disposition", "").lower()
        reason = row.get("supporting evidence", "")
        prop = row.get("proposed change", ""); cline = row.get("carrier line", ""); label = row.get("label", "")
        if disp != "agreed":
            excluded.append((num, "disposition=%s" % (row.get("disposition") or "(blank)"))); continue
        if typ == "flag":
            excluded.append((num, "Flag — resolve before render (rewrite as Add/Correct if accepted)")); continue

        if typ == "correct":
            item = cited_item(row)
            swaps = extract_swaps(prop); desc = extract_desc(prop)
            e = {"item": item, "reason": reason, "suggestion": int(num) if num.isdigit() else num}
            flags = []
            if item is None: flags.append("no carrier item found in 'Carrier line'")
            elif item not in idx["item_page"]: flags.append("item %d not found in PDF" % item)
            if swaps:
                e["swaps"] = [list(s) for s in swaps]
                pno, blk = words_on_item(C, item, idx, SP) if item else (None, [])
                for old, _new in swaps:
                    if blk and not run_found(blk, old):
                        flags.append("swap old-value %r not found on item %s line" % (old, item))
            elif desc:
                e["desc"] = [[desc, "g"]]; flags.append("desc rewrite: confirm which part is green (defaulted whole-green)")
            else:
                flags.append("could not extract a swap or desc from 'Proposed change'")
            corrects.append(e)
            if flags: review.append((num, "Correct", flags))

        elif typ == "add":
            if ri in creation_rows: continue               # the room itself — already created in PASS 1
            pr = next((nm for nm in nr_by_name if nm in cline.lower()), None)
            if pr:                                          # an item belonging to a CCS-added new room
                room = nr_by_name[pr]; cells = extract_cells(prop); flags = []
                if not cells: flags.append("no quantity/unit found in 'Proposed change'")
                flags.append("add description wording is interpretive — confirm desc text")
                room["items"].append(
                    {"label": label or ("Supp-%d" % (len(room["items"]) + 1)), "desc": "[CONFIRM DESC]",
                     "cells": cells, "reason": reason, "suggestion": int(num) if num.isdigit() else num})
                review.append((num, "New-room item", flags + ["-> room '%s'" % room["name"]]))
            else:                                           # an add anchored to an existing carrier item
                parent = cited_item(row)
                cells = extract_cells(prop)
                flags = []
                if parent is None: flags.append("no parent carrier item found")
                elif parent not in idx["item_page"]: flags.append("parent item %d not found in PDF" % parent)
                if not cells: flags.append("no quantity/unit found in 'Proposed change'")
                flags.append("add description wording is interpretive — confirm desc text")
                adds_by_item.setdefault(parent, []).append(
                    {"label": label or ("%sb" % parent), "desc": "[CONFIRM DESC]", "cells": cells,
                     "reason": reason, "suggestion": int(num) if num.isdigit() else num})
                review.append((num, "Add", flags))
        else:
            excluded.append((num, "unknown type %r" % typ))

    plan = {"carrier_pdf": os.path.basename(PDF), "format": SP["name"], "company_name": "Construction Claim Services",
            "pages": idx["pages"], "cover": True,
            "corrects": corrects,
            "adds": [{"item": it, "lines": ls} for it, ls in adds_by_item.items()],
            "new_rooms": new_rooms}
    json.dump(plan, open(OUT, "w"), indent=1, ensure_ascii=False)

    # ---------- report ----------
    print("=" * 70)
    print("INTERPRETED:", os.path.basename(SUG), "->", os.path.basename(OUT), "  [format: %s]" % SP["name"])
    print("  pages: breakdown %s  diagrams %s  header p%d"
          % (idx["pages"]["breakdown"], idx["pages"]["diagrams"], idx["pages"]["header_template"] + 1))
    print("  corrects: %d   add-lines: %d   new-rooms: %d (with %d item(s))   excluded: %d"
          % (len(corrects), sum(len(v) for v in adds_by_item.values()), len(new_rooms),
             sum(len(r["items"]) for r in new_rooms), len(excluded)))
    print("-" * 70); print("EXCLUDED (not rendered):")
    for n, why in excluded: print("  #%s — %s" % (n, why))
    print("-" * 70); print("REVIEW (auto-filled; confirm before render):")
    print("  [pages] breakdown %s, diagrams %s — confirm against the PDF" % (idx["pages"]["breakdown"], idx["pages"]["diagrams"]))
    for n, kind, flags in review:
        for fl in flags: print("  #%s [%s] %s" % (n, kind, fl))

    if truth:
        print("=" * 70); print("COMPARE vs ground truth:")
        tc = {c["item"]: c for c in truth["corrects"]}
        for c in corrects:
            t = tc.get(c["item"])
            if not t: print("  correct item %s: NOT in truth" % c["item"]); continue
            got = c.get("swaps") or c.get("desc"); exp = t.get("swaps") or t.get("desc")
            print("  correct item %s: %s" % (c["item"], "MATCH" if got == exp else "DIFFER got=%s exp=%s" % (got, exp)))
        tbysug = {t.get("suggestion"): t for t in truth["new_rooms"]}
        for r in new_rooms:
            tn = tbysug.get(r.get("suggestion")); a = r["anchor"]; ta = tn["anchor"] if tn else None
            print("  new-room #%s %r: %s" % (r.get("suggestion"), r["name"].split(" (")[0],
                  "MATCH" if a == ta else "DIFFER got=%s exp=%s" % (a, ta)))

if __name__ == "__main__":
    main()

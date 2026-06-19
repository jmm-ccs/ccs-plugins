#!/usr/bin/env python3
"""CCS PDF Viewer - local MCP server (pure standard library, no pip install).

Exposes read-only tools that let an in-app viewer render any local PDF
WITHOUT relying on the host app's built-in PDF panel:

  - list_pdfs(directory?)      -> list local PDF files under allowed roots
  - read_pdf_base64(path)      -> return a PDF's bytes as base64 for rendering

Transport: MCP stdio (newline-delimited JSON-RPC 2.0). Only valid JSON-RPC
messages are ever written to stdout; all diagnostics go to stderr.

Allowed roots default to ~/Documents, ~/Downloads, ~/Desktop and can be
overridden with the CCS_PDF_ROOTS environment variable (os.pathsep-separated).
Reads are confined to those roots.
"""

import base64
import json
import os
import sys
import time

SERVER_NAME = "ccs-pdf-viewer"
SERVER_VERSION = "0.1.0"
DEFAULT_PROTOCOL = "2025-06-18"
MAX_BYTES = 80 * 1024 * 1024  # 80 MB guard on a single read
MAX_LIST = 500  # cap directory listings


def log(*a):
    print("[ccs-pdf-viewer]", *a, file=sys.stderr, flush=True)


def allowed_roots():
    env = os.environ.get("CCS_PDF_ROOTS", "").strip()
    if env:
        roots = [p for p in env.split(os.pathsep) if p]
    else:
        home = os.path.expanduser("~")
        roots = [os.path.join(home, d) for d in ("Documents", "Downloads", "Desktop")]
    out = []
    for r in roots:
        try:
            out.append(os.path.realpath(r))
        except Exception:
            pass
    return out


def within_roots(path, roots):
    try:
        rp = os.path.realpath(path)
    except Exception:
        return None
    for root in roots:
        if rp == root or rp.startswith(root + os.sep):
            return rp
    return None


def do_list_pdfs(args):
    roots = allowed_roots()
    directory = (args or {}).get("directory")
    scan_dirs = []
    if directory:
        base = within_roots(directory, roots)
        if not base:
            return _err_text(
                "Directory is outside the allowed roots. Allowed: "
                + ", ".join(roots)
                + ". Set CCS_PDF_ROOTS to add locations."
            )
        scan_dirs = [base]
    else:
        scan_dirs = [r for r in roots if os.path.isdir(r)]

    found = []
    for base in scan_dirs:
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for fn in filenames:
                if fn.lower().endswith(".pdf"):
                    full = os.path.join(dirpath, fn)
                    try:
                        st = os.stat(full)
                    except OSError:
                        continue
                    found.append({
                        "path": full,
                        "name": fn,
                        "size": st.st_size,
                        "modified": time.strftime(
                            "%Y-%m-%d %H:%M", time.localtime(st.st_mtime)
                        ),
                    })
                    if len(found) >= MAX_LIST:
                        break
            if len(found) >= MAX_LIST:
                break

    found.sort(key=lambda x: x["modified"], reverse=True)
    summary = "Found %d PDF(s)%s." % (
        len(found),
        " (capped at %d)" % MAX_LIST if len(found) >= MAX_LIST else "",
    )
    return {
        "content": [{"type": "text", "text": summary}],
        "structuredContent": {"count": len(found), "pdfs": found, "roots": roots},
    }


def do_read_pdf_base64(args):
    roots = allowed_roots()
    path = (args or {}).get("path")
    if not path:
        return _err_text("Missing required argument 'path'.")
    if not path.lower().endswith(".pdf"):
        return _err_text("Path is not a .pdf file: %s" % path)
    rp = within_roots(path, roots)
    if not rp:
        return _err_text(
            "Path is outside the allowed roots. Allowed: "
            + ", ".join(roots)
            + ". Set CCS_PDF_ROOTS to add locations."
        )
    if not os.path.isfile(rp):
        return _err_text("File not found: %s" % rp)
    size = os.path.getsize(rp)
    if size > MAX_BYTES:
        return _err_text(
            "PDF is %.1f MB, larger than the %d MB limit for a single read."
            % (size / 1048576.0, MAX_BYTES // 1048576)
        )
    try:
        with open(rp, "rb") as f:
            data = f.read()
    except OSError as e:
        return _err_text("Could not read file: %s" % e)
    b64 = base64.b64encode(data).decode("ascii")
    name = os.path.basename(rp)
    return {
        "content": [{
            "type": "text",
            "text": "Loaded %s (%.1f KB) as base64." % (name, size / 1024.0),
        }],
        "structuredContent": {
            "path": rp,
            "name": name,
            "size": size,
            "mime": "application/pdf",
            "base64": b64,
        },
    }


def _err_text(msg):
    return {"content": [{"type": "text", "text": msg}], "isError": True}


TOOLS = [
    {
        "name": "list_pdfs",
        "description": (
            "List local PDF files available to open in the viewer. Optionally "
            "restrict to a directory (must be within the allowed roots). Returns "
            "path, name, size and modified date for each PDF, newest first."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Absolute directory to scan recursively. "
                    "Omit to scan all allowed roots.",
                }
            },
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": False},
    },
    {
        "name": "read_pdf_base64",
        "description": (
            "Return the bytes of a local PDF as base64 so the viewer can render "
            "it client-side. Path must be within the allowed roots and end in .pdf."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path to the .pdf file to load.",
                }
            },
            "required": ["path"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": False},
    },
]

HANDLERS = {"list_pdfs": do_list_pdfs, "read_pdf_base64": do_read_pdf_base64}


def send(obj):
    sys.stdout.write(json.dumps(obj, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def reply(req_id, result):
    send({"jsonrpc": "2.0", "id": req_id, "result": result})


def reply_error(req_id, code, message):
    send({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}})


def handle(msg):
    method = msg.get("method")
    req_id = msg.get("id")

    if method == "initialize":
        params = msg.get("params") or {}
        proto = params.get("protocolVersion") or DEFAULT_PROTOCOL
        reply(req_id, {
            "protocolVersion": proto,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        })
        return

    if method == "notifications/initialized" or method == "initialized":
        return  # notification, no response

    if method == "ping":
        reply(req_id, {})
        return

    if method == "tools/list":
        reply(req_id, {"tools": TOOLS})
        return

    if method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name")
        args = params.get("arguments") or {}
        fn = HANDLERS.get(name)
        if not fn:
            reply_error(req_id, -32602, "Unknown tool: %s" % name)
            return
        try:
            reply(req_id, fn(args))
        except Exception as e:  # never crash the loop
            log("tool error:", repr(e))
            reply(req_id, _err_text("Tool failed: %s" % e))
        return

    if req_id is not None:
        reply_error(req_id, -32601, "Method not found: %s" % method)


def main():
    log("started; roots =", allowed_roots())
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError as e:
            log("bad json:", e)
            continue
        try:
            handle(msg)
        except Exception as e:
            log("handler crash:", repr(e))
    log("stdin closed; exiting")


if __name__ == "__main__":
    main()

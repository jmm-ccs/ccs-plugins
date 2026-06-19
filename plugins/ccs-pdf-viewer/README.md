# ccs-pdf-viewer

A small local MCP connector that lets an interactive in-app viewer render any
local PDF **without** the host app's built-in PDF panel (which fails to mount on
some machines). The connector only reads files and hands their bytes to the
viewer; all rendering happens client-side via pdf.js.

## Why this exists

The built-in PDF viewer mounts an on-screen iframe that, on some setups, never
finishes loading ("viewer never connected / no poll"). That failure is in the
app's panel rendering, not in any connector. This connector sidesteps it: it
serves PDF bytes, and the viewer renders them on a surface that does work.

## Tools

| Tool | Purpose |
| --- | --- |
| `list_pdfs(directory?)` | List local PDFs (path, name, size, modified), newest first. Optional `directory` must be inside an allowed root. |
| `read_pdf_base64(path)` | Return a PDF's bytes as base64 for client-side rendering. Path must be inside an allowed root and end in `.pdf`. |

## Requirements

- macOS `python3` (standard library only — **no `pip install`**). The manifest
  invokes `/usr/bin/python3`. If your Python lives elsewhere, edit
  `command` in `.claude-plugin/plugin.json`.

## Allowed roots (where it can read)

By default the connector can read PDFs under:

- `~/Documents` (covers `~/Documents/Claude/Projects/...`)
- `~/Downloads`
- `~/Desktop`

Override with the `CCS_PDF_ROOTS` environment variable
(`os.pathsep`-separated absolute paths) in the `mcpServers.ccs-pdf-viewer.env`
block of `plugin.json`. Reads outside the allowed roots — and `../` traversal —
are refused.

## Install

1. This plugin ships in the `ccs-plugins` marketplace. With that marketplace
   added, enable **ccs-pdf-viewer** from the plugin list.
2. Approve the `ccs-pdf-viewer` MCP server when prompted.
3. Confirm the tools `list_pdfs` and `read_pdf_base64` appear, then open the
   interactive viewer.

## Security

Read-only. No writes, no network, no shell. Path access is confined to the
allowed roots above.

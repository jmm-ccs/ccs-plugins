# CCS Plugins — Cowork marketplace

Private plugin marketplace for Construction Claim Services. Hosts the **forensic-claim-audit** plugin (13-stage supplement audit + finalizer, PDF annotator, inventory, and export utilities).

## For teammates — install in Claude Cowork

You need access to this (private) repository first. Then:

1. Open the Claude desktop app → **Cowork** tab.
2. Add this marketplace, then install the plugin (plugin command line):

   ```
   /plugin marketplace add YOUR-GITHUB-ORG/ccs-plugins
   /plugin install forensic-claim-audit@ccs-plugins
   ```

   Replace `YOUR-GITHUB-ORG/ccs-plugins` with the real repo path once it's pushed.
3. The audit skills then appear under `/` in any Cowork chat.

## For the maintainer — publishing updates

The plugin lives at `plugins/forensic-claim-audit/`. To ship a change:

1. Edit files under `plugins/forensic-claim-audit/`.
2. **Bump `"version"` in `plugins/forensic-claim-audit/.claude-plugin/plugin.json`** (e.g. `0.1.0` -> `0.1.1`). Teammates only receive an update when the version string changes.
3. Commit and push.
4. Teammates run `/plugin marketplace update ccs-plugins` to pull it.

> Prefer auto-updates on every commit? Remove the `"version"` field from the plugin's `plugin.json`; Claude then uses the git commit as the version.

## Structure

    ccs-plugins/
    |- .claude-plugin/
    |  \- marketplace.json          # the catalog (lists the plugin)
    \- plugins/
       \- forensic-claim-audit/     # the plugin itself
          |- .claude-plugin/plugin.json
          |- skills/                # 21 skills
          \- README.md

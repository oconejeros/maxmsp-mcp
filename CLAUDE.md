# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# MaxMSP MCP Server

This project has two distinct halves:

1. **The MCP server itself** (`server.py` + `MaxMSP_Agent/`) — an extended fork of
   [MaxMSP-MCP-Server](https://github.com/tiianhk/MaxMSP-MCP-Server) that lets an LLM manipulate a
   live-open Max patch over Socket.IO.
2. **The FORTESEQ devices** (`forteseq/`) — a suite of Max for Live devices built *using* that MCP
   server, plus a large library of one-off Python scripts (`tools/`) that edit the compiled
   `.amxd` files directly on disk for things the MCP/live-patch route can't reach.

Most day-to-day work in this repo is #2. Read the right section below before touching either.

## Critical Rule for Max patch work

**Run the `/maxmsp` skill before creating or modifying patches** (live, via the MCP) — it contains
placement rules, object gotchas, and tool usage guidelines that MUST be followed.

### Quick reminders (details in skill)

- **CONSIDER SUBPATCHERS** for new functionality!
- **NO OVERLAP**: Always call `get_avoid_rect_position()` before placing objects
- **Message boxes**: Use numbers `[200, 0, 50]` not strings `["200", "0", "50"]`
- **Auto-sizing**: Objects & comments auto-size; messages fixed 70px; UI objects keep defaults

### Required flags on MCP tool calls

- **Math/pack/unpack**: JSON strips `.0` from numbers. Use STRING args to preserve floats: `["0", "127", "0", "25."]`. Use `["f", "f", "f"]` for unpack. Set `int_mode=True` to explicitly allow integers. Exception: `scale` with output range ≤ 2 auto-detects float intent.
- **dial**: Use `dial` with `@size` attribute instead of `live.dial` (set `use_live_dial=True` to bypass)
- **trigger/t**: Set `trigger_rtl=True` — fires right-to-left (`[t b f]` sends `f` first)
- **random**: Set `random_bang=True` — numbers set range, bangs trigger output (use `[t b]` to convert)
- **coll**: Always include `@embed 1` to persist data on save

## Architecture — MCP server

```
Claude Code (MCP Client) ←Socket.IO(:5002)→ server.py (FastMCP/Python)
                                                   │
                                          max_mcp_node.js (Node.js bridge, runs inside Max's node.script)
                                                   │
                              ┌────────────────────┴────────────────────┐
                       max_mcp.js (Max js object,              max_mcp_v8_add_on.js
                       most operations)                        (V8, `obj.boxtext` access
                                                                 for encapsulation)
```

- `server.py` — FastMCP tool definitions, Socket.IO server, and validation (float enforcement,
  dial/trigger/random/coll acknowledgment flags, signal-safety checks). This is where new MCP
  tools get added.
- `MaxMSP_Agent/max_mcp.js` — main Max-side JS handler for object creation/query/connection.
- `MaxMSP_Agent/max_mcp_v8_add_on.js` — separate V8 JS runtime, used specifically where
  `boxtext` access is needed (encapsulation).
- `MaxMSP_Agent/demo.maxpat` — the Max patch that hosts `node.script` and the two JS objects;
  open this in Max and click `script start` to bring the bridge up.

**After changing `server.py` or the `MaxMSP_Agent/*.js` files**: reload the js objects in Max
(double-click to open the editor, then close it) and restart `node.script` (`script stop`, then
`script start`) inside `demo.maxpat`.

### Running the server

```bash
uv venv
source .venv/bin/activate        # or the Windows equivalent
uv pip install -r requirements.txt
```

Registered with Claude Code via `claude mcp add --scope user maxmsp -- uv --directory <repo> run server.py`
(not via `mcpServers` in settings.json — that key stopped being read as of Claude Code v2.1.47).
There is no test suite or lint config in this repo; validate MCP tool changes by exercising them
against a live Max patch.

## Architecture — FORTESEQ devices (`forteseq/`)

`forteseq/` holds the Max for Live devices and the JS engines they load, in one folder because
`FORTESEQ.amxd` (and siblings) reference their engine by bare filename (e.g. `js pcset351.js`) and
Max resolves bare filenames from the patcher's own folder first. Live reaches them through a Place
pointing at that folder, so **these files are the ones Live actually loads** — there is no second
copy in the Ableton User Library, and edits here take effect directly.

Two consequences worth remembering:

- Saving a device from inside Live writes straight to `forteseq/<Device>.amxd`, so `git diff` will
  show changes made through the Live UI, not just through tooling.
- A `.js` added as a new device dependency must go in `forteseq/`, next to the `.amxd`. Dropping it
  in `MaxMSP_Agent/` (the MCP server's own Max-side code, unrelated) is a silent no-op — Max
  reports no error, the dependency is just never found.

### `tools/` — direct `.amxd` file editing

Most structural work on FORTESEQ/EVENFLOW/ANIMIDI/etc. (adding tabs, params, panels, controls,
wiring) is **not** done live through the MCP — it's done by one-off Python scripts in `tools/`
that parse and rewrite the device file's embedded JSON patcher graph directly. This exists because
several things are unreachable from the MCP/live-patch route: Live's parameter metadata (names,
ranges, bank membership), presentation-mode flags, comment text, and the `.amxd` container format
itself.

- **`tools/amxd.py`** is the shared library every other `tools/*.py` script imports. It knows the
  AMPF container layout (`amxd.load(path)` → `(data, start, end, doc)`; mutate
  `doc['patcher']['boxes'] / ['lines'] / ['parameters']`; `amxd.save(...)` rewrites the length
  header). Read its module docstring before writing a new script — it also explains the three
  places a Live parameter's metadata must agree (see `[[amxd_parameter_registries]]`-style note in
  memory) and why a malformed write fails *silently* in Live rather than erroring.
- Every `tools/*.py` script name describes its one job (`add_*` = new control/panel, `fix_*` =
  targeted bug fix, `build_*` = generates a whole device, `repage_*`/`migrate_*` = UI
  reorganization). They are **not** reusable modules — each is a standalone, single-use migration,
  kept around as a record of what was done, not meant to be re-run.
- Convention across these scripts: dry-run by default, real write behind `--apply`
  (e.g. `python tools/fix_device_height.py --apply`), and a `.before` backup copy of the device
  written just before the real write.
- **`tools/check_structure.py <file.amxd|.maxpat> [...]`** validates the low-level JSON graph
  integrity (unique box ids, patchline endpoints resolve to real boxes, inlet/outlet indices in
  range) — run it after any script that touches `boxes`/`lines`. It recurses into subpatchers but
  has no notion of the rendered viewport, so it will not catch presentation-mode clipping (content
  placed below the device's `openrect` height) — that only shows up by opening the device in Live.
- **`tools/check_params3.py`** validates Live parameter registries, but does not work on devices
  built with an inline subpatcher rather than a bpatcher (e.g. `invertedprism.amxd`).
- **Always edit with the target device closed in both Max and Live** — whichever app saves last
  silently overwrites the other's changes.
- `device_backup/` and the `forteseq/*.amxd.bak-*` / `*.before` files are point-in-time safety
  copies made before risky edits — not build artifacts, don't delete them casually.

### Other top-level directories

- `release/`, `landing/`, `sales/` — packaging and go-to-market material for shipping FORTESEQ/
  EVENFLOW/ANIMIDI/etc. as products (Payhip). `tools/package_release.py` and `tools/make_lite.py`
  build release/Lite variants from the working devices in `forteseq/`.
- `docs/`, `docs.json` — reference documentation (e.g. Max object docs) consumed by the
  `get_object_doc` MCP tool, not hand-maintained prose.

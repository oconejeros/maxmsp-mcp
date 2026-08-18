# MaxMSP MCP Server

This project provides MCP tools for programmatic Max/MSP patch manipulation.

## Critical Rules

**Run `/maxmsp` skill before creating or modifying patches** - it contains all placement rules, object gotchas, and tool usage guidelines that MUST be followed.

### Quick Reminders (details in skill)

- **CONSIDER SUBPATCHERS** for new functionality!
- **NO OVERLAP**: Always call `get_avoid_rect_position()` before placing objects
- **Message boxes**: Use numbers `[200, 0, 50]` not strings `["200", "0", "50"]`
- **Auto-sizing**: Objects & comments auto-size; messages fixed 70px; UI objects keep defaults

### Required Flags

- **Math/pack/unpack**: JSON strips `.0` from numbers. Use STRING args to preserve floats: `["0", "127", "0", "25."]`. Use `["f", "f", "f"]` for unpack. Set `int_mode=True` to explicitly allow integers. Exception: `scale` with output range ≤ 2 auto-detects float intent.
- **dial**: Use `dial` with `@size` attribute instead of `live.dial` (set `use_live_dial=True` to bypass)
- **trigger/t**: Set `trigger_rtl=True` - fires right-to-left (`[t b f]` sends `f` first)
- **random**: Set `random_bang=True` - numbers set range, bangs trigger output (use `[t b]` to convert)
- **coll**: Always include `@embed 1` to persist data on save

## MCP Tools

Key tools for object manipulation:
- `get_avoid_rect_position()` - Get bounding box before placing
- `add_max_object()` - Create object (auto-fits width)
- `recreate_with_args()` - Change creation-time args, preserving connections
- `move_object()` - Reposition object
- `autofit_existing()` - Apply auto-fit to existing object

## Architecture

- `server.py` - Python FastMCP server with Socket.IO
- `MaxMSP_Agent/max_mcp.js` - Main Max-side JavaScript handler
- `MaxMSP_Agent/max_mcp_v8_add_on.js` - V8 JavaScript with `obj.boxtext` access

**After code changes**: Reload js objects in Max (double-click to open editor, then close) and restart node.script (`script stop`, `script start`).

## The FORTESEQ devices

`forteseq/` holds the Max for Live devices and the JS they load, in one folder because
`FORTESEQ.amxd` references its engine by bare filename (`js pcset351.js`) and Max resolves
bare filenames from the patcher's own folder first. Live reaches them through a Place
pointing at that folder, so **these files are the ones Live actually loads** - there is no
second copy in the Ableton User Library, and edits here take effect directly.

Two consequences worth remembering:

- Saving the device from inside Live writes `forteseq/FORTESEQ.amxd`, so `git diff` will
  show changes you made through the Live UI, not just through the MCP.
- A `.js` added as a new device dependency must go in `forteseq/`, next to the `.amxd`.
  Dropping it in `MaxMSP_Agent/` (which is the MCP server's own Max-side code) will not be
  found, and Max reports that as a silent no-op rather than an error.

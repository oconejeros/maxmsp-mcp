"""Mirror MaxMSP_Agent/*.js into the Max for Live device folder after every edit.

Why this exists: the device references its engine as a bare filename (`js pcset351.js`), and
Max resolves bare filenames from the patcher's own folder FIRST. So the copy that actually runs
is the one sitting next to FORTESEQ.amxd on F:, never the git copy in this repo. Editing the
repo copy and testing in Max produces no change and no error -- a whole session was once spent
chasing that as an autowatch bug.

Runs as a PostToolUse hook on Write|Edit. Reads the hook payload on stdin, and:
  * only touches files under MaxMSP_Agent/ that end in .js
  * only overwrites a destination that ALREADY exists, so the device folder mirrors real
    dependencies instead of collecting new ones. max_mcp.js belongs to the MCP server in
    demo.maxpat, not to the device, and must not be copied there. A genuinely new device
    dependency needs one manual copy first; after that it syncs on its own.
  * never fails the tool call -- a broken sync should be visible, not disruptive.
"""
import json
import shutil
import sys
from pathlib import Path

DEVICE_DIR = Path(r"F:/Ableton/User Library/Presets/MIDI Effects/Max MIDI Effect")


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return

    raw = (payload.get("tool_response") or {}).get("filePath") \
        or (payload.get("tool_input") or {}).get("file_path")
    if not raw:
        return

    src = Path(str(raw).replace("\\", "/"))
    if src.suffix.lower() != ".js" or "MaxMSP_Agent" not in src.parts:
        return
    if not src.is_file():
        return

    dst = DEVICE_DIR / src.name
    if not dst.is_file():
        return                      # not a device dependency; see the note above

    try:
        shutil.copyfile(src, dst)
    except OSError as exc:
        print(json.dumps({"systemMessage": "could not sync %s to the Max device folder: %s"
                                           % (src.name, exc)}))
        return

    print(json.dumps({"systemMessage": "synced %s to the Max device folder" % src.name}))


if __name__ == "__main__":
    main()

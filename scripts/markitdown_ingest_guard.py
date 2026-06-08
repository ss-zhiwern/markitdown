#!/usr/bin/env python3
"""markitdown-liberated ingest guard (Claude Code PreToolUse hook).

When Claude tries to `Read` a rich/binary document (PDF, Office, EPUB, …), this
hook blocks the raw read and tells Claude to convert it through the
`markitdown-liberated` MCP tool instead, so it ingests clean Markdown rather
than raw bytes. Plain-text/code/markup files are left alone.

Wired up automatically by scripts/install.{sh,ps1}. Reads the hook payload as
JSON on stdin and emits a PreToolUse decision as JSON on stdout.
"""

import json
import os
import sys
from pathlib import Path

# Document formats markitdown-liberated converts and that a raw Read handles
# poorly (binary or heavily-structured). Plain text / code / json / etc. are
# intentionally excluded so normal file reading is unaffected.
GUARDED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".doc",
    ".pptx",
    ".ppt",
    ".xlsx",
    ".xls",
    ".epub",
    ".msg",
}


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        # Can't parse the hook payload -> do nothing, let the tool proceed.
        return 0

    if payload.get("tool_name") != "Read":
        return 0

    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    if not file_path:
        return 0

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in GUARDED_EXTENSIONS:
        return 0

    # Build a file:// URI the MCP tool understands (convert_uri only accepts
    # file:, data:, http:, https: schemes -- not bare paths).
    try:
        uri = Path(file_path).resolve().as_uri()
    except Exception:
        uri = "file://" + file_path

    reason = (
        f"'{os.path.basename(file_path)}' is a {ext} document. Do NOT read it as raw "
        f"bytes. Use the markitdown-liberated MCP tool instead:\n\n"
        f"    convert_to_markdown(uri=\"{uri}\")\n\n"
        f"It returns clean Markdown extracted locally (no cloud services), which is "
        f"what you should ingest and reason over."
    )

    decision = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(decision))
    return 0


if __name__ == "__main__":
    sys.exit(main())

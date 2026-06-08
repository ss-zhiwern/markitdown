#!/usr/bin/env python3
"""markitdown-liberated ingest guard (Claude Code PreToolUse hook).

Two jobs:

1. `Read` of any markitdown-supported file -> block the raw read and tell Claude
   to convert it through the `markitdown-liberated` MCP `convert_to_markdown`
   tool instead, so it ingests clean Markdown rather than raw bytes.

2. `WebFetch` of any http/https URL -> block Claude's built-in web fetch and tell
   Claude to fetch+convert through `convert_to_markdown` instead, so web pages
   (HTML, Wikipedia, RSS/Atom, remote PDFs/Office docs, ...) are ingested as
   clean Markdown extracted locally -- never via a cloud service.

Wired up automatically by scripts/install.{sh,ps1}. Reads the hook payload as
JSON on stdin and emits a PreToolUse decision as JSON on stdout.
"""

import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

# The markitdown-liberated converters that handle rich / binary / opaque formats
# a raw `Read` would mangle. A `Read` of any of these is blocked and routed
# through convert_to_markdown so Claude ingests clean Markdown instead of bytes.
#
# Deliberately EXCLUDED (left readable so normal Read/Edit of source + config
# keeps working): the text-ish formats markitdown also supports but Claude reads
# fine on its own -- .html .htm .csv .xml .rss .atom .txt .text .md .markdown
# .json .jsonl. Guarding those would block editing this repo's own files.
# Kept in sync with packages/markitdown-liberated-core/.../converters/*.
GUARDED_EXTENSIONS = {
    # PDF
    ".pdf",
    # Word
    ".docx",
    ".doc",
    # PowerPoint
    ".pptx",
    ".ppt",
    # Excel
    ".xlsx",
    ".xls",
    # E-book
    ".epub",
    # Outlook mail
    ".msg",
    # Images (metadata + OCR)
    ".jpg",
    ".jpeg",
    ".png",
    # Jupyter notebook
    ".ipynb",
    # Archives
    ".zip",
}

# The remaining text-ish formats markitdown-liberated also supports. These are
# NOT guarded by default because Claude reads them fine and guarding them blocks
# normal Read/Edit of source + config (incl. this repo's own .md/.json files).
# They are added to the guarded set ONLY in "guard-all" mode -- enabled by the
# `--all` CLI flag or MARKITDOWN_GUARD_ALL=1 in the environment. Enable it via
# `MARKITDOWN_GUARD_ALL=1 scripts/install.sh` to route literally every supported
# file type through markitdown.
TEXT_EXTENSIONS = {
    # HTML
    ".html",
    ".htm",
    # Tabular
    ".csv",
    # Feeds / XML
    ".xml",
    ".rss",
    ".atom",
    # Plain-text family
    ".txt",
    ".text",
    ".md",
    ".markdown",
    ".json",
    ".jsonl",
}


def guarded_extensions(guard_all: bool) -> set:
    """Extensions to redirect on Read. In guard-all mode, EVERY supported type."""
    return GUARDED_EXTENSIONS | TEXT_EXTENSIONS if guard_all else GUARDED_EXTENSIONS


def _guard_all_enabled() -> bool:
    if "--all" in sys.argv[1:]:
        return True
    return os.environ.get("MARKITDOWN_GUARD_ALL", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


# URL schemes convert_to_markdown can fetch directly. Anything Claude would
# otherwise hand to its built-in WebFetch we redirect here instead.
GUARDED_URL_SCHEMES = {"http", "https"}


def _deny(reason: str) -> int:
    decision = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(decision))
    return 0


def _handle_read(tool_input: dict, guarded: set) -> int:
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    if not file_path:
        return 0

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in guarded:
        return 0

    # Build a file:// URI the MCP tool understands (convert_uri only accepts
    # file:, data:, http:, https: schemes -- not bare paths).
    try:
        uri = Path(file_path).resolve().as_uri()
    except Exception:
        uri = "file://" + file_path

    reason = (
        f"'{os.path.basename(file_path)}' is a {ext} file supported by "
        f"markitdown-liberated. Do NOT read it as raw bytes. Use the MCP tool "
        f"instead:\n\n"
        f'    convert_to_markdown(uri="{uri}")\n\n'
        f"It returns clean Markdown extracted locally (no cloud services), which "
        f"is what you should ingest and reason over."
    )
    return _deny(reason)


def _handle_web_fetch(tool_input: dict) -> int:
    url = tool_input.get("url") or ""
    if not url:
        return 0

    scheme = urlparse(url).scheme.lower()
    if scheme not in GUARDED_URL_SCHEMES:
        return 0

    reason = (
        f"Do NOT use the built-in web fetch for {url} -- it routes through a "
        f"cloud service. Fetch and convert it locally with the "
        f"markitdown-liberated MCP tool instead:\n\n"
        f'    convert_to_markdown(uri="{url}")\n\n'
        f"It downloads the URL and returns clean Markdown extracted locally "
        f"(HTML, Wikipedia, RSS/Atom, remote PDFs/Office docs, ...), which is "
        f"what you should ingest and reason over."
    )
    return _deny(reason)


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        # Can't parse the hook payload -> do nothing, let the tool proceed.
        return 0

    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input") or {}

    if tool_name == "Read":
        return _handle_read(tool_input, guarded_extensions(_guard_all_enabled()))
    if tool_name == "WebFetch":
        return _handle_web_fetch(tool_input)
    return 0


if __name__ == "__main__":
    sys.exit(main())

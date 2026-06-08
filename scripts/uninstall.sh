#!/usr/bin/env bash
#
# Uninstall markitdown-liberated: deregister the MCP server from Claude Code and
# remove the ingest-guard hook. Does not delete the repo or any uv caches.
#
# Usage:  scripts/uninstall.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_CONFIG="$SCRIPT_DIR/markitdown_hook_config.py"
SETTINGS="${CLAUDE_SETTINGS:-$HOME/.claude/settings.json}"
SERVER_NAME="markitdown-liberated"

PY="$(command -v python3 || command -v python || true)"

echo "==> Uninstalling $SERVER_NAME"

# --- 1. deregister the MCP server ---------------------------------------------
if command -v claude >/dev/null 2>&1; then
  claude mcp remove "$SERVER_NAME" -s user >/dev/null 2>&1 \
    && echo "    removed MCP server '$SERVER_NAME'" \
    || echo "    MCP server '$SERVER_NAME' was not registered"
else
  echo "    WARNING: 'claude' not on PATH; skipping MCP deregistration." >&2
fi

# --- 2. remove the ingest-guard hook ------------------------------------------
if [ -n "$PY" ]; then
  "$PY" "$HOOK_CONFIG" uninstall --settings "$SETTINGS"
else
  echo "    WARNING: python not found; could not remove hook from $SETTINGS." >&2
fi

echo "==> Done. Restart Claude Code to apply."

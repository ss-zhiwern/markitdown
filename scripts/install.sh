#!/usr/bin/env bash
#
# Install markitdown-liberated as an MCP server for Claude Code, and wire up the
# ingest-guard hook so documents are automatically routed through it.
#
# Registration is done via the official `claude mcp add` command (not by editing
# config files by hand) so Claude Code records it correctly.
#
# Usage:  scripts/install.sh
#
set -euo pipefail

# --- locate the repo regardless of where this is invoked from -----------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MCP_DIR="$REPO_ROOT/packages/markitdown-liberated"
GUARD="$SCRIPT_DIR/markitdown_ingest_guard.py"
HOOK_CONFIG="$SCRIPT_DIR/markitdown_hook_config.py"
SETTINGS="${CLAUDE_SETTINGS:-$HOME/.claude/settings.json}"
SERVER_NAME="markitdown-liberated"

echo "==> Installing $SERVER_NAME"
echo "    repo:     $REPO_ROOT"

# --- prerequisites ------------------------------------------------------------
need() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: '$1' not found on PATH. $2" >&2; exit 1; }; }
need claude "Install Claude Code: https://docs.claude.com/en/docs/claude-code"
need uv     "Install uv: https://docs.astral.sh/uv/getting-started/installation/"

PY="$(command -v python3 || command -v python || true)"
[ -n "$PY" ] || { echo "ERROR: python3 not found on PATH (needed for the ingest-guard hook)." >&2; exit 1; }

[ -d "$MCP_DIR" ] || { echo "ERROR: cannot find $MCP_DIR" >&2; exit 1; }

# --- 1. register the MCP server (idempotent) ----------------------------------
echo "==> Registering MCP server (user scope) via 'claude mcp add'"
claude mcp remove "$SERVER_NAME" -s user >/dev/null 2>&1 || true
claude mcp add "$SERVER_NAME" -s user -- uv run --directory "$MCP_DIR" "$SERVER_NAME"

# --- 2. pre-warm the uv environment (downloads Python 3.13 + deps once) --------
echo "==> Pre-warming environment (first build can take a minute)"
uv run --directory "$MCP_DIR" "$SERVER_NAME" --help >/dev/null 2>&1 || true

# --- 3. install the ingest-guard hook -----------------------------------------
echo "==> Installing ingest-guard hook into $SETTINGS"
"$PY" "$HOOK_CONFIG" install --command "$PY \"$GUARD\"" --settings "$SETTINGS"

# --- done ---------------------------------------------------------------------
cat <<EOF

==> Done.
    MCP server '$SERVER_NAME' registered (user scope).
    Ingest-guard hook active: Read on PDF/Office/EPUB/MSG is redirected to
    the convert_to_markdown tool automatically.

    NOTE: restart Claude Code (or start a new session) to pick up the server
    and hook. Verify with:  claude mcp list
EOF

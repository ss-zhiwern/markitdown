#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Install markitdown-liberated as an MCP server for Claude Code (Windows / PowerShell),
  and wire up the ingest-guard hook so documents are routed through it automatically.

.DESCRIPTION
  Registration uses the official `claude mcp add` command rather than editing config
  files by hand. Run from anywhere:  pwsh scripts/install.ps1
#>
$ErrorActionPreference = 'Stop'

# --- locate the repo regardless of where this is invoked from -----------------
$ScriptDir  = $PSScriptRoot
$RepoRoot   = (Resolve-Path (Join-Path $ScriptDir '..')).Path
$McpDir     = Join-Path $RepoRoot 'packages/markitdown-liberated'
$Guard      = Join-Path $ScriptDir 'markitdown_ingest_guard.py'
$HookConfig = Join-Path $ScriptDir 'markitdown_hook_config.py'
$Settings   = if ($env:CLAUDE_SETTINGS) { $env:CLAUDE_SETTINGS } else { Join-Path $HOME '.claude/settings.json' }
$ServerName = 'markitdown-liberated'

Write-Host "==> Installing $ServerName"
Write-Host "    repo:     $RepoRoot"

# --- prerequisites ------------------------------------------------------------
function Need($name, $hint) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    Write-Error "'$name' not found on PATH. $hint"; exit 1
  }
}
Need 'claude' 'Install Claude Code: https://docs.claude.com/en/docs/claude-code'
Need 'uv'     'Install uv: https://docs.astral.sh/uv/getting-started/installation/'

$PyCmd = (Get-Command python -ErrorAction SilentlyContinue) `
  ?? (Get-Command python3 -ErrorAction SilentlyContinue)
if (-not $PyCmd) { Write-Error 'python not found on PATH (needed for the ingest-guard hook).'; exit 1 }
$Py = $PyCmd.Source

if (-not (Test-Path $McpDir)) { Write-Error "cannot find $McpDir"; exit 1 }

# --- 1. register the MCP server (idempotent) ----------------------------------
Write-Host "==> Registering MCP server (user scope) via 'claude mcp add'"
& claude mcp remove $ServerName -s user 2>$null | Out-Null
& claude mcp add $ServerName -s user -- uv run --directory $McpDir $ServerName

# --- 2. pre-warm the uv environment (downloads Python 3.13 + deps once) --------
Write-Host '==> Pre-warming environment (first build can take a minute)'
try { & uv run --directory $McpDir $ServerName --help *> $null } catch {}

# --- 3. install the ingest-guard hook -----------------------------------------
# Matcher covers Read (local files) and WebFetch (http/https URLs) so both are
# routed through markitdown-liberated instead of raw reads / built-in web fetch.
#
# By default only rich/binary docs are guarded on Read (text-ish md/json/txt/csv/
# xml/html stay readable so editing source works). Set MARKITDOWN_GUARD_ALL=1 to
# guard LITERALLY EVERY supported file type -- including the text-ish ones. That
# also blocks Claude from Read/Edit of .md/.json/.txt/etc, so use deliberately.
$HookCommand = "$Py `"$Guard`""
if ($env:MARKITDOWN_GUARD_ALL -eq '1' -or $env:MARKITDOWN_GUARD_ALL -eq 'true') {
  $HookCommand = "$HookCommand --all"
  Write-Host '==> MARKITDOWN_GUARD_ALL set: guarding ALL supported types (incl. md/json/txt/csv/xml/html)'
}
Write-Host "==> Installing ingest-guard hook into $Settings"
& $Py $HookConfig install --command $HookCommand --settings $Settings --matcher 'Read|WebFetch'

# --- done ---------------------------------------------------------------------
Write-Host @"

==> Done.
    MCP server '$ServerName' registered (user scope).
    Ingest-guard hook active:
      - Read of a rich/binary document (PDF, Word, PowerPoint, Excel, EPUB,
        MSG, images, ipynb, zip) is redirected to convert_to_markdown.
        (Text-ish formats md/json/txt/csv/xml/html stay directly readable --
         re-run with MARKITDOWN_GUARD_ALL=1 to guard those too.)
      - WebFetch of any http/https URL is redirected to convert_to_markdown so
        web pages are fetched + converted locally (never via cloud web fetch).

    NOTE: restart Claude Code (or start a new session) to pick up the server
    and hook. Verify with:  claude mcp list
"@

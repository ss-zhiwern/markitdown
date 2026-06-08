#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Uninstall markitdown-liberated (Windows / PowerShell): deregister the MCP server
  from Claude Code and remove the ingest-guard hook.

.DESCRIPTION
  Does not delete the repo or any uv caches. Run from anywhere:
    pwsh scripts/uninstall.ps1
#>
$ErrorActionPreference = 'Stop'

$ScriptDir  = $PSScriptRoot
$HookConfig = Join-Path $ScriptDir 'markitdown_hook_config.py'
$Settings   = if ($env:CLAUDE_SETTINGS) { $env:CLAUDE_SETTINGS } else { Join-Path $HOME '.claude/settings.json' }
$ServerName = 'markitdown-liberated'

Write-Host "==> Uninstalling $ServerName"

# --- 1. deregister the MCP server ---------------------------------------------
if (Get-Command claude -ErrorAction SilentlyContinue) {
  try {
    & claude mcp remove $ServerName -s user 2>$null | Out-Null
    Write-Host "    removed MCP server '$ServerName'"
  } catch {
    Write-Host "    MCP server '$ServerName' was not registered"
  }
} else {
  Write-Warning "'claude' not on PATH; skipping MCP deregistration."
}

# --- 2. remove the ingest-guard hook ------------------------------------------
$PyCmd = (Get-Command python -ErrorAction SilentlyContinue) `
  ?? (Get-Command python3 -ErrorAction SilentlyContinue)
if ($PyCmd) {
  & $PyCmd.Source $HookConfig uninstall --settings $Settings
} else {
  Write-Warning "python not found; could not remove hook from $Settings."
}

Write-Host '==> Done. Restart Claude Code to apply.'

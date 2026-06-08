# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

This release forks Microsoft MarkItDown into **markitdown-liberated**: a
cloud-free, local-only build designed to be used primarily as an MCP server for
Claude.

### Added

- MCP installer/uninstaller scripts (`scripts/install.{sh,ps1}`,
  `scripts/uninstall.{sh,ps1}`) that register the server with Claude Code via
  the official `claude mcp add` command (user scope).
- PreToolUse **ingest-guard hook** that redirects `Read` of PDF/Office/EPUB/MSG
  documents to the `convert_to_markdown` MCP tool, with an idempotent
  settings.json merge helper.
- `hook`: ingest-guard now also intercepts `WebFetch`, redirecting every
  `http`/`https` URL to `convert_to_markdown` so web pages are fetched and
  converted locally instead of via the built-in cloud web fetch.
- `hook`: `Read` now guards all rich/binary supported types (PDF, Word,
  PowerPoint, Excel, EPUB, MSG, images, `.ipynb`, `.zip`); opt-in
  `MARKITDOWN_GUARD_ALL=1` extends guarding to every supported type, including
  the text-ish ones (`.html`/`.csv`/`.xml`/`.rss`/`.atom`/`.txt`/`.md`/`.json`).

### Changed

- Renamed `markitdown` → `markitdown-liberated-core` (import
  `markitdown_liberated`, CLI `markitdown-liberated-core`) and `markitdown-mcp`
  → `markitdown-liberated` (module `markitdown_liberated_mcp`, command/server
  `markitdown-liberated`).
- Pinned the runtime to Python 3.13 (onnxruntime wheel availability); the MCP
  server resolves the core engine from local source via `tool.uv.sources`.

### Removed

- Azure Document Intelligence and Azure Content Understanding converters.
- LLM image descriptions (OpenAI) and the `markitdown-ocr` plugin package.
- Cloud audio transcription (Google `recognize_google`); audio support dropped
  entirely.
- YouTube transcript converter (`youtube-transcript-api`).
- The 3rd-party plugin system and the sample plugin.
- Docker packaging (`Dockerfile`, `.dockerignore`, MCP `Dockerfile`).

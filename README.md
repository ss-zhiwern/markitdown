# markitdown-liberated

**A local-only, cloud-free fork of [Microsoft MarkItDown](https://github.com/microsoft/markitdown), packaged primarily as an MCP server for Claude.**

`markitdown-liberated` converts documents (PDF, Office, EPUB, HTML, …) into clean Markdown so an LLM can read and reason over them. It is meant to be used **mainly as an MCP server**: you point Claude at a file, Claude calls the `convert_to_markdown` tool, and gets back well-structured Markdown — all conversion happens **on your machine, with no data sent to any third-party service**.

It exists for one reason: **keep sensitive documents local.** Upstream MarkItDown can route your content to cloud services (Azure, OpenAI, Google). This fork rips all of that out.

## What it does

- Exposes a single MCP tool — `convert_to_markdown(uri)` — over stdio (also HTTP/SSE).
- `uri` may be a `file:`, `data:`, `http:` or `https:` URI.
- Conversion of **local files is fully offline**. Fetching `http(s)`/Wikipedia/Bing/RSS URLs reaches the network only because you explicitly asked for that remote content.
- Ships an **ingest-guard hook** for Claude Code: when Claude tries to `Read` a binary document (PDF/Office/EPUB/MSG), the read is automatically redirected to `convert_to_markdown` so it always ingests Markdown instead of raw bytes.

### Supported formats
PDF · Word (docx) · PowerPoint (pptx) · Excel (xlsx/xls) · EPUB · HTML · Outlook (.msg) · CSV/JSON/XML · ZIP (iterates contents) · images (EXIF metadata) · Wikipedia/Bing/RSS URLs · plain text & code.

## How it differs from Microsoft MarkItDown

| | Microsoft MarkItDown | **markitdown-liberated** |
|---|---|---|
| Azure Document Intelligence | ✅ optional cloud converter | ❌ **removed** |
| Azure Content Understanding | ✅ optional cloud converter | ❌ **removed** |
| LLM image descriptions (OpenAI) | ✅ optional | ❌ **removed** |
| `markitdown-ocr` (LLM vision OCR) | ✅ plugin | ❌ **removed** |
| Audio transcription | ✅ via Google `recognize_google` (cloud) | ❌ **removed entirely** |
| YouTube transcripts | ✅ via `youtube-transcript-api` | ❌ **removed** |
| 3rd-party plugin system | ✅ entry-point plugins | ❌ **removed** (smaller attack surface) |
| Telemetry | none (ONNX telemetry already disabled by `magika`) | none (audited & confirmed) |
| Docker packaging | ✅ Dockerfiles | ❌ removed (runs natively) |
| Primary interface | Python lib / CLI | **MCP server for Claude** (+ lib/CLI) |
| Package name | `markitdown` | engine `markitdown-liberated-core` (`import markitdown_liberated`), server `markitdown-liberated` |

Net effect: the conversion engine is identical for local files, minus every code path that could send your content off-device.

## Install (recommended: as an MCP server)

**Prerequisites**
- [Claude Code](https://docs.claude.com/en/docs/claude-code) (the `claude` CLI)
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) — manages the Python 3.13 runtime and dependencies automatically (the system Python may be too new for some wheels; `uv` handles this for you)

**macOS / Linux**
```bash
git clone <your-fork-url> markitdown-liberated
cd markitdown-liberated
./scripts/install.sh
```

**Windows (PowerShell)**
```powershell
git clone <your-fork-url> markitdown-liberated
cd markitdown-liberated
pwsh scripts/install.ps1
```

The installer:
1. Registers the MCP server with Claude Code via the official `claude mcp add` command (user scope) — no hand-editing of config files.
2. Pre-warms the `uv` environment (first run downloads Python 3.13 + deps once).
3. Installs the **ingest-guard hook** into `~/.claude/settings.json`.

Then **restart Claude Code** (or start a new session) and verify:
```bash
claude mcp list      # -> markitdown-liberated: ... ✓ Connected
```

### Uninstall
```bash
./scripts/uninstall.sh           # macOS / Linux
pwsh scripts/uninstall.ps1       # Windows
```
Deregisters the MCP server and removes the hook. Your repo and `uv` caches are left untouched.

## Use

### Via Claude (MCP) — the primary path
Just reference a file and let Claude convert it. With the ingest-guard hook active, asking Claude to read a document does this automatically. Examples:

> "Summarize `file:///Users/me/contracts/nda.pdf`"
> "Convert `file:///Users/me/reports/q3.xlsx` to markdown and pull out the totals."

Under the hood Claude calls `convert_to_markdown(uri="file:///…")` and reasons over the returned Markdown. Use a full `file://` URI (or absolute path) — the tool accepts `file:`, `data:`, `http:`, `https:` schemes.

### Running the server manually (optional)
```bash
# stdio (default)
uv run --directory packages/markitdown-liberated markitdown-liberated

# Streamable HTTP / SSE (binds to 127.0.0.1 by default)
uv run --directory packages/markitdown-liberated markitdown-liberated --http --host 127.0.0.1 --port 3001
```

### Claude Desktop
Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "markitdown-liberated": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/packages/markitdown-liberated", "markitdown-liberated"]
    }
  }
}
```

### As a library / CLI (no MCP)
The conversion engine is a normal Python package:
```bash
pip install -e 'packages/markitdown-liberated-core[all]'
```
```python
from markitdown_liberated import MarkItDown

md = MarkItDown()
print(md.convert("report.pdf").text_content)
```
```bash
# CLI
markitdown-liberated-core report.pdf > report.md
```

## Why Markdown?
Markdown is close to plain text but preserves structure (headings, lists, tables, links). LLMs natively "speak" Markdown and it is highly token-efficient, which makes it an ideal ingestion format.

## Security considerations

`markitdown-liberated` performs I/O with the privileges of the current process. Like `open()` or `requests.get()`, it accesses whatever the process can access.

- **Sanitize untrusted input.** Do not feed untrusted file paths or URIs directly in hosted/multi-user contexts. Restrict file paths, URI schemes, and network destinations (block private/loopback/link-local/metadata addresses) as appropriate.
- **The MCP HTTP transport has no authentication** and binds to `localhost` by default. Do not bind it to other interfaces unless you understand the implications.
- **The ingest-guard hook only blocks `Read` and redirects to the local converter** — it does not itself send data anywhere.

## Running tests
```bash
uv run --directory packages/markitdown-liberated-core --python 3.13 --extra all --with pytest pytest -q
```

## Credits & trademarks

This is a fork of [Microsoft MarkItDown](https://github.com/microsoft/markitdown) (MIT License), built by the AutoGen team. All conversion logic derives from that project. "markitdown-liberated" is an independent, renamed fork and is **not** affiliated with or endorsed by Microsoft. Microsoft trademarks and logos are subject to [Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general); this fork is renamed specifically to avoid implying Microsoft sponsorship. Third-party trademarks are subject to their respective policies.

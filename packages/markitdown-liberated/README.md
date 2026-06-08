# markitdown-liberated (MCP server)

> [!IMPORTANT]
> This server is meant for **local use** with local, trusted agents. In Streamable HTTP / SSE mode it binds to `localhost` by default and has **no authentication**. DO NOT bind it to other interfaces unless you understand the [security implications](#security-considerations).

`markitdown-liberated` is a lightweight STDIO / Streamable HTTP / SSE MCP server that converts documents to Markdown, fully locally (no cloud services). It is the MCP front-end for the cloud-free [`markitdown-liberated-core`](../markitdown-liberated-core) engine — the "liberated" fork of [Microsoft MarkItDown](https://github.com/microsoft/markitdown).

It exposes one tool: `convert_to_markdown(uri)`, where `uri` can be any `http:`, `https:`, `file:`, or `data:` URI.

## Installation

Use the installer at the repo root — it registers the server with Claude Code via `claude mcp add` and wires up the ingest-guard hook. See the [main README](../../README.md#install-recommended-as-an-mcp-server).

```bash
./scripts/install.sh        # macOS / Linux
pwsh scripts/install.ps1    # Windows
```

## Running manually

STDIO (default):
```bash
uv run --directory packages/markitdown-liberated markitdown-liberated
```

Streamable HTTP / SSE:
```bash
uv run --directory packages/markitdown-liberated markitdown-liberated --http --host 127.0.0.1 --port 3001
```

## Accessing from Claude Desktop

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

## Debugging

Use the `MCP Inspector`:

```bash
npx @modelcontextprotocol/inspector
```

Connect via the host/port shown (e.g. `http://localhost:5173/`).

- **STDIO:** transport `STDIO`; command `uv run --directory <abs>/packages/markitdown-liberated markitdown-liberated`.
- **Streamable HTTP:** transport `Streamable HTTP`; URL `http://127.0.0.1:3001/mcp`.
- **SSE:** transport `SSE`; URL `http://127.0.0.1:3001/sse`.

Then: `Tools` → `List Tools` → `convert_to_markdown` → run it on any valid URI.

## Security considerations

The server has no authentication and runs with the privileges of the user running it. In SSE / Streamable HTTP mode it binds to `localhost` by default. Even so, any process or user on the same machine can reach it, and `convert_to_markdown` can read any file the server's user can access or fetch any network resource that user can reach. For stronger isolation, run it under a restricted user. **DO NOT bind to non-localhost interfaces** unless you understand the implications.

## Credits & trademarks

A renamed, cloud-free fork of [Microsoft MarkItDown](https://github.com/microsoft/markitdown) (MIT, built by the AutoGen team). Not affiliated with or endorsed by Microsoft. Microsoft trademarks are subject to [Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general); this fork is renamed to avoid implying Microsoft sponsorship.

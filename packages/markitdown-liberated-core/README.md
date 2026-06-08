# markitdown-liberated-core

The local-only conversion engine behind [`markitdown-liberated`](../markitdown-liberated) — a cloud-free fork of [Microsoft MarkItDown](https://github.com/microsoft/markitdown) that converts documents (PDF, Office, EPUB, HTML, …) to Markdown for LLM ingestion, with **no data sent to any third-party service**.

All cloud converters (Azure Document Intelligence / Content Understanding), LLM image descriptions, LLM-vision OCR, cloud audio transcription, and YouTube transcripts have been removed. Conversion of local files runs entirely offline.

Most users should install this via the MCP server — see the [repository README](../../README.md). To use it directly as a library:

```bash
pip install -e 'packages/markitdown-liberated-core[all]'
```

```python
from markitdown_liberated import MarkItDown

md = MarkItDown()
print(md.convert("report.pdf").text_content)
```

CLI:

```bash
markitdown-liberated-core report.pdf > report.md
```

## Optional dependencies

`[all]` installs everything; or pick per-format: `[pptx]`, `[docx]`, `[xlsx]`, `[xls]`, `[pdf]`, `[outlook]`.

## Credits & trademarks

A renamed fork of [Microsoft MarkItDown](https://github.com/microsoft/markitdown) (MIT, built by the AutoGen team). Not affiliated with or endorsed by Microsoft. Microsoft trademarks are subject to [Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general); renamed to avoid implying Microsoft sponsorship.

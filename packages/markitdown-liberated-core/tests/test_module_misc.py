#!/usr/bin/env python3 -m pytest
import io
import os
import re
import shutil
import pytest

from markitdown_liberated._uri_utils import parse_data_uri, file_uri_to_path

from markitdown_liberated import (
    MarkItDown,
    UnsupportedFormatException,
    FileConversionException,
    StreamInfo,
)

# This file contains module tests that are not directly tested by the FileTestVectors.
# This includes things like helper functions and runtime conversion options
# (e.g., LLM clients, exiftool path, transcription services, etc.)

skip_remote = (
    True if os.environ.get("GITHUB_ACTIONS") else False
)  # Don't run these tests in CI


# Skip exiftool tests if not installed
skip_exiftool = shutil.which("exiftool") is None

TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "test_files")

JPG_TEST_EXIFTOOL = {
    "Author": "AutoGen Authors",
    "Title": "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation",
    "Description": "AutoGen enables diverse LLM-based applications",
    "ImageSize": "1615x1967",
    "DateTimeOriginal": "2024:03:14 22:10:00",
}

PDF_TEST_URL = "https://arxiv.org/pdf/2308.08155v2.pdf"
PDF_TEST_STRINGS = [
    "While there is contemporaneous exploration of multi-agent approaches"
]

DOCX_COMMENT_TEST_STRINGS = [
    "314b0a30-5b04-470b-b9f7-eed2c2bec74a",
    "49e168b7-d2ae-407f-a055-2167576f39a1",
    "## d666f1f7-46cb-42bd-9a39-9a39cf2a509f",
    "# Abstract",
    "# Introduction",
    "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation",
    "This is a test comment. 12df-321a",
    "Yet another comment in the doc. 55yiyi-asd09",
]

BLOG_TEST_URL = "https://microsoft.github.io/autogen/blog/2023/04/21/LLM-tuning-math"
BLOG_TEST_STRINGS = [
    "Large language models (LLMs) are powerful tools that can generate natural language texts for various applications, such as chatbots, summarization, translation, and more. GPT-4 is currently the state of the art LLM in the world. Is model selection irrelevant? What about inference parameters?",
    "an example where high cost can easily prevent a generic complex",
]

PPTX_TEST_STRINGS = [
    "2cdda5c8-e50e-4db4-b5f0-9722a649f455",
    "04191ea8-5c73-4215-a1d3-1cfb43aaaf12",
    "44bf7d06-5e7a-4a40-a2e1-a2e42ef28c8a",
    "1b92870d-e3b5-4e65-8153-919f4ff45592",
    "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation",
    "a3f6004b-6f4f-4ea8-bee3-3741f4dc385f",  # chart title
    "2003",  # chart value
]


# --- Helper Functions ---
def validate_strings(result, expected_strings, exclude_strings=None):
    """Validate presence or absence of specific strings."""
    text_content = result.text_content.replace("\\", "")
    for string in expected_strings:
        assert string in text_content
    if exclude_strings:
        for string in exclude_strings:
            assert string not in text_content


def test_stream_info_operations() -> None:
    """Test operations performed on StreamInfo objects."""

    stream_info_original = StreamInfo(
        mimetype="mimetype.1",
        extension="extension.1",
        charset="charset.1",
        filename="filename.1",
        local_path="local_path.1",
        url="url.1",
    )

    # Check updating all attributes by keyword
    keywords = ["mimetype", "extension", "charset", "filename", "local_path", "url"]
    for keyword in keywords:
        updated_stream_info = stream_info_original.copy_and_update(
            **{keyword: f"{keyword}.2"}
        )

        # Make sure the targted attribute is updated
        assert getattr(updated_stream_info, keyword) == f"{keyword}.2"

        # Make sure the other attributes are unchanged
        for k in keywords:
            if k != keyword:
                assert getattr(stream_info_original, k) == getattr(
                    updated_stream_info, k
                )

    # Check updating all attributes by passing a new StreamInfo object
    keywords = ["mimetype", "extension", "charset", "filename", "local_path", "url"]
    for keyword in keywords:
        updated_stream_info = stream_info_original.copy_and_update(
            StreamInfo(**{keyword: f"{keyword}.2"})
        )

        # Make sure the targted attribute is updated
        assert getattr(updated_stream_info, keyword) == f"{keyword}.2"

        # Make sure the other attributes are unchanged
        for k in keywords:
            if k != keyword:
                assert getattr(stream_info_original, k) == getattr(
                    updated_stream_info, k
                )

    # Check mixing and matching
    updated_stream_info = stream_info_original.copy_and_update(
        StreamInfo(extension="extension.2", filename="filename.2"),
        mimetype="mimetype.3",
        charset="charset.3",
    )
    assert updated_stream_info.extension == "extension.2"
    assert updated_stream_info.filename == "filename.2"
    assert updated_stream_info.mimetype == "mimetype.3"
    assert updated_stream_info.charset == "charset.3"
    assert updated_stream_info.local_path == "local_path.1"
    assert updated_stream_info.url == "url.1"

    # Check multiple StreamInfo objects
    updated_stream_info = stream_info_original.copy_and_update(
        StreamInfo(extension="extension.4", filename="filename.5"),
        StreamInfo(mimetype="mimetype.6", charset="charset.7"),
    )
    assert updated_stream_info.extension == "extension.4"
    assert updated_stream_info.filename == "filename.5"
    assert updated_stream_info.mimetype == "mimetype.6"
    assert updated_stream_info.charset == "charset.7"
    assert updated_stream_info.local_path == "local_path.1"
    assert updated_stream_info.url == "url.1"


def test_data_uris() -> None:
    # Test basic parsing of data URIs
    data_uri = "data:text/plain;base64,SGVsbG8sIFdvcmxkIQ=="
    mime_type, attributes, data = parse_data_uri(data_uri)
    assert mime_type == "text/plain"
    assert len(attributes) == 0
    assert data == b"Hello, World!"

    data_uri = "data:base64,SGVsbG8sIFdvcmxkIQ=="
    mime_type, attributes, data = parse_data_uri(data_uri)
    assert mime_type is None
    assert len(attributes) == 0
    assert data == b"Hello, World!"

    data_uri = "data:text/plain;charset=utf-8;base64,SGVsbG8sIFdvcmxkIQ=="
    mime_type, attributes, data = parse_data_uri(data_uri)
    assert mime_type == "text/plain"
    assert len(attributes) == 1
    assert attributes["charset"] == "utf-8"
    assert data == b"Hello, World!"

    data_uri = "data:,Hello%2C%20World%21"
    mime_type, attributes, data = parse_data_uri(data_uri)
    assert mime_type is None
    assert len(attributes) == 0
    assert data == b"Hello, World!"

    data_uri = "data:text/plain,Hello%2C%20World%21"
    mime_type, attributes, data = parse_data_uri(data_uri)
    assert mime_type == "text/plain"
    assert len(attributes) == 0
    assert data == b"Hello, World!"

    data_uri = "data:text/plain;charset=utf-8,Hello%2C%20World%21"
    mime_type, attributes, data = parse_data_uri(data_uri)
    assert mime_type == "text/plain"
    assert len(attributes) == 1
    assert attributes["charset"] == "utf-8"
    assert data == b"Hello, World!"


def test_file_uris() -> None:
    # Test file URI with an empty host
    file_uri = "file:///path/to/file.txt"
    netloc, path = file_uri_to_path(file_uri)
    assert netloc is None
    assert path == "/path/to/file.txt"

    # Test file URI with no host
    file_uri = "file:/path/to/file.txt"
    netloc, path = file_uri_to_path(file_uri)
    assert netloc is None
    assert path == "/path/to/file.txt"

    # Test file URI with localhost
    file_uri = "file://localhost/path/to/file.txt"
    netloc, path = file_uri_to_path(file_uri)
    assert netloc == "localhost"
    assert path == "/path/to/file.txt"

    # Test file URI with query parameters
    file_uri = "file:///path/to/file.txt?param=value"
    netloc, path = file_uri_to_path(file_uri)
    assert netloc is None
    assert path == "/path/to/file.txt"

    # Test file URI with fragment
    file_uri = "file:///path/to/file.txt#fragment"
    netloc, path = file_uri_to_path(file_uri)
    assert netloc is None
    assert path == "/path/to/file.txt"


def test_docx_comments() -> None:
    # Test DOCX processing, with comments and setting style_map on init
    markitdown_with_style_map = MarkItDown(style_map="comment-reference => ")
    result = markitdown_with_style_map.convert(
        os.path.join(TEST_FILES_DIR, "test_with_comment.docx")
    )
    validate_strings(result, DOCX_COMMENT_TEST_STRINGS)


def test_docx_equations() -> None:
    markitdown_liberated = MarkItDown()
    docx_file = os.path.join(TEST_FILES_DIR, "equations.docx")
    result = markitdown_liberated.convert(docx_file)

    # Check for inline equation m=1 (wrapped with single $) is present
    assert "$m=1$" in result.text_content, "Inline equation $m=1$ not found"

    # Find block equations wrapped with double $$ and check if they are present
    block_equations = re.findall(r"\$\$(.+?)\$\$", result.text_content)
    assert block_equations, "No block equations found in the document."


def test_input_as_strings() -> None:
    markitdown_liberated = MarkItDown()

    # Test input from a stream
    input_data = b"<html><body><h1>Test</h1></body></html>"
    result = markitdown_liberated.convert_stream(io.BytesIO(input_data))
    assert "# Test" in result.text_content

    # Test input with leading blank characters
    input_data = b"   \n\n\n<html><body><h1>Test</h1></body></html>"
    result = markitdown_liberated.convert_stream(io.BytesIO(input_data))
    assert "# Test" in result.text_content


def test_deeply_nested_html_fallback() -> None:
    """Large, deeply nested HTML should fall back to plain-text extraction
    instead of silently returning unconverted HTML (issue #1636).

    Note: This test uses sys.setrecursionlimit to guarantee a RecursionError
    regardless of the host environment's default limit, making it deterministic
    across different platforms and CI configurations.
    """
    import sys
    import warnings

    markitdown_liberated = MarkItDown()

    # Use a small recursion limit so the test is environment-independent.
    # We restore the original limit in a finally block to avoid side-effects.
    original_limit = sys.getrecursionlimit()
    low_limit = 200  # well below markdownify's traversal depth for depth=500

    # Build HTML with nesting deep enough to trigger RecursionError
    depth = 500
    html = "<html><body>"
    for _ in range(depth):
        html += '<div style="margin-left:10px">'
    html += "<p>Deep content with <b>bold text</b></p>"
    for _ in range(depth):
        html += "</div>"
    html += "</body></html>"

    try:
        sys.setrecursionlimit(low_limit)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = markitdown_liberated.convert_stream(
                io.BytesIO(html.encode("utf-8")),
                file_extension=".html",
            )

            # Should have emitted a warning about the fallback
            recursion_warnings = [x for x in w if "deeply nested" in str(x.message)]
            assert len(recursion_warnings) > 0
    finally:
        sys.setrecursionlimit(original_limit)

    # The output should contain the text content, not raw HTML
    assert "Deep content" in result.markdown
    assert "bold text" in result.markdown
    assert "<div" not in result.markdown
    assert "<p>" not in result.markdown


def test_doc_rlink() -> None:
    # Test for: CVE-2025-11849
    markitdown_liberated = MarkItDown()

    # Document with rlink
    docx_file = os.path.join(TEST_FILES_DIR, "rlink.docx")

    # Directory containing the target rlink file
    rlink_tmp_dir = os.path.abspath(os.sep + "tmp")

    # Ensure the tmp directory exists
    if not os.path.exists(rlink_tmp_dir):
        pytest.skip(f"Skipping rlink test; {rlink_tmp_dir} directory does not exist.")
        return

    rlink_file_path = os.path.join(rlink_tmp_dir, "test_rlink.txt")
    rlink_content = "de658225-569e-4e3d-9ed2-cfb6abf927fc"
    b64_prefix = (
        "ZGU2NTgyMjUtNTY5ZS00ZTNkLTllZDItY2ZiNmFiZjk"  # base64 prefix of rlink_content
    )

    if os.path.exists(rlink_file_path):
        with open(rlink_file_path, "r", encoding="utf-8") as f:
            existing_content = f.read()
            if existing_content != rlink_content:
                raise ValueError(
                    f"Existing {rlink_file_path} content does not match expected content."
                )
    else:
        with open(rlink_file_path, "w", encoding="utf-8") as f:
            f.write(rlink_content)

    try:
        result = markitdown_liberated.convert(docx_file, keep_data_uris=True).text_content
        assert (
            b64_prefix not in result
        )  # Make sure the target file was NOT embedded in the output
    finally:
        os.remove(rlink_file_path)


@pytest.mark.skipif(
    skip_remote,
    reason="do not run tests that query external urls",
)
def test_markitdown_remote() -> None:
    markitdown_liberated = MarkItDown()

    # By URL
    result = markitdown_liberated.convert(PDF_TEST_URL)
    for test_string in PDF_TEST_STRINGS:
        assert test_string in result.text_content


def test_exceptions() -> None:
    # Check that an exception is raised when trying to convert an unsupported format
    markitdown_liberated = MarkItDown()
    with pytest.raises(UnsupportedFormatException):
        markitdown_liberated.convert(os.path.join(TEST_FILES_DIR, "random.bin"))

    # Check that an exception is raised when trying to convert a file that is corrupted
    with pytest.raises(FileConversionException) as exc_info:
        markitdown_liberated.convert(
            os.path.join(TEST_FILES_DIR, "random.bin"), file_extension=".pptx"
        )
    assert len(exc_info.value.attempts) == 1
    assert type(exc_info.value.attempts[0].converter).__name__ == "PptxConverter"


@pytest.mark.skipif(
    skip_exiftool,
    reason="do not run if exiftool is not installed",
)
def test_markitdown_exiftool() -> None:
    which_exiftool = shutil.which("exiftool")
    assert which_exiftool is not None

    # Test explicitly setting the location of exiftool
    markitdown_liberated = MarkItDown(exiftool_path=which_exiftool)
    result = markitdown_liberated.convert(os.path.join(TEST_FILES_DIR, "test.jpg"))
    for key in JPG_TEST_EXIFTOOL:
        target = f"{key}: {JPG_TEST_EXIFTOOL[key]}"
        assert target in result.text_content

    # Test setting the exiftool path through an environment variable
    os.environ["EXIFTOOL_PATH"] = which_exiftool
    markitdown_liberated = MarkItDown()
    result = markitdown_liberated.convert(os.path.join(TEST_FILES_DIR, "test.jpg"))
    for key in JPG_TEST_EXIFTOOL:
        target = f"{key}: {JPG_TEST_EXIFTOOL[key]}"
        assert target in result.text_content


if __name__ == "__main__":
    """Runs this file's tests from the command line."""
    for test in [
        test_stream_info_operations,
        test_data_uris,
        test_file_uris,
        test_docx_comments,
        test_input_as_strings,
        test_markitdown_remote,
        test_exceptions,
        test_doc_rlink,
        test_markitdown_exiftool,
    ]:
        print(f"Running {test.__name__}...", end="")
        test()
        print("OK")
    print("All tests passed!")

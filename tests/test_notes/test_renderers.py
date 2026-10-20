"""Tests for markdown rendering and bleach HTML sanitization."""

from markdown_notes.notes.renderers import render_markdown_to_html


def test_render_basic_markdown() -> None:
    """Verify headers, emphasis, lists, and code blocks render correctly."""
    raw = "# Header 1\n\nThis is **bold** and *italic*.\n\n- Item 1\n- Item 2\n\n```python\nprint('hello')\n```"
    html = render_markdown_to_html(raw)

    assert "<h1>Header 1</h1>" in html
    assert "<strong>bold</strong>" in html
    assert "<em>italic</em>" in html
    assert "<li>Item 1</li>" in html
    assert "<code" in html
    assert "</code>" in html


def test_render_table_extension() -> None:
    """Verify markdown table extension renders table structure."""
    raw = "| Name | Value |\n| --- | --- |\n| Alpha | 100 |"
    html = render_markdown_to_html(raw)

    assert "<table>" in html
    assert "<th>Name</th>" in html
    assert "<td>Alpha</td>" in html


def test_sanitize_xss_scripts() -> None:
    """Verify malicious script tags and inline event handlers are sanitized."""
    malicious = '# Title\n\n<script>alert("XSS")</script>\n\n<p onclick="steal()">Click</p>'
    html = render_markdown_to_html(malicious)

    assert "<script>" not in html
    assert "</script>" not in html
    assert "onclick" not in html
    assert "<p>Click</p>" in html


def test_sanitize_javascript_links() -> None:
    """Verify javascript: URIs are stripped from links."""
    malicious = '[Malicious Link](javascript:alert("pwned"))'
    html = render_markdown_to_html(malicious)

    assert "javascript:" not in html
    assert 'href="javascript:' not in html


def test_render_empty_input() -> None:
    """Verify empty string returns empty result."""
    assert render_markdown_to_html("") == ""

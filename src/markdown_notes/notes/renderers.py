"""Markdown to HTML rendering engine with HTML sanitization."""

import bleach
import markdown

# Safe list of tags permitted in rendered markdown
ALLOWED_TAGS: list[str] = [
    "a",
    "abbr",
    "b",
    "blockquote",
    "br",
    "code",
    "del",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "i",
    "img",
    "li",
    "ol",
    "p",
    "pre",
    "span",
    "strong",
    "sub",
    "sup",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "ul",
]

# Safe attributes whitelist per HTML tag
ALLOWED_ATTRIBUTES: dict[str, list[str]] = {
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title", "width", "height"],
    "code": ["class"],
    "span": ["class"],
    "th": ["align"],
    "td": ["align"],
}

# Permitted URI schemes
ALLOWED_PROTOCOLS: list[str] = ["http", "https", "mailto"]


def render_markdown_to_html(raw_markdown: str) -> str:
    """Convert raw Markdown into sanitized, safe HTML.

    Args:
        raw_markdown: Markdown source text.

    Returns:
        Sanitized HTML string safe for browser rendering.
    """
    if not raw_markdown:
        return ""

    # Convert markdown to HTML with standard structured formatting extensions
    html_output = markdown.markdown(
        raw_markdown,
        extensions=[
            "extra",
            "toc",
            "sane_lists",
            "nl2br",
        ],
        output_format="html",
    )

    # Sanitize HTML using bleach to guard against XSS injection attacks
    clean_html = bleach.clean(
        html_output,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )

    return clean_html

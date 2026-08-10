"""HTML sanitising for owner-authored content (section 4.8 of tech.md)."""

import re

import bleach

ALLOWED_TAGS: frozenset[str] = frozenset(
    {
        "p",
        "br",
        "strong",
        "em",
        "u",
        "ul",
        "ol",
        "li",
        "h2",
        "h3",
        "h4",
        "a",
        "img",
        "blockquote",
        "table",
        "thead",
        "tbody",
        "tr",
        "th",
        "td",
        "hr",
    }
)

ALLOWED_ATTRIBUTES: dict[str, list[str]] = {
    "*": ["href", "title", "target", "rel", "src", "alt", "width", "height"]
}

ALLOWED_PROTOCOLS: frozenset[str] = frozenset({"http", "https", "mailto", "tel"})

# bleach strips the tag but keeps its text, which would print stylesheets and
# scripts as visible content. These two are dropped whole.
_DROP_WITH_CONTENT = re.compile(r"<\s*(script|style)\b[^>]*>.*?<\s*/\s*\1\s*>", re.IGNORECASE | re.S)
_DROP_UNCLOSED = re.compile(r"<\s*(script|style)\b[^>]*>.*", re.IGNORECASE | re.S)


def sanitize_html(value: str) -> str:
    """Return `value` with everything outside the allow-list removed."""
    if not value:
        return ""
    text = _DROP_WITH_CONTENT.sub("", value)
    text = _DROP_UNCLOSED.sub("", text)
    return bleach.clean(
        text,
        tags=set(ALLOWED_TAGS),
        attributes=ALLOWED_ATTRIBUTES,
        protocols=list(ALLOWED_PROTOCOLS),
        strip=True,
        strip_comments=True,
    )

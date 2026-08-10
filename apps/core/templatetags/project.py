"""Template tags shared by every page: translations, renditions, URLs, menus."""

import json
from typing import Any
from urllib.parse import urljoin

from django import template
from django.conf import settings
from django.utils.safestring import SafeString, mark_safe

from apps.core.navigation import footer_items, main_items

register = template.Library()

# Closed list from section 11: only fields sanitised by bleach on save may be
# rendered as markup.
TR_HTML_FIELDS: frozenset[tuple[str, str]] = frozenset({("staticpage", "body"), ("post", "body")})


def _model_name(obj: Any) -> str:
    meta = getattr(obj, "_meta", None)
    if meta is not None:
        return str(meta.model_name)
    return type(obj).__name__.lower()


@register.filter
def tr(obj: Any, field: str) -> str:
    """Translated text, escaped like any other template variable."""
    if obj is None:
        return ""
    return str(obj.tr(field))


@register.filter
def tr_html(obj: Any, field: str) -> SafeString:
    """Translated markup. Allowed only for fields sanitised on save."""
    if obj is None:
        return mark_safe("")
    key = (_model_name(obj), field)
    if key not in TR_HTML_FIELDS:
        raise ValueError(
            f"tr_html is not allowed for {key[0]}.{key[1]}: "
            "only bleach-sanitised fields may be rendered as markup"
        )
    return mark_safe(obj.tr(field))


@register.filter
def times(value: Any) -> range:
    """`{% for _ in 3|times %}` - templates cannot count on their own."""
    try:
        return range(int(value))
    except (TypeError, ValueError):
        return range(0)


def _renditions(image: Any) -> list[Any]:
    related = getattr(image, "renditions", None)
    if related is None:
        return []
    return list(related.all()) if hasattr(related, "all") else list(related)


@register.simple_tag
def rendition(image: Any, preset: str, image_format: str) -> Any:
    for item in _renditions(image):
        if item.preset == preset and item.image_format == image_format:
            return item
    return None


@register.simple_tag
def rendition_srcset(image: Any, image_format: str) -> str:
    """Widths for one format, narrowest first. The og preset is not a screen size."""
    candidates = [
        item
        for item in _renditions(image)
        if item.image_format == image_format and item.preset != "og"
    ]
    candidates.sort(key=lambda item: item.width)
    return ", ".join(f"{item.file.url} {item.width}w" for item in candidates)


@register.simple_tag
def absolute_url(path: str) -> str:
    return urljoin(f"{settings.SITE_URL}/", path.lstrip("/"))


def alternate_path(full_path: str, language: str) -> str:
    """Same page in another language, query string and fragment untouched.

    Pure string work on purpose: it must also answer for paths whose view does
    not exist yet, and it is covered by property based tests.
    """
    path, separator, tail = full_path.partition("?")
    prefixed = [code for code, _name in settings.LANGUAGES if code != settings.LANGUAGE_CODE]

    stripped = path
    for code in prefixed:
        if path == f"/{code}" or path.startswith(f"/{code}/"):
            stripped = path[len(code) + 1 :] or "/"
            break

    if not stripped.startswith("/"):
        stripped = f"/{stripped}"
    target = stripped if language == settings.LANGUAGE_CODE else f"/{language}{stripped}"
    return f"{target}{separator}{tail}"


@register.simple_tag(name="alternate_path")
def alternate_path_tag(full_path: str, language: str) -> str:
    return alternate_path(full_path, language)


@register.simple_tag
def language_alternates(full_path: str) -> list[tuple[str, str]]:
    """hreflang pairs: every language plus x-default on the Ukrainian version."""
    pairs = [
        (code, absolute_url(alternate_path(full_path, code))) for code, _name in settings.LANGUAGES
    ]
    pairs.append(("x-default", absolute_url(alternate_path(full_path, settings.LANGUAGE_CODE))))
    return pairs


@register.simple_tag
def main_menu() -> list[Any]:
    return main_items()


@register.simple_tag
def footer_menu() -> list[Any]:
    return footer_items()


@register.simple_tag
def breadcrumb_jsonld(items: list[dict[str, Any]]) -> SafeString:
    data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": position,
                "name": str(item.get("label", "")),
                **({"item": absolute_url(item["url"])} if item.get("url") else {}),
            }
            for position, item in enumerate(items, start=1)
        ],
    }
    return mark_safe(json.dumps(data, ensure_ascii=False).replace("<", "\\u003C"))

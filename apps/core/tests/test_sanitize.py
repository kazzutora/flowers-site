"""Section 4.8 of tech.md: the owner writes HTML, the sanitiser decides what survives."""

import pytest

from apps.core.services.sanitize import sanitize_html

DANGEROUS = [
    "<script>alert(1)</script>",
    "<iframe src='https://evil.example'></iframe>",
    "<img src=x onerror='alert(1)'>",
    "<a href='javascript:alert(1)'>click</a>",
    "<style>body{display:none}</style>",
    "<p onclick='alert(1)'>text</p>",
    "<object data='https://evil.example'></object>",
    "<svg><script>alert(1)</script></svg>",
    "<form action='/steal'><input name='card'></form>",
]


@pytest.mark.parametrize("payload", DANGEROUS)
def test_dangerous_markup_is_removed(payload: str) -> None:
    cleaned = sanitize_html(payload)

    for marker in ("<script", "<iframe", "onerror", "onclick", "javascript:", "<style", "<object"):
        assert marker not in cleaned.lower()


def test_script_and_style_bodies_do_not_leak_as_text() -> None:
    cleaned = sanitize_html("<script>alert('hi')</script><style>body{color:red}</style>")

    assert cleaned.strip() == ""


def test_allowed_markup_survives() -> None:
    source = (
        "<h2>Заголовок</h2><p><strong>Жирний</strong> та <em>курсив</em></p>"
        "<ul><li>Пункт</li></ul>"
        '<a href="https://example.com" title="site" target="_blank" rel="noopener">link</a>'
        '<img src="/media/site/photo.webp" alt="Фото" width="100" height="200">'
        "<table><thead><tr><th>a</th></tr></thead><tbody><tr><td>b</td></tr></tbody></table><hr>"
    )

    cleaned = sanitize_html(source)

    for marker in ("<h2>", "<strong>", "<em>", "<ul>", "<li>", "<table>", "<hr>", "<img"):
        assert marker in cleaned
    assert 'href="https://example.com"' in cleaned
    assert 'alt="Фото"' in cleaned


@pytest.mark.parametrize(
    "target",
    ["http://a.com", "https://a.com", "mailto:a@b.com", "tel:+380501112233"],
)
def test_allowed_protocols_survive(target: str) -> None:
    assert target in sanitize_html(f'<a href="{target}">link</a>')


def test_empty_input_is_safe() -> None:
    assert sanitize_html("") == ""

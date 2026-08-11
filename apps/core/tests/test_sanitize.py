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
    # What a copy and paste from a strange page actually brings along.
    "<SCRIPT>alert(1)</SCRIPT>",
    "<scr<script>ipt>alert(1)</script>",
    "<a href='JaVaScRiPt:alert(1)'>click</a>",
    "<a href='&#106;avascript:alert(1)'>click</a>",
    '<a href="data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==">click</a>',
    "<img src='data:text/html,<script>alert(1)</script>'>",
    "<body onload='alert(1)'>text</body>",
    "<div onmouseover='alert(1)'>hover</div>",
    "<p style='position:fixed;top:0;width:100%'>overlay</p>",
    "<link rel='stylesheet' href='https://evil.example/x.css'>",
    "<meta http-equiv='refresh' content='0;url=https://evil.example'>",
    "<base href='https://evil.example/'>",
    "<embed src='https://evil.example/x.swf'>",
    "<video><source onerror='alert(1)'></video>",
    "<math><mtext><script>alert(1)</script></mtext></math>",
    "<template><script>alert(1)</script></template>",
    "<noscript><p>hidden</p></noscript>",
    "<textarea>text</textarea>",
    "<button onclick='alert(1)'>press</button>",
    "<a href='vbscript:msgbox(1)'>click</a>",
    "<a href='file:///etc/passwd'>click</a>",
]

FORBIDDEN_MARKERS = (
    "<script",
    "<iframe",
    "<style",
    "<object",
    "<embed",
    "<link",
    "<meta",
    "<base",
    "<form",
    "<input",
    "<button",
    "<textarea",
    "javascript:",
    "vbscript:",
    "data:text/html",
    "onerror",
    "onclick",
    "onload",
    "onmouseover",
    "style=",
)


@pytest.mark.parametrize("payload", DANGEROUS)
def test_dangerous_markup_is_removed(payload: str) -> None:
    cleaned = sanitize_html(payload).lower()

    for marker in FORBIDDEN_MARKERS:
        assert marker not in cleaned, f"{marker} survived in {cleaned!r}"


def test_an_attribute_the_allow_list_does_not_name_is_dropped() -> None:
    cleaned = sanitize_html('<p class="hack" id="x" data-x="y">text</p>')

    assert cleaned == "<p>text</p>"


@pytest.mark.django_db
def test_the_database_never_holds_the_payload() -> None:
    """Sanitising happens on save, so nothing dangerous is ever stored."""
    from apps.core.models import StaticPage

    page = StaticPage.objects.create(
        slug="pro-nas",
        title_uk="Про нас",
        body_uk="<p>ok</p><script>bad()</script><img src=x onerror=alert(1)>",
    )
    page.refresh_from_db()

    assert "<script" not in page.body_uk
    assert "onerror" not in page.body_uk
    assert "<p>ok</p>" in page.body_uk


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

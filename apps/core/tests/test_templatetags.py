"""Section 11 of tech.md: translated fields are read through the filters only."""

import pytest
from django.template import Context, Template
from django.utils.translation import override
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from apps.core.models import StaticPage
from apps.core.templatetags.project import (
    absolute_url,
    alternate_path,
    breadcrumb_jsonld,
    rendition,
    rendition_srcset,
    times,
    tr,
    tr_html,
)


def render(source: str, **context: object) -> str:
    return Template("{% load project %}" + source).render(Context(context))


def test_tr_escapes_markup() -> None:
    page = StaticPage(slug="x", title_uk="<b>Про нас</b>")

    assert render('{{ page|tr:"title" }}', page=page) == "&lt;b&gt;Про нас&lt;/b&gt;"


def test_tr_html_does_not_escape_a_sanitised_field() -> None:
    page = StaticPage(slug="x", title_uk="x", body_uk="<p>Текст</p>")

    assert render('{{ page|tr_html:"body" }}', page=page) == "<p>Текст</p>"


def test_tr_html_is_refused_for_other_fields() -> None:
    page = StaticPage(slug="x", title_uk="<b>x</b>")

    with pytest.raises(ValueError):
        tr_html(page, "title")


def test_tr_falls_back_to_ukrainian() -> None:
    page = StaticPage(slug="x", title_uk="Про нас", title_ru="")

    with override("ru"):
        assert tr(page, "title") == "Про нас"


def test_tr_handles_missing_object() -> None:
    assert tr(None, "title") == ""


@pytest.mark.parametrize(
    ("path", "language", "expected"),
    [
        ("/galereya/?color=bilyi", "ru", "/ru/galereya/?color=bilyi"),
        ("/ru/galereya/?color=bilyi", "uk", "/galereya/?color=bilyi"),
        ("/", "ru", "/ru/"),
        ("/ru/", "uk", "/"),
        ("/ru", "uk", "/"),
        ("/rules/", "ru", "/ru/rules/"),
        ("/ru/rules/", "ru", "/ru/rules/"),
    ],
)
def test_alternate_path(path: str, language: str, expected: str) -> None:
    assert alternate_path(path, language) == expected


NAMES = st.text(alphabet="abcdefghijklmnopqrstuvwxyz-_", min_size=1, max_size=6)
QUERIES = st.dictionaries(NAMES, NAMES, max_size=3)
PATHS = st.lists(NAMES, max_size=3)

# The strategies above are tiny; the health check fires when the machine is
# busy, not when the test is. A flaky gate teaches people to ignore it.
STEADY = settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])


@STEADY
@given(segments=PATHS, query=QUERIES)
def test_alternate_path_keeps_the_query(segments: list[str], query: dict[str, str]) -> None:
    # A path that already starts with a language prefix is a translated page,
    # not a page called "ru": the round trip below would not hold for it.
    assume(not segments or segments[0] not in {"uk", "ru"})
    path = "/" + "".join(f"{segment}/" for segment in segments)
    tail = "&".join(f"{key}={value}" for key, value in query.items())
    full_path = f"{path}?{tail}" if tail else path

    switched = alternate_path(full_path, "ru")

    assert switched.startswith("/ru/")
    assert switched.partition("?")[2] == tail
    assert alternate_path(switched, "uk") == full_path


@STEADY
@given(segments=PATHS)
def test_alternate_path_is_stable(segments: list[str]) -> None:
    path = "/" + "".join(f"{segment}/" for segment in segments)

    once = alternate_path(path, "ru")

    assert alternate_path(once, "ru") == once


def test_absolute_url_uses_the_configured_site() -> None:
    assert absolute_url("/pro-nas/") == "http://localhost:8000/pro-nas/"


def test_times_gives_a_countable_range() -> None:
    assert list(times(3)) == [0, 1, 2]
    assert list(times("x")) == []


class _File:
    def __init__(self, url: str) -> None:
        self.url = url


class _Rendition:
    def __init__(self, preset: str, image_format: str, width: int) -> None:
        self.preset = preset
        self.image_format = image_format
        self.width = width
        self.height = width
        self.file = _File(f"/media/{preset}.{image_format}")


class _Image:
    def __init__(self) -> None:
        self.renditions = [
            _Rendition("card", "avif", 800),
            _Rendition("thumb", "avif", 400),
            _Rendition("og", "avif", 1200),
            _Rendition("card", "webp", 800),
        ]


def test_rendition_picks_preset_and_format() -> None:
    image = _Image()

    assert rendition(image, "card", "webp").file.url == "/media/card.webp"
    assert rendition(image, "large", "webp") is None


def test_rendition_srcset_is_sorted_and_skips_og() -> None:
    assert rendition_srcset(_Image(), "avif") == "/media/thumb.avif 400w, /media/card.avif 800w"


def test_breadcrumb_jsonld_escapes_angle_brackets() -> None:
    markup = breadcrumb_jsonld([{"label": "<b>Home</b>", "url": "/"}])

    assert "\\u003C" in markup
    assert "<b>" not in markup

"""Section 9: the query contract, normalisation and the indexing table."""

from urllib.parse import parse_qs, urlencode

import pytest
from django.http import QueryDict
from hypothesis import given
from hypothesis import strategies as st

from apps.catalog import filters, seo

GROUPS = filters.FilterSpec(
    groups=(
        filters.GroupSpec(slug="type", tag_slugs=frozenset({"buket", "koshyk"})),
        filters.GroupSpec(slug="color", tag_slugs=frozenset({"bilyi", "rozhevyi"})),
    )
)

KNOWN_PAIRS = [(group.slug, tag) for group in GROUPS.groups for tag in sorted(group.tag_slugs)]


def _parse(query: str) -> filters.GalleryQuery:
    return filters.parse(QueryDict(query), GROUPS)


# --- parsing ------------------------------------------------------------------


def test_values_of_one_group_are_collected_together() -> None:
    parsed = _parse("type=buket&color=bilyi&color=rozhevyi")

    assert parsed.selected == (("type", ("buket",)), ("color", ("bilyi", "rozhevyi")))


def test_unknown_parameters_and_slugs_are_dropped_silently() -> None:
    parsed = _parse("type=buket&type=nemaye&shape=round&color=violet")

    assert parsed.selected == (("type", ("buket",)),)


def test_an_unknown_sort_falls_back_to_new() -> None:
    assert _parse("sort=abc").sort == filters.SORT_NEW
    assert _parse("sort=popular").sort == filters.SORT_POPULAR


@pytest.mark.parametrize("raw", ["", "page=0", "page=-3", "page=abc", "page="])
def test_a_broken_page_number_becomes_one(raw: str) -> None:
    assert _parse(raw).page == 1


def test_duplicated_values_collapse() -> None:
    assert _parse("type=buket&type=buket").selected == (("type", ("buket",)),)


def test_removing_a_value_returns_to_the_first_page() -> None:
    parsed = _parse("type=buket&color=bilyi&page=3")

    assert parsed.without("color", "bilyi").selected == (("type", ("buket",)),)
    assert parsed.without("color", "bilyi").page == 1


# --- property based -----------------------------------------------------------


@st.composite
def _raw_params(draw: st.DrawFn) -> list[tuple[str, str]]:
    """A plausible query: repeated group values, at most one sort and one page."""
    params = draw(
        st.lists(
            st.tuples(
                st.sampled_from(["type", "color", "q", "a", "shape", "utm_source"]),
                st.sampled_from(["buket", "koshyk", "bilyi", "rozhevyi", "2", "junk"]),
            ),
            max_size=10,
        )
    )
    if draw(st.booleans()):
        params.append(("sort", draw(st.sampled_from(["new", "popular", "abc"]))))
    if draw(st.booleans()):
        params.append(("page", draw(st.sampled_from(["1", "2", "0", "abc"]))))
    return draw(st.permutations(params))


@given(_raw_params())
def test_normalisation_is_idempotent(params: list[tuple[str, str]]) -> None:
    once = filters.parse(QueryDict(urlencode(params)), GROUPS)
    twice = filters.parse(QueryDict(urlencode(once.to_params())), GROUPS)

    assert once == twice


@given(_raw_params())
def test_the_order_of_the_incoming_parameters_never_shows_up(
    params: list[tuple[str, str]],
) -> None:
    forwards = filters.parse(QueryDict(urlencode(params)), GROUPS)
    backwards = filters.parse(QueryDict(urlencode(list(reversed(params)))), GROUPS)

    assert forwards.selected == backwards.selected
    assert forwards.query_string() == backwards.query_string()


@given(_raw_params(), st.text(max_size=10), st.text(max_size=10))
def test_an_unknown_parameter_never_changes_the_result(
    params: list[tuple[str, str]], key: str, value: str
) -> None:
    known = {group.slug for group in GROUPS.groups} | {"sort", "page"}
    if key in known:
        return

    without = filters.parse(QueryDict(urlencode(params)), GROUPS)
    with_junk = filters.parse(QueryDict(urlencode([*params, (key, value)])), GROUPS)

    assert without == with_junk


@given(st.lists(st.sampled_from(KNOWN_PAIRS), max_size=6))
def test_the_canonical_query_is_sorted_and_deduplicated(pairs: list[tuple[str, str]]) -> None:
    parsed = filters.parse(QueryDict(urlencode(pairs)), GROUPS)

    values = parse_qs(parsed.query_string().lstrip("?"))
    for group, tags in values.items():
        assert tags == sorted(set(tags)), group
    assert [group for group, _tags in parsed.selected] == [
        group.slug for group in GROUPS.groups if group.slug in values
    ]


# --- the indexing table -------------------------------------------------------


@pytest.mark.parametrize(
    ("occasion", "tags", "sort", "page", "robots", "canonical"),
    [
        (None, [], "new", 1, seo.INDEX, "/galereya/"),
        (None, [], "new", 2, seo.INDEX, "/galereya/?page=2"),
        ("vesillya", [], "new", 1, seo.INDEX, "/galereya/vesillya/"),
        (None, [("type", "buket")], "new", 1, seo.INDEX, "/galereya/?type=buket"),
        (None, [("type", "buket")], "new", 3, seo.INDEX, "/galereya/?type=buket&page=3"),
        (
            None,
            [("type", "buket"), ("color", "bilyi")],
            "new",
            1,
            seo.NOINDEX,
            "/galereya/",
        ),
        (None, [], "popular", 1, seo.NOINDEX, "/galereya/"),
        (None, [("type", "buket")], "popular", 1, seo.NOINDEX, "/galereya/?type=buket"),
        # Both examples spelled out in section 9.
        (
            None,
            [("type", "a"), ("color", "b")],
            "new",
            2,
            seo.NOINDEX,
            "/galereya/",
        ),
        (
            "vesillya",
            [("type", "a")],
            "popular",
            1,
            seo.NOINDEX,
            "/galereya/vesillya/?type=a",
        ),
    ],
)
def test_the_robots_table_is_followed_row_by_row(
    occasion: str | None,
    tags: list[tuple[str, str]],
    sort: str,
    page: int,
    robots: str,
    canonical: str,
) -> None:
    assert seo.robots_directive(occasion, tags, sort, page) == (robots, canonical)


def test_the_canonical_never_carries_the_sort() -> None:
    _robots, canonical = seo.robots_directive(None, [("type", "buket")], "popular", 2)

    assert "sort" not in canonical
    assert canonical == "/galereya/?type=buket&page=2"

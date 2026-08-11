"""Sections 9 and 10: the gallery page as a visitor meets it."""

from typing import Any

import pytest
from django.test import Client

from apps.catalog.filters import PAGE_SIZE
from apps.catalog.models import TagGroup, Work
from tests.factories import (
    OccasionFactory,
    SiteSettingsFactory,
    TagFactory,
    TagGroupFactory,
    WorkFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def catalog() -> dict[str, Any]:
    """Two groups, four tags, four works and one occasion."""
    SiteSettingsFactory.create()
    wedding = OccasionFactory.create(slug="vesillya", name_uk="Весілля")
    gift = OccasionFactory.create(slug="podarunok", name_uk="Подарунок")

    types = TagGroupFactory.create(slug="type", name_uk="Тип", order=1)
    colors = TagGroupFactory.create(
        slug="color", name_uk="Колір", order=2, filter_kind=TagGroup.FilterKind.COLOR_SWATCH
    )
    bouquet = TagFactory.create(group=types, slug="buket", name_uk="Букет")
    basket = TagFactory.create(group=types, slug="koshyk", name_uk="Кошик")
    white = TagFactory.create(group=colors, slug="bilyi", name_uk="Білий", color_hex="#FFFFFF")
    pink = TagFactory.create(group=colors, slug="rozhevyi", name_uk="Рожевий", color_hex="#F2C9C9")

    white_bouquet = WorkFactory.create(
        title_uk="Білий букет", occasions=[wedding], tags=[bouquet, white]
    )
    pink_bouquet = WorkFactory.create(
        title_uk="Рожевий букет", occasions=[gift], tags=[bouquet, pink]
    )
    white_basket = WorkFactory.create(title_uk="Білий кошик", tags=[basket, white])
    draft = WorkFactory.create(title_uk="Чернетка", status=Work.Status.DRAFT, tags=[bouquet])
    archived = WorkFactory.create(title_uk="Архів", status=Work.Status.ARCHIVED, tags=[bouquet])

    return {
        "wedding": wedding,
        "white_bouquet": white_bouquet,
        "pink_bouquet": pink_bouquet,
        "white_basket": white_basket,
        "draft": draft,
        "archived": archived,
    }


def _titles(response: Any) -> list[str]:
    return [work.title_uk for work in response.context["works"]]


# --- filtering ----------------------------------------------------------------


def test_values_of_one_group_are_an_or_and_groups_are_an_and(
    client: Client, catalog: dict[str, Any]
) -> None:
    response = client.get("/galereya/?type=buket&color=bilyi&color=rozhevyi")

    assert response.status_code == 200
    assert sorted(_titles(response)) == ["Білий букет", "Рожевий букет"]


def test_an_unknown_parameter_or_slug_leaves_the_page_alone(
    client: Client, catalog: dict[str, Any]
) -> None:
    response = client.get("/galereya/?shape=round&type=nemaye&sort=abc")

    assert response.status_code == 200
    assert len(_titles(response)) == 3


def test_drafts_and_archived_works_stay_out_of_the_gallery(
    client: Client, catalog: dict[str, Any]
) -> None:
    body = client.get("/galereya/").content.decode()

    assert "Чернетка" not in body
    assert "Архів" not in body


def test_an_occasion_narrows_the_section(client: Client, catalog: dict[str, Any]) -> None:
    response = client.get("/galereya/vesillya/")

    assert _titles(response) == ["Білий букет"]


def test_an_unknown_or_inactive_occasion_is_a_404(client: Client, catalog: dict[str, Any]) -> None:
    OccasionFactory.create(slug="prykhovanyi", is_active=False)

    assert client.get("/galereya/nemaye-takogo/").status_code == 404
    assert client.get("/galereya/prykhovanyi/").status_code == 404


def test_the_counter_matches_the_number_of_cards(client: Client, catalog: dict[str, Any]) -> None:
    response = client.get("/galereya/?type=buket")

    assert response.context["found_count"] == 2
    assert len(_titles(response)) == 2


# --- the panel ----------------------------------------------------------------


def test_occasions_are_links_in_the_panel_not_checkboxes(
    client: Client, catalog: dict[str, Any]
) -> None:
    body = client.get("/galereya/").content.decode()

    assert 'href="/galereya/vesillya/"' in body
    assert 'name="occasion" value=""' in body
    assert 'value="vesillya"' not in body.split("<form")[1].split("</form>")[0].replace(
        'name="occasion"', ""
    )


def test_active_filters_show_as_chips_that_can_be_removed(
    client: Client, catalog: dict[str, Any]
) -> None:
    body = client.get("/galereya/?type=buket&color=bilyi").content.decode()

    assert "Букет" in body
    assert 'href="/galereya/?color=bilyi"' in body, "removing a chip drops only its own value"
    assert 'href="/galereya/?type=buket"' in body


def test_an_empty_result_offers_a_way_out(client: Client, catalog: dict[str, Any]) -> None:
    response = client.get("/galereya/?type=koshyk&color=rozhevyi")
    body = response.content.decode()

    assert response.status_code == 200
    assert response.context["found_count"] == 0
    assert 'href="tel:' in body


def test_the_section_text_is_printed_below_the_grid(
    client: Client, catalog: dict[str, Any]
) -> None:
    occasion = catalog["wedding"]
    occasion.description_uk = "Весільна флористика під ключ."
    occasion.save()

    assert "Весільна флористика під ключ." in client.get("/galereya/vesillya/").content.decode()


# --- ordering and paging ------------------------------------------------------


def test_pinned_works_come_first_under_both_sorts(client: Client, catalog: dict[str, Any]) -> None:
    pinned = catalog["white_basket"]
    pinned.is_pinned = True
    pinned.save()

    for sort in ("new", "popular"):
        response = client.get(f"/galereya/?sort={sort}")
        assert _titles(response)[0] == "Білий кошик", sort


def test_the_order_is_stable_when_no_one_has_any_views(client: Client) -> None:
    SiteSettingsFactory.create()
    for index in range(10):
        WorkFactory.create(title_uk=f"Робота {index}")

    first = [work.pk for work in client.get("/galereya/?sort=popular").context["works"]]
    again = [work.pk for work in client.get("/galereya/?sort=popular").context["works"]]

    assert first == again


def test_show_more_walks_the_pages_without_repeating_a_card(client: Client) -> None:
    SiteSettingsFactory.create()
    for index in range(PAGE_SIZE + 5):
        WorkFactory.create(title_uk=f"Робота {index}")

    first = [work.pk for work in client.get("/galereya/").context["works"]]
    second = [work.pk for work in client.get("/galereya/?page=2").context["works"]]

    assert len(first) == PAGE_SIZE
    assert len(second) == 5
    assert set(first).isdisjoint(second)
    assert len(set(first) | set(second)) == PAGE_SIZE + 5


def test_a_broken_sort_does_not_take_the_page_down(client: Client, catalog: dict[str, Any]) -> None:
    assert client.get("/galereya/?sort=abc&page=nope").status_code == 200


# --- the htmx fragment --------------------------------------------------------


def test_the_fragment_answers_with_the_results_and_pushes_the_public_url(
    client: Client, catalog: dict[str, Any]
) -> None:
    response = client.get(
        "/hx/gallery/?occasion=vesillya&type=buket", headers={"HX-Request": "true"}
    )
    body = response.content.decode()

    assert response.status_code == 200
    assert response.headers["HX-Push-Url"] == "/galereya/vesillya/?type=buket"
    assert 'id="gallery-results"' in body
    assert "<html" not in body
    assert 'hx-swap-oob="true"' in body, "the show more button lives outside the swapped block"


def test_the_fragment_and_the_page_agree(client: Client, catalog: dict[str, Any]) -> None:
    page = client.get("/galereya/?type=buket")
    fragment = client.get("/hx/gallery/?type=buket", headers={"HX-Request": "true"})

    assert _titles(page) == _titles(fragment)


# --- seo ----------------------------------------------------------------------


def test_the_page_carries_the_canonical_and_the_robots_directive(
    client: Client, catalog: dict[str, Any]
) -> None:
    body = client.get("/galereya/?type=buket&color=bilyi").content.decode()

    assert '<meta name="robots" content="noindex, follow">' in body
    assert '<link rel="canonical" href="http://localhost:8000/galereya/">' in body


def test_a_single_tag_stays_indexable(client: Client, catalog: dict[str, Any]) -> None:
    body = client.get("/galereya/?type=buket").content.decode()

    assert '<meta name="robots" content="index, follow">' in body
    assert '<link rel="canonical" href="http://localhost:8000/galereya/?type=buket">' in body


def test_the_next_page_is_announced(client: Client) -> None:
    SiteSettingsFactory.create()
    for index in range(PAGE_SIZE + 1):
        WorkFactory.create(title_uk=f"Робота {index}")

    body = client.get("/galereya/").content.decode()

    assert 'rel="next"' in body


# --- query budget -------------------------------------------------------------


def _query_count(client: Client, url: str) -> int:
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    with CaptureQueriesContext(connection) as captured:
        client.get(url)
    return len(captured.captured_queries)


def test_the_page_costs_the_same_whatever_the_number_of_works(
    client: Client, catalog: dict[str, Any]
) -> None:
    from apps.core.models import SiteSettings

    SiteSettings.load()  # warm, exactly like a live site between deploys

    with_three = _query_count(client, "/galereya/")
    for index in range(30):
        WorkFactory.create(title_uk=f"Робота {index}")
    with_thirty_three = _query_count(client, "/galereya/")

    assert with_three == with_thirty_three
    assert with_thirty_three <= 10, "the grid must not walk the works one by one"

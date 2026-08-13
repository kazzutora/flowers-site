"""Section 10, "favourites": a collection the visitor dictates on the phone."""

from typing import Any

import pytest
from django.test import Client

from apps.catalog.models import Work
from tests.factories import SiteSettingsFactory, WorkFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def works() -> list[Work]:
    SiteSettingsFactory.create()
    return [WorkFactory.create(title_uk=f"Робота {index}") for index in range(3)]


def test_a_shared_link_renders_on_the_server(client: Client, works: list[Work]) -> None:
    numbers = ",".join(str(work.article) for work in works[:2])

    response = client.get("/obrane/", {"a": numbers})
    body = response.content.decode()

    assert response.status_code == 200
    assert response.context["shared"] is True
    assert "Робота 0" in body
    assert "Робота 1" in body
    assert "Робота 2" not in body


def test_the_shared_link_keeps_the_order_it_was_given(client: Client, works: list[Work]) -> None:
    numbers = f"{works[2].article},{works[0].article}"

    response = client.get("/obrane/", {"a": numbers})

    assert [work.pk for work in response.context["works"]] == [works[2].pk, works[0].pk]


def test_junk_and_duplicates_fall_out_in_silence(client: Client, works: list[Work]) -> None:
    numbers = f"abc,-1,0,{works[0].article},{works[0].article},999999"

    response = client.get("/obrane/", {"a": numbers})

    assert response.status_code == 200
    assert [work.pk for work in response.context["works"]] == [works[0].pk]


def test_an_archived_work_is_dropped_from_a_collection(client: Client, works: list[Work]) -> None:
    works[0].status = Work.Status.ARCHIVED
    works[0].save()

    response = client.get("/obrane/", {"a": str(works[0].article)})

    assert list(response.context["works"]) == []


def test_a_collection_longer_than_fifty_is_cut(client: Client, works: list[Work]) -> None:
    numbers = ",".join(str(number) for number in range(1, 200))

    response = client.get("/obrane/", {"a": numbers})

    assert response.status_code == 200
    assert len(response.context["works"]) <= 50


def test_without_the_parameter_the_page_asks_the_browser(client: Client, works: list[Work]) -> None:
    body = client.get("/obrane/").content.decode()

    assert 'hx-post="/hx/favorites/"' in body
    assert "window.favoriteArticles()" in body


def test_the_fragment_returns_the_cards_for_the_given_numbers(
    client: Client, works: list[Work]
) -> None:
    response = client.post("/hx/favorites/", {"articles": str(works[1].article)})
    body = response.content.decode()

    assert response.status_code == 200
    assert "Робота 1" in body
    assert "<html" not in body


def test_the_fragment_answers_an_empty_collection_with_a_way_out(client: Client) -> None:
    SiteSettingsFactory.create()

    body = client.post("/hx/favorites/", {"articles": ""}).content.decode()

    assert 'href="/galereya/"' in body


def test_the_page_is_closed_to_crawlers(client: Client, works: list[Work]) -> None:
    body = client.get("/obrane/").content.decode()

    assert '<meta name="robots" content="noindex, follow">' in body


def test_the_page_offers_the_enquiry_and_the_link(client: Client, works: list[Work]) -> None:
    body = client.get("/obrane/").content.decode()

    assert 'id="lead-form-full"' in body
    assert "collectionLink()" in body
    assert 'name="favorites"' in body, "the enquiry carries the whole collection"


def test_the_header_counts_the_collection(client: Client, works: list[Work]) -> None:
    body = client.get("/").content.decode()

    assert 'href="/obrane/"' in body
    assert "$store.favorites.count" in body


def test_a_card_carries_the_heart(client: Client, works: list[Work]) -> None:
    body = client.get("/galereya/").content.decode()

    # The control knows which work it belongs to, is the named component of
    # section 8 rather than an expression in an attribute, and reports its
    # state from the browser instead of a value baked into the response.
    assert f'data-favorite="{works[0].article}"' in body
    assert f"favoriteButton({works[0].article})" in body
    assert ':aria-pressed="active"' in body


def test_no_registration_is_asked_for(client: Client, works: list[Work]) -> None:
    body = client.get("/obrane/").content.decode()

    assert 'type="password"' not in body
    assert "/accounts/" not in body


def test_a_collection_costs_a_fixed_number_of_queries(
    client: Client, works: list[Work], django_assert_num_queries: Any
) -> None:
    from apps.core.models import SiteSettings

    SiteSettings.load()
    numbers = ",".join(str(work.article) for work in works)

    # The works, their photos and the renditions of those photos.
    with django_assert_num_queries(2):
        client.post("/hx/favorites/", {"articles": numbers})

"""Sections 9, 10 and 16: the pages that exist in the skeleton."""

from typing import Any

import pytest
from django.test import Client
from django.urls import reverse

from apps.core.models import SiteSettings, StaticPage

pytestmark = pytest.mark.django_db


@pytest.fixture
def page() -> StaticPage:
    return StaticPage.objects.create(
        slug="pro-nas",
        title_uk="Про нас",
        title_ru="",
        body_uk="<p>Ми збираємо букети вручну</p><script>alert(1)</script>",
        seo_description_uk="Майстерня квітів",
    )


def test_static_page_opens(client: Client, page: StaticPage) -> None:
    response = client.get("/pro-nas/")

    assert response.status_code == 200
    assert "Ми збираємо букети вручну" in response.content.decode()


def test_static_page_opens_in_russian_and_falls_back(client: Client, page: StaticPage) -> None:
    response = client.get("/ru/pro-nas/")
    body = response.content.decode()

    assert response.status_code == 200
    assert "Про нас" in body


def test_unpublished_page_is_not_found(client: Client) -> None:
    StaticPage.objects.create(slug="chernetka", title_uk="Чернетка", is_published=False)

    assert client.get("/chernetka/").status_code == 404


def test_missing_page_is_not_found(client: Client) -> None:
    assert client.get("/nemaye-takoyi/").status_code == 404


def test_body_is_rendered_as_markup_without_the_stripped_tag(
    client: Client, page: StaticPage
) -> None:
    body = client.get("/pro-nas/").content.decode()

    assert "<p>Ми збираємо букети вручну</p>" in body
    assert "<script>" not in body
    assert "alert(1)" not in body


def test_static_page_carries_canonical_and_hreflang(client: Client, page: StaticPage) -> None:
    body = client.get("/pro-nas/").content.decode()

    assert '<link rel="canonical" href="http://localhost:8000/pro-nas/">' in body
    assert '<link rel="alternate" hreflang="uk" href="http://localhost:8000/pro-nas/">' in body
    assert '<link rel="alternate" hreflang="ru" href="http://localhost:8000/ru/pro-nas/">' in body
    assert (
        '<link rel="alternate" hreflang="x-default" href="http://localhost:8000/pro-nas/">' in body
    )


def test_static_page_shows_breadcrumbs(client: Client, page: StaticPage) -> None:
    body = client.get("/pro-nas/").content.decode()

    assert "BreadcrumbList" in body
    assert 'aria-current="page"' in body


def test_static_page_query_count(
    client: Client, page: StaticPage, django_assert_num_queries: Any
) -> None:
    SiteSettings.load()  # warm, exactly like a live site between deploys

    # Only the page itself: the settings singleton comes from the cache.
    with django_assert_num_queries(1):
        client.get("/pro-nas/")


def test_home_opens(client: Client) -> None:
    assert client.get(reverse("home")).status_code == 200


def test_kitchen_sink_is_hidden_without_debug(client: Client) -> None:
    assert client.get("/kitchen-sink/").status_code == 404


def test_kitchen_sink_renders_every_primitive(client: Client, settings: Any) -> None:
    settings.DEBUG = True

    response = client.get("/kitchen-sink/")
    body = response.content.decode()

    assert response.status_code == 200
    for marker in ("button.html", "picture.html", "card_work.html", "breadcrumbs.html"):
        assert marker in body


def test_the_delivery_page_opens_with_the_four_columns(client: Client) -> None:
    """Section 10. The band cannot live in the page body: bleach keeps no
    classes, so the columns would collapse into one text."""
    StaticPage.objects.create(
        slug="dostavka-i-oplata", title_uk="Доставка і оплата", body_uk="<p>Текст</p>"
    )
    settings = SiteSettings.load()
    settings.address_uk = "вул. Дворецька, 125, Рівне"
    settings.working_hours_uk = "Щодня 9:00 - 20:00"
    settings.pickup_text_uk = "Заберіть замовлення з магазину."
    settings.delivery_text_uk = "Доставка по місту."
    settings.save()

    body = client.get("/dostavka-i-oplata/").content.decode()

    for text in (
        "вул. Дворецька, 125, Рівне",
        "Щодня 9:00 - 20:00",
        "Заберіть замовлення з магазину.",
        "Доставка по місту.",
    ):
        assert text in body


def test_a_column_the_owner_left_empty_is_not_drawn(client: Client) -> None:
    StaticPage.objects.create(
        slug="dostavka-i-oplata", title_uk="Доставка і оплата", body_uk="<p>Текст</p>"
    )
    settings = SiteSettings.load()
    settings.address_uk = "вул. Дворецька, 125, Рівне"
    settings.pickup_text_uk = ""
    settings.delivery_text_uk = ""
    settings.working_hours_uk = ""
    settings.save()

    body = client.get("/dostavka-i-oplata/").content.decode()

    assert body.count('class="flex flex-col items-center gap-3') == 1


def test_another_static_page_carries_no_columns(client: Client, page: StaticPage) -> None:
    body = client.get("/pro-nas/").content.decode()

    assert 'class="flex flex-col items-center gap-3' not in body

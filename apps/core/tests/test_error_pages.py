"""Section 10, "error pages", and the legal links of section 9."""

from typing import Any

import pytest
from django.template import loader
from django.test import Client, override_settings
from django.urls import path

from apps.catalog.models import Work
from tests.factories import SiteSettingsFactory, WorkFactory


def _boom(request: Any) -> Any:  # pragma: no cover - it never returns
    raise RuntimeError("the database went away")


# A urlconf of one address, used by the 500 test below.
urlpatterns = [path("boom/", _boom)]


# --- 404 ----------------------------------------------------------------------


@pytest.mark.django_db
def test_the_404_page_offers_the_gallery_and_the_search(client: Client) -> None:
    SiteSettingsFactory.create()

    response = client.get("/nemaye-takoyi-storinky/")
    body = response.content.decode()

    assert response.status_code == 404
    assert 'href="/galereya/"' in body
    assert 'action="/poshuk/"' in body
    assert 'name="q"' in body


# --- 410 ----------------------------------------------------------------------


@pytest.mark.django_db
def test_the_410_page_shows_similar_works(client: Client) -> None:
    from tests.factories import OccasionFactory

    SiteSettingsFactory.create()
    occasion = OccasionFactory.create(slug="vesillya")
    archived = WorkFactory.create(
        title_uk="В архіві", status=Work.Status.ARCHIVED, occasions=[occasion]
    )
    WorkFactory.create(title_uk="Схожа робота", occasions=[occasion])

    response = client.get(archived.get_absolute_url())
    body = response.content.decode()

    assert response.status_code == 410
    assert "Схожа робота" in body
    assert 'href="/galereya/"' in body


# --- 500 ----------------------------------------------------------------------


def test_the_500_page_renders_without_touching_the_database() -> None:
    """No django_db mark here on purpose: any query would raise instead."""
    html = loader.render_to_string("500.html")

    assert "<html" in html
    assert "Щось пішло не так" in html


def test_the_500_page_inherits_nothing_and_carries_its_own_styles() -> None:
    html = loader.render_to_string("500.html")

    assert "<style>" in html
    assert "app.css" not in html, "a build artefact is one more thing that can be missing"
    assert "<header" not in html
    assert "<footer" not in html


@override_settings(ROOT_URLCONF=__name__)
def test_a_broken_view_answers_500_with_that_template(client: Client) -> None:
    client.raise_request_exception = False

    response = client.get("/boom/")

    assert response.status_code == 500
    assert "Щось пішло не так" in response.content.decode()


# --- the legal links ----------------------------------------------------------


@pytest.mark.django_db
def test_the_policy_is_linked_from_the_footer_the_form_and_the_banner(
    client: Client,
) -> None:
    SiteSettingsFactory.create()
    work = WorkFactory.create()

    home = client.get("/").content.decode()
    work_page = client.get(work.get_absolute_url()).content.decode()

    # The footer menu and the cookie banner are on every page.
    assert home.count('href="/polityka-konfidentsiynosti/"') >= 2
    # And the enquiry form carries its own link.
    assert 'href="/polityka-konfidentsiynosti/"' in work_page.split('id="lead-form-full"')[1]


@pytest.mark.django_db
def test_the_policy_page_itself_opens(client: Client) -> None:
    from scripts.seed import run

    run()

    response = client.get("/polityka-konfidentsiynosti/")
    body = response.content.decode()

    assert response.status_code == 200
    assert "IP-адрес" in body, "the policy explains that the address is only hashed"
    assert "cookie" in body.lower()
    assert "<script" not in body.split('class="content')[1]

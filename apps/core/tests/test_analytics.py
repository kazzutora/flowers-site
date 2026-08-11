"""Section 16: nothing is measured before the visitor agrees to it."""

import pytest
from django.test import Client

from apps.core.context_processors import CONSENT_ACCEPTED, CONSENT_COOKIE
from apps.core.models import SiteSettings
from tests.factories import SiteSettingsFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def measured() -> SiteSettings:
    site = SiteSettingsFactory.create()
    site.analytics_ga_id = "G-TESTID123"
    site.viber_url = "viber://chat?number=%2B380501112233"
    site.telegram_url = "https://t.me/example"
    site.save()
    return site


def test_without_consent_nothing_is_loaded_even_with_an_id(
    client: Client, measured: SiteSettings
) -> None:
    body = client.get("/").content.decode()

    assert "gtag" not in body
    assert "G-TESTID123" not in body


def test_with_consent_and_an_id_the_tag_is_there_once(
    client: Client, measured: SiteSettings
) -> None:
    client.cookies[CONSENT_COOKIE] = CONSENT_ACCEPTED

    body = client.get("/").content.decode()

    assert body.count("gtag") == 1
    assert "G-TESTID123" in body
    assert "js/analytics.js" in body


def test_with_consent_but_no_id_nothing_is_loaded(client: Client) -> None:
    SiteSettingsFactory.create()
    client.cookies[CONSENT_COOKIE] = CONSENT_ACCEPTED

    body = client.get("/").content.decode()

    assert "gtag" not in body
    assert "js/analytics.js" not in body


def test_choosing_necessary_only_loads_nothing(client: Client, measured: SiteSettings) -> None:
    client.cookies[CONSENT_COOKIE] = "necessary"

    assert "gtag" not in client.get("/").content.decode()


def test_the_analytics_script_is_deferred(client: Client, measured: SiteSettings) -> None:
    client.cookies[CONSENT_COOKIE] = CONSENT_ACCEPTED

    body = client.get("/").content.decode()

    assert '<script defer src="https://www.googletagmanager.com/gtag/js' in body


def test_the_banner_is_on_the_page_with_a_link_to_the_policy(
    client: Client, measured: SiteSettings
) -> None:
    body = client.get("/").content.decode()

    from pathlib import Path

    assert "cookieConsent()" in body
    assert 'href="/polityka-konfidentsiynosti/"' in body
    # The key of section 10 is the one the component actually writes.
    app_js = Path(__file__).resolve().parents[3] / "static" / "js" / "app.js"
    assert "cookie_consent:v1" in app_js.read_text(encoding="utf-8")


def test_the_events_of_section_16_are_declared_in_the_markup(
    client: Client, measured: SiteSettings
) -> None:
    from tests.factories import TagGroupFactory, WorkFactory

    WorkFactory.create()
    TagGroupFactory.create(slug="type")

    home = client.get("/").content.decode()
    gallery = client.get("/galereya/").content.decode()
    favourites = client.get("/obrane/").content.decode()

    assert 'data-analytics="phone_click"' in home
    assert 'data-analytics="viber_click"' in home
    assert 'data-analytics="telegram_click"' in home
    assert 'data-analytics="filter_apply"' in gallery
    assert 'data-analytics="lead_submit"' in favourites

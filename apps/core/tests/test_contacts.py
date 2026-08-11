"""Section 10, "contacts", and the LocalBusiness markup of section 16."""

import pytest
from django.test import Client

from apps.core.models import SiteSettings
from tests.factories import SiteSettingsFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def site() -> SiteSettings:
    site = SiteSettingsFactory.create()
    site.address_uk = "вул. Квіткова, 1"
    site.landmark_uk = "навпроти пошти"
    site.parking_uk = "паркування у дворі"
    site.working_hours_uk = "Щодня 9:00 - 20:00"
    site.email = "hello@example.com"
    site.map_embed_url = "https://www.google.com/maps/embed?pb=demo"
    site.map_directions_url = "https://maps.google.com/?daddr=demo"
    site.viber_url = "viber://chat?number=%2B380501112233"
    site.save()
    return site


def test_the_contacts_page_opens(client: Client, site: SiteSettings) -> None:
    response = client.get("/kontakty/")

    assert response.status_code == 200
    assert "вул. Квіткова, 1" in response.content.decode()


def test_everything_on_it_comes_from_the_admin(client: Client, site: SiteSettings) -> None:
    body = client.get("/kontakty/").content.decode()

    assert "навпроти пошти" in body
    assert "паркування у дворі" in body
    assert "Щодня 9:00 - 20:00" in body
    assert "hello@example.com" in body


def test_editing_the_hours_shows_up_immediately(client: Client, site: SiteSettings) -> None:
    site.working_hours_uk = "Пн-Пт 10:00 - 19:00"
    site.save()

    assert "Пн-Пт 10:00 - 19:00" in client.get("/kontakty/").content.decode()


def test_the_map_waits_until_it_is_scrolled_to(client: Client, site: SiteSettings) -> None:
    body = client.get("/kontakty/").content.decode()

    assert 'src="https://www.google.com/maps/embed?pb=demo"' in body
    assert 'loading="lazy"' in body


def test_the_directions_button_opens_the_navigation(client: Client, site: SiteSettings) -> None:
    body = client.get("/kontakty/").content.decode()

    assert 'href="https://maps.google.com/?daddr=demo"' in body


def test_local_business_carries_the_phone_and_the_address(
    client: Client, site: SiteSettings
) -> None:
    body = client.get("/kontakty/").content.decode()

    assert '"@type": "LocalBusiness"' in body
    assert '"telephone": "+380501112233"' in body
    assert '"streetAddress": "вул. Квіткова, 1"' in body
    assert '"openingHours": "Щодня 9:00 - 20:00"' in body


def test_the_enquiry_form_is_on_the_page(client: Client, site: SiteSettings) -> None:
    body = client.get("/kontakty/").content.decode()

    assert 'id="lead-form-full"' in body
    assert 'action="/hx/lead/"' in body


def test_the_menu_now_reaches_the_contacts(client: Client, site: SiteSettings) -> None:
    body = client.get("/").content.decode()

    assert 'href="/kontakty/"' in body


def test_the_page_answers_in_russian_too(client: Client, site: SiteSettings) -> None:
    site.address_ru = "ул. Цветочная, 1"
    site.save()

    body = client.get("/ru/kontakty/").content.decode()

    assert "ул. Цветочная, 1" in body

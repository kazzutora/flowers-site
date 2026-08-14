"""Section 10, "home page", and the LocalBusiness markup of section 16."""

import pytest
from django.test import Client

from apps.catalog.models import Work
from apps.core.models import SiteSettings
from tests.factories import (
    HowToStepFactory,
    OccasionFactory,
    SiteSettingsFactory,
    WorkFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def filled_home() -> SiteSettings:
    site = SiteSettingsFactory.create()
    site.hero_title_uk = "Квіти, які запамʼятовують"
    site.address_uk = "вул. Квіткова, 1"
    site.working_hours_uk = "Щодня 9:00 - 20:00"
    site.instagram_url = "https://instagram.com/example"
    site.save()

    OccasionFactory.create(slug="vesillya", name_uk="Весілля", show_on_home=True)
    OccasionFactory.create(slug="tayemnyi", name_uk="Таємний", is_active=False)
    OccasionFactory.create(slug="ne-na-holovniy", name_uk="Не на головній", show_on_home=False)
    HowToStepFactory.create(title_uk="Оберіть роботу")
    WorkFactory.create(title_uk="Білий букет", status=Work.Status.PUBLISHED)
    WorkFactory.create(title_uk="Чернетка", status=Work.Status.DRAFT)
    return site


def test_the_home_page_opens(client: Client, filled_home: SiteSettings) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Квіти, які запамʼятовують" in response.content.decode()


def test_a_tile_leads_into_its_section(client: Client, filled_home: SiteSettings) -> None:
    body = client.get("/").content.decode()

    assert 'href="/galereya/vesillya/"' in body
    assert "Весілля" in body


def test_tiles_follow_the_admin_switches(client: Client, filled_home: SiteSettings) -> None:
    body = client.get("/").content.decode()

    assert "Таємний" not in body
    assert "Не на головній" not in body


def test_only_published_works_reach_the_fresh_block(
    client: Client, filled_home: SiteSettings
) -> None:
    body = client.get("/").content.decode()

    assert "Білий букет" in body
    assert "Чернетка" not in body


def test_the_hero_is_eager_while_the_tiles_are_lazy(
    client: Client, filled_home: SiteSettings
) -> None:
    from django.core.files.uploadedfile import SimpleUploadedFile

    from tests.factories import photo_bytes

    filled_home.hero_image = SimpleUploadedFile("hero.jpg", photo_bytes(), "image/jpeg")
    filled_home.save()
    tile = OccasionFactory.create(slug="vesillya")
    tile.cover = SimpleUploadedFile("tile.jpg", photo_bytes(), "image/jpeg")
    tile.save()

    body = client.get("/").content.decode()

    assert 'fetchpriority="high"' in body
    assert 'loading="lazy"' in body


def _with_photos(settings: SiteSettings, tiles: int) -> None:
    from django.core.files.uploadedfile import SimpleUploadedFile

    from tests.factories import photo_bytes

    settings.hero_image = SimpleUploadedFile("hero.jpg", photo_bytes(), "image/jpeg")
    settings.save()
    for number in range(tiles):
        tile = OccasionFactory.create(slug=f"pryvid-hero-{number}")
        tile.cover = SimpleUploadedFile(f"tile{number}.jpg", photo_bytes(), "image/jpeg")
        tile.save()


def test_the_hero_fan_holds_three_cards_at_most(client: Client, filled_home: SiteSettings) -> None:
    """Section 12: the fan is three cards, however many tiles the shop has."""
    _with_photos(filled_home, tiles=5)

    body = client.get("/").content.decode()

    # One modifier per card: `hero-fan-card` alone also matches the base class.
    assert body.count("hero-fan-card--") == 3


def test_the_hero_fan_shortens_when_there_are_no_photos(
    client: Client, filled_home: SiteSettings
) -> None:
    body = client.get("/").content.decode()

    assert "hero-fan-card--" not in body
    # The words still carry the page: only the photographs are missing.
    assert "Квіти, які запамʼятовують" in body


def test_the_hero_fan_is_hidden_from_a_screen_reader(
    client: Client, filled_home: SiteSettings
) -> None:
    """The fan is decoration; the heading and the subtitle carry the meaning."""
    _with_photos(filled_home, tiles=2)

    body = client.get("/").content.decode()

    assert 'class="hero-fan" x-data="heroFan" aria-hidden="true"' in body


def test_an_empty_block_is_not_rendered_at_all(client: Client, filled_home: SiteSettings) -> None:
    """With no reviews and no posts, neither section appears.

    The assertions look for the links that only live inside those blocks: the
    words themselves are also in the menu, which is a different thing.
    """
    body = client.get("/").content.decode()

    assert "Всі відгуки" not in body
    assert "Всі статті" not in body


def test_there_is_a_button_to_instagram_and_no_feed(
    client: Client, filled_home: SiteSettings
) -> None:
    body = client.get("/").content.decode()

    assert "https://instagram.com/example" in body
    assert "instagram.com/embed" not in body


def test_local_business_carries_the_phone_from_the_settings(
    client: Client, filled_home: SiteSettings
) -> None:
    body = client.get("/").content.decode()

    assert '"@type": "LocalBusiness"' in body
    assert '"telephone": "+380501112233"' in body
    assert "вул. Квіткова, 1" in body


def test_the_home_page_costs_the_same_whatever_the_number_of_works(
    client: Client, filled_home: SiteSettings
) -> None:
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    def count() -> int:
        with CaptureQueriesContext(connection) as captured:
            client.get("/")
        return len(captured.captured_queries)

    SiteSettings.load()  # warm, exactly like a live site between deploys
    with_one = count()
    for index in range(20):
        WorkFactory.create(title_uk=f"Робота {index}")
    with_twenty_one = count()

    assert with_one == with_twenty_one
    assert with_twenty_one <= 8

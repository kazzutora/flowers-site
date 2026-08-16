"""Section 18: one set of fixtures, safe to run again."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.blog.models import Post
from apps.catalog.models import Occasion, Tag, TagGroup, Work, WorkImage
from apps.core.models import HowToStep, SiteSettings, StaticPage
from apps.reviews.models import Review
from scripts.seed import run
from tests.factories import photo_bytes

pytestmark = pytest.mark.django_db


def test_seed_fills_the_core_models() -> None:
    counts = run()

    assert counts["site_settings"] == 1
    assert counts["static_pages"] == 4
    assert counts["how_to_steps"] == 3
    assert set(StaticPage.objects.values_list("slug", flat=True)) == {
        "pro-nas",
        "dostavka-i-oplata",
        "faq",
        "polityka-konfidentsiynosti",
    }


def test_seed_fills_the_catalog() -> None:
    counts = run()

    assert counts["occasions"] == 7
    assert counts["tag_groups"] == 4
    assert counts["works"] == 5
    assert counts["work_images"] == 11
    assert counts["reviews"] == 5
    assert counts["posts"] == 3
    assert set(TagGroup.objects.values_list("slug", flat=True)) == {
        "type",
        "color",
        "flower",
        "season",
    }
    assert "vesillya" in set(Occasion.objects.values_list("slug", flat=True))
    assert Work.published.count() == 5


def test_seed_is_idempotent() -> None:
    first = run()
    second = run()

    assert first == second
    assert SiteSettings.objects.count() == 1
    assert StaticPage.objects.count() == 4
    assert HowToStep.objects.count() == 3
    assert Occasion.objects.count() == 7
    assert Tag.objects.count() == 20
    assert Work.objects.count() == 5
    assert WorkImage.objects.count() == 11
    assert Review.objects.count() == 5
    assert Review.published.count() == 5
    assert Post.objects.count() == 3
    assert Post.published.count() == 3


def test_seed_gives_every_occasion_a_cover_and_the_home_a_hero() -> None:
    run()

    assert not Occasion.objects.filter(cover="").exists()
    assert SiteSettings.load().hero_image


def test_seed_gives_every_post_a_cover() -> None:
    run()

    assert not Post.objects.filter(cover="").exists()


def test_seed_corrects_working_hours_left_over_from_an_older_run() -> None:
    """The hours are shop data, like the name and the address: they are assigned."""
    run()
    site = SiteSettings.load()
    site.working_hours_uk = "Щодня 9:00 - 20:00"
    site.working_hours_ru = "Ежедневно 9:00 - 20:00"
    site.save()

    run()

    refreshed = SiteSettings.load()
    assert refreshed.working_hours_uk == "Цілодобово, без вихідних"
    assert refreshed.working_hours_ru == "Круглосуточно, без выходных"


def test_seed_carries_the_real_contacts() -> None:
    """The phones and the Instagram account are shop data, so they are assigned."""
    run()
    site = SiteSettings.load()
    site.phone_primary = "+380501112233"
    site.phone_secondary = ""
    site.instagram_url = "https://instagram.com/example"
    site.save()

    run()

    refreshed = SiteSettings.load()
    assert str(refreshed.phone_primary) == "+380992050565"
    assert str(refreshed.phone_secondary) == "+380972050565"
    assert refreshed.instagram_url == "https://www.instagram.com/kvitkova_prymkha"


def test_seeding_again_keeps_a_photo_the_owner_uploaded() -> None:
    """The tiles ship with stand-ins; the owner's own work outranks them."""
    run()
    occasion = Occasion.objects.get(slug="vesillya")
    occasion.cover = SimpleUploadedFile("own.jpg", photo_bytes(1200, 1500), "image/jpeg")
    occasion.save()
    uploaded = occasion.cover.name

    run()

    assert Occasion.objects.get(slug="vesillya").cover.name == uploaded


def test_seeded_pages_are_sanitised_and_published() -> None:
    run()

    page = StaticPage.objects.get(slug="pro-nas")

    assert page.is_published is True
    assert "<script>" not in page.body_uk

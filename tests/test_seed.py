"""Section 18: one set of fixtures, safe to run again."""

import pytest

from apps.blog.models import Post
from apps.catalog.models import Occasion, Tag, TagGroup, Work, WorkImage
from apps.core.models import HowToStep, SiteSettings, StaticPage
from apps.reviews.models import Review
from scripts.seed import run

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
    assert counts["works"] == 30
    assert counts["work_images"] == 30
    assert counts["reviews"] == 5
    assert counts["posts"] == 3
    assert set(TagGroup.objects.values_list("slug", flat=True)) == {
        "type",
        "color",
        "flower",
        "season",
    }
    assert "vesillya" in set(Occasion.objects.values_list("slug", flat=True))
    assert Work.published.count() == 30


def test_seed_is_idempotent() -> None:
    first = run()
    second = run()

    assert first == second
    assert SiteSettings.objects.count() == 1
    assert StaticPage.objects.count() == 4
    assert HowToStep.objects.count() == 3
    assert Occasion.objects.count() == 7
    assert Tag.objects.count() == 20
    assert Work.objects.count() == 30
    assert WorkImage.objects.count() == 30
    assert Review.objects.count() == 5
    assert Review.published.count() == 5
    assert Post.objects.count() == 3
    assert Post.published.count() == 3


def test_seeded_pages_are_sanitised_and_published() -> None:
    run()

    page = StaticPage.objects.get(slug="pro-nas")

    assert page.is_published is True
    assert "<script>" not in page.body_uk

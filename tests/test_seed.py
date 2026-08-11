"""Section 18: one set of fixtures, safe to run again."""

import pytest

from apps.core.models import HowToStep, SiteSettings, StaticPage
from scripts.seed import run

pytestmark = pytest.mark.django_db


def test_seed_fills_the_core_models() -> None:
    counts = run()

    assert counts == {"site_settings": 1, "static_pages": 4, "how_to_steps": 3}
    assert set(StaticPage.objects.values_list("slug", flat=True)) == {
        "pro-nas",
        "dostavka-i-oplata",
        "faq",
        "polityka-konfidentsiynosti",
    }


def test_seed_is_idempotent() -> None:
    first = run()
    second = run()

    assert first == second
    assert SiteSettings.objects.count() == 1
    assert StaticPage.objects.count() == 4
    assert HowToStep.objects.count() == 3


def test_seeded_pages_are_sanitised_and_published() -> None:
    run()

    page = StaticPage.objects.get(slug="pro-nas")

    assert page.is_published is True
    assert "<script>" not in page.body_uk

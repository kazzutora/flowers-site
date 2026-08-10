"""Sections 4.7-4.9 and 11 of tech.md."""

from datetime import timedelta
from typing import Any

import pytest
from django.utils import timezone
from django.utils.translation import override

from apps.core.models import HowToStep, SiteSettings, StaticPage

pytestmark = pytest.mark.django_db


def test_a_second_instance_does_not_create_a_second_row() -> None:
    SiteSettings.objects.create(analytics_ga_id="G-FIRST")
    SiteSettings.objects.create(analytics_ga_id="G-SECOND")

    assert SiteSettings.objects.count() == 1
    assert SiteSettings.objects.get().pk == 1
    assert SiteSettings.objects.get().analytics_ga_id == "G-SECOND"


def test_the_singleton_cannot_be_deleted() -> None:
    settings = SiteSettings.load()

    with pytest.raises(NotImplementedError):
        settings.delete()

    assert SiteSettings.objects.count() == 1


def test_load_serves_the_second_read_from_cache(django_assert_num_queries: Any) -> None:
    SiteSettings.load()

    with django_assert_num_queries(0):
        assert SiteSettings.load().pk == 1


def test_saving_invalidates_the_cache() -> None:
    settings = SiteSettings.load()

    settings.phone_primary = "+380501112233"
    settings.save()

    assert str(SiteSettings.load().phone_primary) == "+380501112233"


def test_unreachable_cache_does_not_break_reading(broken_cache: None) -> None:
    SiteSettings.objects.create(analytics_ga_id="G-LIVE")

    assert SiteSettings.load().analytics_ga_id == "G-LIVE"


def test_unreachable_cache_does_not_break_writing(broken_cache: None) -> None:
    settings = SiteSettings.load()
    settings.analytics_ga_id = "G-NEW"

    settings.save()

    assert SiteSettings.objects.get().analytics_ga_id == "G-NEW"


@pytest.mark.parametrize(
    ("enabled", "hours_from_now", "expected"),
    [
        (True, None, True),
        (True, 1, True),
        (True, -1, False),
        (False, 1, False),
        (False, None, False),
    ],
)
def test_banner_visibility(enabled: bool, hours_from_now: int | None, expected: bool) -> None:
    until = None if hours_from_now is None else timezone.now() + timedelta(hours=hours_from_now)
    settings = SiteSettings(banner_enabled=enabled, banner_until=until)

    assert settings.banner_is_active is expected


def test_banner_hash_follows_text_and_date() -> None:
    until = timezone.now()
    first = SiteSettings(banner_text_uk="Знижка", banner_until=until).banner_dismiss_hash

    assert SiteSettings(banner_text_uk="Знижка", banner_until=until).banner_dismiss_hash == first
    assert SiteSettings(banner_text_uk="Інша", banner_until=until).banner_dismiss_hash != first
    assert SiteSettings(banner_text_uk="Знижка").banner_dismiss_hash != first


def test_translation_falls_back_to_ukrainian() -> None:
    page = StaticPage(slug="pro-nas", title_uk="Про нас", title_ru="")

    with override("ru"):
        assert page.tr("title") == "Про нас"


def test_translation_uses_the_active_language() -> None:
    page = StaticPage(slug="pro-nas", title_uk="Про нас", title_ru="О нас")

    with override("ru"):
        assert page.tr("title") == "О нас"
    with override("uk"):
        assert page.tr("title") == "Про нас"


def test_static_page_body_is_sanitized_on_save() -> None:
    page = StaticPage.objects.create(
        slug="pro-nas",
        title_uk="Про нас",
        body_uk="<p>Вітаємо</p><script>alert(1)</script>",
    )

    page.refresh_from_db()
    assert "<script>" not in page.body_uk
    assert "alert(1)" not in page.body_uk
    assert "<p>Вітаємо</p>" in page.body_uk


def test_how_to_steps_are_ordered() -> None:
    HowToStep.objects.create(order=2, title_uk="Другий")
    HowToStep.objects.create(order=1, title_uk="Перший")

    assert [step.title_uk for step in HowToStep.objects.all()] == ["Перший", "Другий"]

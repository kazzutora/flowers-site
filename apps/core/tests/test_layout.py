"""Section 10: header, mobile menu, banner and the modes that switch them."""

from datetime import timedelta
from typing import Any

import pytest
from django.test import Client
from django.utils import timezone

from apps.core.models import SiteSettings, StaticPage
from apps.core.navigation import MAIN_MENU, NavItem, resolve

pytestmark = pytest.mark.django_db


@pytest.fixture
def settings_row() -> SiteSettings:
    row = SiteSettings.load()
    row.phone_primary = "+380501112233"
    row.viber_url = "viber://chat?number=%2B380501112233"
    row.telegram_url = "https://t.me/example"
    row.save()
    return row


def test_header_keeps_the_menu_behind_a_button_on_mobile(
    client: Client, settings_row: SiteSettings
) -> None:
    body = client.get("/").content.decode()

    assert 'id="mobile-menu"' in body
    assert 'aria-label="Відкрити меню"' in body or "Open menu" in body
    # The panel is a dialog and the button points at it (section 12 of
    # FRONTEND.md). aria-expanded is bound to the state, never written flat:
    # a static value lies the moment the panel opens.
    assert 'role="dialog"' in body
    assert 'aria-modal="true"' in body
    assert 'aria-controls="mobile-menu"' in body
    assert ":aria-expanded=" in body


def test_header_has_no_floating_call_button(client: Client, settings_row: SiteSettings) -> None:
    body = client.get("/").content.decode()

    assert "fixed bottom-" not in body


def test_language_switch_keeps_path_and_query(client: Client, settings_row: SiteSettings) -> None:
    StaticPage.objects.create(slug="pro-nas", title_uk="Про нас")

    body = client.get("/pro-nas/?color=bilyi").content.decode()

    assert 'href="/ru/pro-nas/?color=bilyi"' in body


def test_phone_stays_clickable_when_orders_are_closed(
    client: Client, settings_row: SiteSettings
) -> None:
    settings_row.accepting_orders = False
    settings_row.not_accepting_message_uk = "Зараз не приймаємо замовлення"
    settings_row.save()

    body = client.get("/").content.decode()

    assert 'href="tel:+380501112233"' in body
    assert "Зараз не приймаємо замовлення" in body


def test_banner_shows_with_its_dismiss_hash(client: Client, settings_row: SiteSettings) -> None:
    settings_row.banner_enabled = True
    settings_row.banner_text_uk = "Знижка на весільні букети"
    settings_row.banner_until = timezone.now() + timedelta(days=1)
    settings_row.save()

    body = client.get("/").content.decode()

    assert "Знижка на весільні букети" in body
    assert f"banner('{settings_row.banner_dismiss_hash}')" in body


def test_expired_banner_is_not_rendered(client: Client, settings_row: SiteSettings) -> None:
    settings_row.banner_enabled = True
    settings_row.banner_text_uk = "Стара акція"
    settings_row.banner_until = timezone.now() - timedelta(minutes=1)
    settings_row.save()

    assert "Стара акція" not in client.get("/").content.decode()


def test_menu_is_data_and_skips_urls_that_do_not_exist_yet() -> None:
    resolved = resolve(MAIN_MENU)
    labels = [item.label for item in resolved]

    assert "Про нас" in labels or "About" in labels
    assert all(item.url.startswith("/") for item in resolved)


def test_adding_a_menu_item_needs_no_template_change(
    client: Client, settings_row: SiteSettings, monkeypatch: pytest.MonkeyPatch
) -> None:
    extended = (*MAIN_MENU, NavItem("Питання", "static_page", {"slug": "faq"}))
    monkeypatch.setattr("apps.core.navigation.MAIN_MENU", extended)

    body = client.get("/").content.decode()

    assert 'href="/faq/"' in body


def test_footer_links_to_the_privacy_policy(client: Client, settings_row: SiteSettings) -> None:
    body = client.get("/").content.decode()

    assert 'href="/polityka-konfidentsiynosti/"' in body


def test_static_assets_are_local(client: Client, settings_row: SiteSettings, settings: Any) -> None:
    body = client.get("/").content.decode()

    assert "https://cdn" not in body
    assert "fonts.googleapis.com" not in body
    assert "/static/js/htmx.min.js" in body
    assert "/static/js/alpine.min.js" in body

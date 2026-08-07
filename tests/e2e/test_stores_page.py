"""Reference-vertical E2E smoke test — DEV.md S0.9 ("все четыре типа
тестов хотя бы на эталонной вертикали"). Runs against a real browser via
Playwright + a live Django server (pytest-django's live_server fixture).
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

pytestmark = [pytest.mark.e2e, pytest.mark.django_db]


def test_stores_page_shows_store_cards(
    page: Page,
    live_server: object,
    django_db_setup: object,
    django_db_blocker: object,
) -> None:
    with django_db_blocker.unblock():
        from apps.stores.tests.factories import StoreFactory

        StoreFactory(slug="centr", name="Центр")

    page.goto(f"{live_server.url}/stores/")

    expect(page.get_by_role("heading", name="Наші магазини")).to_be_visible()
    store_card = page.locator('[data-testid="store-card"]').first
    expect(store_card).to_be_visible()
    expect(store_card.get_by_role("heading", name="Центр")).to_be_visible()

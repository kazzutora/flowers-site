"""Section 9 in a real browser: filtering, the address bar and the Back button.

Nothing below asserts on markup for its own sake. What is being proved is that
a filtered gallery has an address, that the address survives being shared, and
that Back returns the previous set - the three things htmx can quietly break.
"""

from typing import Any

import pytest
from playwright.sync_api import expect

from apps.catalog.models import TagGroup, Work
from tests.factories import (
    OccasionFactory,
    SiteSettingsFactory,
    TagFactory,
    TagGroupFactory,
    WorkFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def catalog(db: Any) -> dict[str, Any]:
    SiteSettingsFactory.create()
    wedding = OccasionFactory.create(slug="vesillya", name_uk="Весілля")

    types = TagGroupFactory.create(slug="type", name_uk="Тип", order=1)
    colors = TagGroupFactory.create(
        slug="color", name_uk="Колір", order=2, filter_kind=TagGroup.FilterKind.COLOR_SWATCH
    )
    bouquet = TagFactory.create(group=types, slug="buket", name_uk="Букет")
    basket = TagFactory.create(group=types, slug="koshyk", name_uk="Кошик")
    white = TagFactory.create(group=colors, slug="bilyi", name_uk="Білий", color_hex="#FFFFFF")

    WorkFactory.create(
        title_uk="Білий букет",
        status=Work.Status.PUBLISHED,
        occasions=[wedding],
        tags=[bouquet, white],
    )
    WorkFactory.create(title_uk="Кошик польовий", status=Work.Status.PUBLISHED, tags=[basket])
    return {"wedding": wedding}


def _cards(page: Any) -> Any:
    return page.locator("#gallery-grid article")


def test_filtering_changes_the_address_and_back_returns(
    profile: Any, live_server: Any, catalog: dict[str, Any]
) -> None:
    page = profile
    page.goto(f"{live_server.url}/galereya/")
    expect(_cards(page)).to_have_count(2)

    # On a phone the panel is a drawer; on a desktop it is always open.
    filters_button = page.get_by_role("button", name="Фільтри")
    if filters_button.is_visible():
        filters_button.click()

    page.locator('input[name="type"][value="buket"]:visible').first.check()

    expect(_cards(page)).to_have_count(1)
    expect(page).to_have_url(f"{live_server.url}/galereya/?type=buket")
    expect(page.get_by_text("Білий букет")).to_be_visible()

    page.go_back()

    expect(page).to_have_url(f"{live_server.url}/galereya/")
    expect(_cards(page)).to_have_count(2)


def test_a_filtered_address_opens_the_same_set_elsewhere(
    profile: Any, browser: Any, live_server: Any, catalog: dict[str, Any]
) -> None:
    """The link is the point: it gets sent to a friend, not re-derived."""
    page = profile
    page.goto(f"{live_server.url}/galereya/?type=buket")
    expect(_cards(page)).to_have_count(1)

    fresh = browser.new_context()
    try:
        stranger = fresh.new_page()
        stranger.goto(f"{live_server.url}/galereya/?type=buket")
        expect(stranger.locator("#gallery-grid article")).to_have_count(1)
        expect(stranger.get_by_text("Білий букет")).to_be_visible()
    finally:
        fresh.close()


def test_an_occasion_is_a_page_of_its_own(
    profile: Any, live_server: Any, catalog: dict[str, Any]
) -> None:
    """Section 1: an occasion lives in the path, not in the query."""
    page = profile
    page.goto(f"{live_server.url}/galereya/vesillya/")

    expect(page).to_have_url(f"{live_server.url}/galereya/vesillya/")
    expect(_cards(page)).to_have_count(1)

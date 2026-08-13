"""Section 10, "favourites", in a real browser.

Two works go into the collection, the page shows them, the link is copied and
opened in a clean context - which is the whole point of the feature: the
visitor sends the address to a friend, or dictates the numbers on the phone.
"""

from typing import Any

import pytest
from playwright.sync_api import expect

from apps.catalog.filters import parse_articles
from apps.catalog.models import Work
from tests.factories import SiteSettingsFactory, WorkFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def works(db: Any) -> list[Work]:
    SiteSettingsFactory.create()
    return [
        WorkFactory.create(title_uk=f"Робота {index}", status=Work.Status.PUBLISHED)
        for index in range(3)
    ]


def test_two_works_travel_to_another_browser(
    profile: Any, browser: Any, live_server: Any, works: list[Work]
) -> None:
    page = profile
    page.context.grant_permissions(["clipboard-read", "clipboard-write"])

    page.goto(f"{live_server.url}/galereya/")
    hearts = page.locator('button[aria-label="В обране"]')
    expect(hearts.first).to_be_visible()

    hearts.nth(0).click()
    hearts.nth(1).click()

    counter = page.locator('a[href="/obrane/"] span')
    expect(counter).to_have_text("2")

    page.goto(f"{live_server.url}/obrane/")
    cards = page.locator("#favorites-grid article")
    expect(cards).to_have_count(2)

    page.get_by_role("button", name="Скопіювати посилання на добірку").click()
    copied = page.evaluate("navigator.clipboard.readText()")

    assert "/obrane/?a=" in copied
    numbers = copied.split("?a=")[1].split(",")
    assert len(numbers) == 2

    # A clean context: no localStorage, no cookies, nothing but the address.
    fresh = browser.new_context()
    try:
        stranger = fresh.new_page()
        stranger.goto(copied.replace("http://localhost", live_server.url.rsplit(":", 1)[0]))
        expect(stranger.locator("#favorites-grid article")).to_have_count(2)
        assert stranger.evaluate("window.localStorage.getItem('favorites')") is None
    finally:
        fresh.close()


def test_the_collection_survives_a_reload(
    profile: Any, live_server: Any, works: list[Work]
) -> None:
    page = profile
    page.goto(f"{live_server.url}/galereya/")
    page.locator('button[aria-label="В обране"]').first.click()

    page.reload()

    expect(page.locator('a[href="/obrane/"] span')).to_have_text("1")


def test_an_empty_collection_offers_the_gallery(
    profile: Any, live_server: Any, works: list[Work]
) -> None:
    page = profile
    page.goto(f"{live_server.url}/obrane/")

    expect(page.get_by_role("link", name="До галереї")).to_be_visible()


def test_the_browser_normalises_the_collection_exactly_as_the_server_does(
    profile: Any, live_server: Any, works: list[Work]
) -> None:
    """Section 9: the same rules on both sides, checked by a test.

    The browser list ends up in `?a=` and in the enquiry, so a client that
    accepted more than the server would show a collection the server refuses to
    render, and one that accepted less would silently drop works.
    """
    junk = ["7.0", "0x10", " 147 ", 147, -5, 0, "abc", 152, 152]

    page = profile
    page.goto(f"{live_server.url}/galereya/")
    page.evaluate("(list) => window.localStorage.setItem('favorites', JSON.stringify(list))", junk)
    page.reload()
    in_browser = page.evaluate("Alpine.store('favorites').items")

    on_server = parse_articles(",".join(str(value) for value in junk))

    assert in_browser == on_server == [147, 152]


def test_a_shared_collection_is_the_one_the_enquiry_carries(
    profile: Any, live_server: Any, works: list[Work]
) -> None:
    """Section 10: an enquiry sent from somebody else's link is about the works
    on the screen, not about whatever this browser happens to be holding."""
    shared = [work.article for work in works[:2]]

    page = profile
    page.goto(f"{live_server.url}/galereya/")
    page.evaluate("() => window.localStorage.setItem('favorites', JSON.stringify([999999]))")
    page.goto(f"{live_server.url}/obrane/?a={','.join(str(a) for a in shared)}")
    page.locator("form[id^=lead-form]").first.evaluate(
        "form => form.dispatchEvent(new Event('submit', {bubbles: true}))"
    )

    field = page.locator("form[id^=lead-form] input[data-favorites]").first
    assert field.input_value() == ",".join(str(a) for a in shared)

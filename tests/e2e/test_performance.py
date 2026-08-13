"""Section 16: LCP up to 2.5 s on 4G, CLS up to 0.1.

Measured, not asserted from first principles. The numbers come from the same
browser APIs Lighthouse reads, with the network throttled through the DevTools
protocol to the 4G profile. What this cannot reproduce is a real network path
to a real server, so treat it as the floor: if the page misses the budget here,
it has no chance in the field.
"""

from typing import Any

import pytest

from apps.catalog.models import Work
from apps.catalog.tasks import generate_renditions
from tests.factories import (
    OccasionFactory,
    SiteSettingsFactory,
    WorkFactory,
    WorkImageFactory,
    photo_bytes,
)

pytestmark = pytest.mark.django_db

# Lighthouse's "Slow 4G": 1.6 Mbit down, 750 kbit up, 150 ms round trip.
FOUR_G = {
    "offline": False,
    "downloadThroughput": int(1.6 * 1024 * 1024 / 8),
    "uploadThroughput": int(750 * 1024 / 8),
    "latency": 150,
}

LCP_BUDGET_MS = 2500
CLS_BUDGET = 0.1

MEASURE = """
() => new Promise((resolve) => {
  let lcp = 0;
  let cls = 0;
  new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) lcp = entry.startTime;
  }).observe({ type: 'largest-contentful-paint', buffered: true });
  new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) if (!entry.hadRecentInput) cls += entry.value;
  }).observe({ type: 'layout-shift', buffered: true });
  // Give the page a moment to settle: a shift that arrives late still counts.
  setTimeout(() => resolve({ lcp, cls }), 1500);
})
"""


@pytest.fixture
def filled_site(db: Any) -> None:
    site = SiteSettingsFactory.create()
    from django.core.files.uploadedfile import SimpleUploadedFile

    site.hero_image = SimpleUploadedFile("hero.jpg", photo_bytes(2000, 2500), "image/jpeg")
    site.save()

    occasion = OccasionFactory.create(slug="vesillya", name_uk="Весілля")
    for index in range(12):
        work = WorkFactory.create(
            title_uk=f"Робота {index}", status=Work.Status.PUBLISHED, occasions=[occasion]
        )
        image = WorkImageFactory.create(work=work)
        # Real renditions: a page of skeletons would flatter the measurement.
        generate_renditions(payload={"work_image_id": image.pk})


def _measure(page: Any, url: str) -> dict[str, float]:
    """Warm first, measure second.

    The first hit of a page compiles its templates and pulls every image off
    disk for the first time. That cost belongs to the server's first minute of
    life, not to the visitor the budget is about.
    """
    page.goto(url, wait_until="load")

    session = page.context.new_cdp_session(page)
    session.send("Network.enable")
    session.send("Network.emulateNetworkConditions", FOUR_G)
    try:
        page.goto(url, wait_until="load")
        return page.evaluate(MEASURE)
    finally:
        session.detach()


@pytest.mark.parametrize("path", ["/", "/galereya/"])
def test_the_page_stays_inside_the_budget_on_4g(
    profile: Any, live_server: Any, filled_site: None, path: str
) -> None:
    measured = _measure(profile, f"{live_server.url}{path}")
    # The numbers land in the assertion message, which is where they are read.
    assert measured["lcp"] <= LCP_BUDGET_MS, f"{path}: LCP {measured['lcp']:.0f} ms"
    assert measured["cls"] <= CLS_BUDGET, f"{path}: CLS {measured['cls']:.3f}"


def test_nothing_is_loaded_from_a_third_party(
    profile: Any, live_server: Any, filled_site: None
) -> None:
    """Section 13: fonts are local and there is no CDN. A third party request
    is both a privacy leak and the easiest way to lose the LCP budget."""
    outside: list[str] = []
    profile.on(
        "request",
        lambda request: (
            outside.append(request.url)
            if not request.url.startswith(live_server.url) and not request.url.startswith("data:")
            else None
        ),
    )

    profile.goto(f"{live_server.url}/", wait_until="load")

    assert outside == []


def test_the_grid_reserves_its_space(profile: Any, live_server: Any, filled_site: None) -> None:
    """CLS is zero by construction when every card has a fixed ratio and every
    image carries its width and height (section 10)."""
    profile.goto(f"{live_server.url}/galereya/", wait_until="load")

    images = profile.locator("#gallery-grid img")
    assert images.count() > 0
    for index in range(images.count()):
        image = images.nth(index)
        assert image.get_attribute("width"), "an image without width can shift the page"
        assert image.get_attribute("height")

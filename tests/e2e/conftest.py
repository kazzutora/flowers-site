"""End to end scenarios run against a real browser.

They are skipped, not failed, when the browser binary is missing: a laptop
without `playwright install` still gets a green suite, while CI runs them for
real.
"""

import subprocess
import sys
from collections.abc import Iterator
from typing import Any

import pytest

# Section 13 starts the design at 360px; the desktop profile is the width the
# gallery switches to four columns at.
PROFILES: dict[str, dict[str, int]] = {
    "mobile": {"width": 390, "height": 844},
    "desktop": {"width": 1440, "height": 900},
}


def pytest_collection_modifyitems(items: list[Any]) -> None:
    for item in items:
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)


@pytest.fixture(scope="session", autouse=True)
def skip_without_chromium() -> None:
    """Skip instead of failing when nobody ran `playwright install`.

    The probe runs in a subprocess on purpose: starting Playwright in this
    thread would leave an event loop behind and Django would then refuse every
    ORM call in the suite.
    """
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            "from playwright.sync_api import sync_playwright\n"
            "with sync_playwright() as p: p.chromium.launch().close()",
        ],
        capture_output=True,
        check=False,
    )
    if probe.returncode != 0:  # pragma: no cover - only without the browser
        pytest.skip("chromium is not installed: run `playwright install chromium`")


@pytest.fixture(scope="session", autouse=True)
def allow_orm_beside_the_browser() -> Iterator[None]:
    """The synchronous Playwright API keeps an event loop in the thread, and
    Django then refuses every ORM call as "async unsafe". The queries here are
    plain synchronous ones; the flag only silences a guard that is looking at
    the wrong thing. Session scoped and confined to the e2e package.
    """
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("DJANGO_ALLOW_ASYNC_UNSAFE", "1")
        yield


@pytest.fixture(params=sorted(PROFILES), ids=sorted(PROFILES))
def profile(request: Any, browser: Any) -> Iterator[Any]:
    """A page on a phone and a page on a desktop, for the same scenario."""
    context = browser.new_context(viewport=PROFILES[request.param])
    try:
        yield context.new_page()
    finally:
        context.close()


@pytest.fixture
def eager_celery() -> Iterator[None]:
    """Run the notification inline, so the fake client can be inspected.

    Nothing here is testing the broker; what the scenario has to prove is that
    the enquiry reaches the owner.
    """
    from config.celery import app

    was_eager = app.conf.task_always_eager
    app.conf.task_always_eager = True
    try:
        yield
    finally:
        app.conf.task_always_eager = was_eager

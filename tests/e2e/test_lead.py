"""Section 10 in a real browser: an enquiry sent from a work page.

The scenario ends where it matters - in the fake Telegram client. A form that
submits and a message that arrives are two different claims.
"""

import time
from typing import Any

import pytest
from django.core import signing
from playwright.sync_api import expect

from apps.catalog.models import Work
from apps.leads.models import Lead
from apps.leads.services import antispam
from clients.factory import fake_telegram_client
from tests.factories import SiteSettingsFactory, WorkFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def work(db: Any) -> Work:
    site = SiteSettingsFactory.create()
    site.viber_url = "viber://chat?number=%2B380501112233"
    site.save()
    return WorkFactory.create(title_uk="Білий букет", status=Work.Status.PUBLISHED)


@pytest.fixture(autouse=True)
def telegram() -> Any:
    fake_telegram_client.reset()
    yield fake_telegram_client
    fake_telegram_client.reset()


@pytest.fixture(autouse=True)
def clean_limits() -> Any:
    """Every enquiry here comes from 127.0.0.1 and spends the real hourly quota
    of section 15. Without this the suite passes once and then starts filing
    its own submissions as spam."""
    from apps.leads.services import ratelimit

    try:
        client = ratelimit.get_client()
        client.ping()
    except Exception:  # pragma: no cover - only on a machine without Redis
        pytest.skip("redis is not reachable")

    def clear() -> None:
        for key in client.scan_iter(match="lead:*", count=500):
            client.delete(key)

    clear()
    yield
    clear()


def _age_the_form(page: Any) -> None:
    """Section 15 refuses a form filled in faster than a human could.

    A browser test types in milliseconds, so the timestamp is backdated the way
    a real visitor's would be by the time they finish reading the page.
    """
    token = signing.dumps(time.time() - 30, salt=antispam.TIMESTAMP_SALT)
    page.eval_on_selector_all(
        'input[name="ts"]',
        "(fields, value) => fields.forEach((field) => { field.value = value; })",
        token,
    )


def test_an_enquiry_from_a_work_page_reaches_the_owner(
    profile: Any, live_server: Any, work: Work, telegram: Any, eager_celery: None
) -> None:
    page = profile
    page.goto(f"{live_server.url}{work.get_absolute_url()}")

    page.get_by_role("button", name="Замовити схожу").click()
    form = page.locator("#lead-form-full")
    expect(form).to_be_visible()
    _age_the_form(page)

    form.locator('input[name="name"]').fill("Олена")
    form.locator('input[name="phone"]').fill("0501234567")
    form.locator('textarea[name="comment"]').fill("Потрібен такий самий букет")
    form.locator('input[name="consent"]').check()
    form.get_by_role("button", name="Надіслати").click()

    page.wait_for_url(f"{live_server.url}/dyakuyemo/")
    expect(page.get_by_text("Дякуємо")).to_be_visible()

    lead = Lead.objects.get()
    assert lead.name == "Олена"
    assert str(lead.phone) == "+380501234567"
    assert lead.work_article == work.article

    assert len(telegram.sent) == 1
    message = telegram.sent[0].text
    assert "Олена" in message
    assert "<code>+380501234567</code>" in message
    assert f"№{work.article}" in message


def test_the_call_me_back_form_asks_for_two_fields(
    profile: Any, live_server: Any, work: Work, eager_celery: None
) -> None:
    page = profile
    page.goto(f"{live_server.url}{work.get_absolute_url()}")

    page.get_by_role("button", name="Передзвоніть мені").click()
    form = page.locator("#lead-form-callback")
    expect(form).to_be_visible()
    _age_the_form(page)

    form.locator('input[name="name"]').fill("Ігор")
    form.locator('input[name="phone"]').fill("+380501112244")
    form.locator('input[name="consent"]').check()
    form.get_by_role("button", name="Надіслати").click()

    page.wait_for_url(f"{live_server.url}/dyakuyemo/")
    assert Lead.objects.get().name == "Ігор"


def test_the_phone_stays_reachable_without_the_form(
    profile: Any, live_server: Any, work: Work
) -> None:
    """The links of section 10 never depend on JavaScript or on a form."""
    page = profile
    page.goto(f"{live_server.url}{work.get_absolute_url()}")

    # `:visible` matters: the header renders the phone twice, and one of the
    # two is hidden by the breakpoint.
    assert page.locator('a[href^="tel:"]:visible').count() >= 1
    assert page.locator('a[href^="viber:"]').count() >= 1

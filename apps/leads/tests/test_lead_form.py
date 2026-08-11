"""Sections 10 and 15: the enquiry arrives, the spam does not, nobody is lost."""

import time
from typing import Any

import pytest
from django.core import signing
from django.test import Client
from hypothesis import given
from hypothesis import strategies as st

from apps.catalog.models import Work
from apps.leads.forms import normalize_phone
from apps.leads.models import Lead
from apps.leads.services import antispam, ratelimit
from tests.factories import SiteSettingsFactory, WorkFactory

pytestmark = pytest.mark.django_db

LEAD_URL = "/hx/lead/"


@pytest.fixture(autouse=True)
def site() -> Any:
    return SiteSettingsFactory.create()


@pytest.fixture(autouse=True)
def clean_limits() -> Any:
    """The limiter talks to a real Redis; every test starts from zero."""
    try:
        client = ratelimit.get_client()
        client.ping()
    except Exception:  # pragma: no cover - only on a machine without Redis
        pytest.skip("redis is not reachable")

    def clear() -> None:
        for key in client.scan_iter(match="lead:*", count=500):
            client.delete(key)

    clear()
    yield client
    clear()


def _old_token(seconds: int = 30) -> str:
    """A form rendered `seconds` ago, signed exactly like the real one."""
    return signing.dumps(time.time() - seconds, salt=antispam.TIMESTAMP_SALT)


def _payload(**overrides: Any) -> dict[str, Any]:
    data = {
        "form": "full",
        "ts": _old_token(),
        "name": "Олена",
        "phone": "0501234567",
        "preferred_contact": "phone",
        "event_date": "",
        "budget_text": "",
        "comment": "Потрібен букет",
        "consent": "on",
        "website": "",
    }
    data.update(overrides)
    return data


# --- phone numbers ------------------------------------------------------------


@pytest.mark.parametrize(
    "raw", ["0501234567", "+380501234567", "380501234567", "050 123 45 67", "(050) 123-45-67"]
)
def test_every_shape_of_a_ukrainian_number_is_accepted(raw: str) -> None:
    assert normalize_phone(raw) == "+380501234567"


@given(st.integers(min_value=0, max_value=99999999))
def test_normalising_a_phone_is_idempotent(tail: int) -> None:
    once = normalize_phone(f"050{tail:07d}")

    assert normalize_phone(once) == once


@pytest.mark.parametrize("raw", ["", "abc", "123", "+1 555 0100 999999"])
def test_a_number_we_cannot_read_comes_back_empty(raw: str) -> None:
    assert normalize_phone(raw) == ""


# --- the happy path -----------------------------------------------------------


def test_an_enquiry_is_stored_and_answered_with_a_redirect(client: Client) -> None:
    response = client.post(LEAD_URL, _payload(), headers={"HX-Request": "true"})

    lead = Lead.objects.get()
    assert response.headers["HX-Redirect"] == "/dyakuyemo/"
    assert lead.name == "Олена"
    assert str(lead.phone) == "+380501234567"
    assert lead.status == Lead.Status.NEW
    assert lead.ip_hash and lead.ip_hash != "127.0.0.1"


def test_without_javascript_the_same_post_ends_in_a_302(client: Client) -> None:
    response = client.post(LEAD_URL, _payload())

    assert response.status_code == 302
    assert response.headers["Location"] == "/dyakuyemo/"
    assert Lead.objects.count() == 1


def test_the_short_form_needs_only_a_name_and_a_number(client: Client) -> None:
    response = client.post(
        LEAD_URL,
        {
            "form": "callback",
            "ts": _old_token(),
            "name": "Ігор",
            "phone": "0501112233",
            "consent": "on",
        },
    )

    assert response.status_code == 302
    assert Lead.objects.get().name == "Ігор"


def test_an_enquiry_from_a_work_page_carries_its_number(client: Client) -> None:
    work = WorkFactory.create(status=Work.Status.PUBLISHED)

    client.post(LEAD_URL, _payload(work_article=str(work.article)))

    lead = Lead.objects.get()
    assert lead.work == work
    assert lead.work_article == work.article


def test_an_enquiry_from_the_favourites_carries_the_whole_collection(client: Client) -> None:
    client.post(LEAD_URL, _payload(favorites="147, 152,abc,152,-1"))

    assert Lead.objects.get().favorites_articles == [147, 152]


# --- validation ---------------------------------------------------------------


def test_without_consent_the_form_comes_back_with_an_error(client: Client) -> None:
    response = client.post(LEAD_URL, _payload(consent=""))

    assert response.status_code == 200
    assert Lead.objects.count() == 0
    assert "lead-form" in response.content.decode()


def test_a_broken_number_comes_back_highlighted(client: Client) -> None:
    response = client.post(LEAD_URL, _payload(phone="12"))

    assert Lead.objects.count() == 0
    assert 'aria-invalid="true"' in response.content.decode()


# --- antispam, one layer at a time --------------------------------------------


def test_a_filled_trap_answers_like_a_success_and_writes_nothing(client: Client) -> None:
    response = client.post(LEAD_URL, _payload(website="https://buy-cheap.example"))

    assert response.status_code == 302
    assert response.headers["Location"] == "/dyakuyemo/"
    assert Lead.objects.count() == 0


def test_a_form_sent_faster_than_a_human_is_dropped_in_silence(client: Client) -> None:
    response = client.post(LEAD_URL, _payload(ts=antispam.timestamp_token()))

    assert response.status_code == 302
    assert Lead.objects.count() == 0


def test_a_tampered_timestamp_is_dropped_in_silence(client: Client) -> None:
    response = client.post(LEAD_URL, _payload(ts="not-a-signature"))

    assert response.status_code == 302
    assert Lead.objects.count() == 0


def test_a_failed_turnstile_check_comes_back_with_a_notice(
    client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    from clients.factory import fake_turnstile_verifier

    fake_turnstile_verifier.success = False
    try:
        response = client.post(LEAD_URL, _payload())
    finally:
        fake_turnstile_verifier.reset()

    assert response.status_code == 200
    assert Lead.objects.count() == 0


def test_the_sixth_enquiry_within_the_hour_is_kept_as_spam(client: Client) -> None:
    for _index in range(5):
        client.post(LEAD_URL, _payload())

    response = client.post(LEAD_URL, _payload())

    assert Lead.objects.count() == 6
    assert Lead.objects.filter(status=Lead.Status.SPAM).count() == 1
    body = response.content.decode()
    assert "tel:" in body, "the visitor is offered the phone instead"


def test_the_daily_limit_behaves_the_same_way(
    client: Client, settings: Any, clean_limits: Any
) -> None:
    settings.ENV.lead_rate_global_day = 2

    for index in range(3):
        client.post(LEAD_URL, _payload(), REMOTE_ADDR=f"10.0.0.{index}")

    assert Lead.objects.filter(status=Lead.Status.SPAM).count() == 1


def test_an_unreachable_redis_never_blocks_an_enquiry(
    client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    def explode() -> Any:
        raise ConnectionError("redis is down")

    monkeypatch.setattr(ratelimit, "get_client", explode)

    response = client.post(LEAD_URL, _payload())

    assert response.status_code == 302
    assert Lead.objects.get().status == Lead.Status.NEW


# --- the mode switch ----------------------------------------------------------


def test_with_orders_closed_the_button_is_disabled_and_the_phone_is_not(
    client: Client, site: Any
) -> None:
    work = WorkFactory.create(status=Work.Status.PUBLISHED)
    site.accepting_orders = False
    site.not_accepting_message_uk = "Зараз не приймаємо замовлення"
    site.save()

    body = client.get(work.get_absolute_url()).content.decode()

    assert 'href="tel:+380501112233"' in body
    assert "disabled" in body
    assert "Зараз не приймаємо замовлення" in body


def test_the_thanks_page_always_exists(client: Client) -> None:
    response = client.get("/dyakuyemo/")

    assert response.status_code == 200
    assert '<meta name="robots" content="noindex, follow">' in response.content.decode()

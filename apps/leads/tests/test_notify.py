"""Section 8.1: the owner hears about an enquiry, exactly once."""

import datetime
from typing import Any

import pytest
from pydantic import ValidationError

from apps.leads.models import Lead
from apps.leads.tasks import build_message, notify_new_lead
from clients.base import ClientError
from clients.factory import fake_telegram_client
from config.celery import app

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def telegram() -> Any:
    fake_telegram_client.reset()
    yield fake_telegram_client
    fake_telegram_client.reset()


@pytest.fixture
def lead() -> Lead:
    return Lead.objects.create(
        name="Олена",
        phone="+380501234567",
        preferred_contact=Lead.PreferredContact.VIBER,
        event_date=datetime.date(2026, 9, 1),
        budget_text="до 1500",
        comment="Потрібен букет нареченої",
        work_article=147,
        favorites_articles=[147, 152],
        consent=True,
    )


def test_the_task_name_is_explicit() -> None:
    assert "leads.notify_new_lead" in app.tasks


def test_the_message_carries_everything_the_owner_needs(lead: Lead) -> None:
    text = build_message(lead)

    assert "Олена" in text
    assert "<code>+380501234567</code>" in text, "a tap on a code block copies the number"
    assert "01.09.2026" in text
    assert "до 1500" in text
    assert "№147" in text
    assert "№152" in text
    assert "Потрібен букет нареченої" in text
    assert f"/admin/leads/lead/{lead.pk}/change/" in text


def test_a_message_never_grows_past_the_telegram_limit(lead: Lead) -> None:
    lead.comment = "я" * 1000
    lead.save()

    assert len(build_message(lead)) <= 4096


def test_the_enquiry_is_announced_once(lead: Lead, telegram: Any) -> None:
    assert notify_new_lead(payload={"lead_id": lead.pk}) == "sent"

    lead.refresh_from_db()
    assert lead.notified_at is not None
    assert lead.notify_attempts == 1
    assert len(telegram.sent) == 1


def test_running_the_task_twice_sends_one_message(lead: Lead, telegram: Any) -> None:
    first = notify_new_lead(payload={"lead_id": lead.pk})
    second = notify_new_lead(payload={"lead_id": lead.pk})

    assert (first, second) == ("sent", "already sent")
    assert len(telegram.sent) == 1


def test_a_spam_enquiry_is_never_announced(lead: Lead, telegram: Any) -> None:
    lead.status = Lead.Status.SPAM
    lead.save()

    assert notify_new_lead(payload={"lead_id": lead.pk}) == "spam"
    assert telegram.sent == []
    lead.refresh_from_db()
    assert lead.notified_at is None


def test_a_server_error_is_retried_and_the_enquiry_stays(lead: Lead, telegram: Any) -> None:
    from apps.core.exceptions import TransientError

    telegram.fail_with(500)

    with pytest.raises(TransientError):
        notify_new_lead(payload={"lead_id": lead.pk})

    lead.refresh_from_db()
    assert lead.notified_at is None, "an unsent enquiry must not look sent"
    assert lead.notify_attempts == 1
    assert Lead.objects.filter(pk=lead.pk).exists()


def test_a_refusal_from_telegram_is_not_retried(lead: Lead, telegram: Any) -> None:
    telegram.fail_with(400)

    with pytest.raises(ClientError):
        notify_new_lead(payload={"lead_id": lead.pk})

    lead.refresh_from_db()
    assert lead.notified_at is None


def test_a_retry_picks_the_enquiry_up_again(lead: Lead, telegram: Any) -> None:
    """A retry of the same task may claim it; a parallel task may not."""
    from apps.core.exceptions import TransientError

    telegram.timeout()
    with pytest.raises(TransientError):
        notify_new_lead(payload={"lead_id": lead.pk})
    lead.refresh_from_db()
    assert lead.notify_attempts == 1
    assert lead.notified_at is None

    telegram.reset()
    result = notify_new_lead.apply(kwargs={"payload": {"lead_id": lead.pk}}, retries=1)

    assert result.get() == "sent"
    lead.refresh_from_db()
    assert lead.notify_attempts == 2
    assert lead.notified_at is not None


def test_the_retry_policy_is_the_one_from_section_8(lead: Lead) -> None:
    assert notify_new_lead.max_retries == 5
    assert notify_new_lead.retry_backoff_max == 600


def test_a_payload_without_a_positive_id_is_refused() -> None:
    with pytest.raises(ValidationError):
        notify_new_lead(payload={"lead_id": 0})


def test_an_unexpected_payload_key_is_refused() -> None:
    with pytest.raises(ValidationError):
        notify_new_lead(payload={"lead_id": 1, "urgent": True})


def test_a_deleted_enquiry_does_not_fail_the_task() -> None:
    assert notify_new_lead(payload={"lead_id": 999999}) == "missing"


def test_the_fake_validates_what_it_is_given(lead: Lead, telegram: Any) -> None:
    """Contract test: nonsense fails here, without a token and without a call."""
    from clients.dto import TelegramMessage

    with pytest.raises(ValidationError):
        telegram.send_message(TelegramMessage(chat_id="x", text="a" * 5000))
    assert telegram.sent == []


@pytest.mark.django_db(transaction=True)
def test_two_workers_racing_send_one_message(lead: Lead, telegram: Any) -> None:
    """The claim runs under select_for_update, so only one of them wins."""
    import threading

    from django.db import connections

    results: list[str] = []

    def run() -> None:
        try:
            results.append(notify_new_lead(payload={"lead_id": lead.pk}))
        finally:
            connections.close_all()

    threads = [threading.Thread(target=run) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(results) == ["already sent", "sent"]
    assert len(telegram.sent) == 1

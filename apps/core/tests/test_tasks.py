"""Section 8: task names, payload validation, idempotency."""

import pytest
from pydantic import ValidationError

from apps.core.contracts import EmptyPayload
from apps.core.tasks import ping
from config.celery import RetryTask, app


def test_task_names_are_explicit() -> None:
    assert "core.ping" in app.tasks
    assert ping.name == "core.ping"


def test_beat_entries_resolve_to_registered_tasks() -> None:
    assert app.conf.beat_schedule

    for name, entry in app.conf.beat_schedule.items():
        assert entry["task"] in app.tasks, f"{name} points at an unregistered task"
        assert "payload" in entry["kwargs"]


def test_ping_is_idempotent(caplog: pytest.LogCaptureFixture) -> None:
    first = ping(payload={})
    second = ping(payload={})

    assert first == second == "pong"


def test_invalid_payload_is_rejected_before_any_work() -> None:
    with pytest.raises(ValidationError):
        ping(payload={"unexpected": 1})


def test_empty_payload_forbids_extras() -> None:
    assert EmptyPayload.model_validate({}) is not None

    with pytest.raises(ValidationError):
        EmptyPayload.model_validate({"lead_id": 1})


def test_retry_policy_matches_the_contract() -> None:
    assert RetryTask.max_retries == 5
    assert RetryTask.retry_backoff is True
    assert RetryTask.retry_backoff_max == 600
    assert RetryTask.retry_jitter is True
    assert ping.max_retries == 5


def test_media_queue_is_routed_separately() -> None:
    assert app.conf.task_default_queue == "default"
    assert app.conf.task_routes["catalog.generate_renditions"] == {"queue": "media"}

import uuid

import pytest

from apps.common.models import PingRecord
from apps.common.tasks import ping

pytestmark = pytest.mark.django_db


def test_double_run_with_same_nonce_has_one_effect() -> None:
    # A fresh nonce per test run: the idempotency key lives in real Redis
    # with a 1h TTL, which outlives a single test run, so a fixed literal
    # here would collide with leftover state from the previous run.
    nonce = str(uuid.uuid4())

    first = ping.run({"nonce": nonce})
    second = ping.run({"nonce": nonce})

    assert first == "executed"
    assert second == "duplicate"
    assert PingRecord.objects.filter(nonce=nonce).count() == 1


def test_different_nonces_each_execute() -> None:
    nonce_a, nonce_b = str(uuid.uuid4()), str(uuid.uuid4())

    ping.run({"nonce": nonce_a})
    ping.run({"nonce": nonce_b})

    assert PingRecord.objects.filter(nonce__in=[nonce_a, nonce_b]).count() == 2

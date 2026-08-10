import uuid

import pytest
from django.core.cache import cache
from django.db import DatabaseError, transaction

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


def test_failed_work_releases_key_so_a_retry_can_still_do_it() -> None:
    """Error path: the claim is taken before the work, so a run whose work
    blows up must hand the key back — otherwise ``autoretry_for`` re-enters,
    sees its own claim and reports success for an effect that never landed.
    """
    # Longer than PingRecord.nonce's max_length, so the INSERT itself fails
    # in the database. No patching: the failure is real (tech.md §11.2).
    nonce = "x" * 100
    key = f"task:common.ping:{nonce}"
    cache.delete(key)

    # atomic() contains the broken transaction so the assertions below
    # still have a usable connection.
    with pytest.raises(DatabaseError), transaction.atomic():
        ping.run({"nonce": nonce})

    assert cache.get(key) is None, "failed run left its idempotency key claimed"
    assert PingRecord.objects.filter(nonce=nonce).count() == 0

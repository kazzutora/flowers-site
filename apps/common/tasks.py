"""``common.ping`` — the skeleton demo task and structural reference for
every task that follows it (tech.md §7): validate payload with a schema,
claim the idempotency key, do the work.
"""

from __future__ import annotations

import logging

from celery import shared_task

from apps.common.idempotency import acquire_idempotency_key, release_idempotency_key
from apps.common.models import PingRecord
from apps.common.schemas import PingPayload

logger = logging.getLogger(__name__)

PING_IDEMPOTENCY_TTL_SECONDS = 60 * 60


@shared_task(
    name="common.ping",
    queue="default",
    acks_late=True,
    reject_on_worker_lost=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def ping(payload: dict[str, object]) -> str:
    data = PingPayload.model_validate(payload)

    key = f"task:common.ping:{data.nonce}"
    if not acquire_idempotency_key(key, PING_IDEMPOTENCY_TTL_SECONDS):
        logger.info("common.ping duplicate nonce=%s", data.nonce)
        return "duplicate"

    try:
        PingRecord.objects.create(nonce=data.nonce)
    except Exception:
        # Hand the key back so the autoretry above can actually redo the
        # work; without this the retry sees this run's own claim and
        # reports "duplicate" for an effect that never happened.
        release_idempotency_key(key)
        raise

    logger.info("common.ping executed nonce=%s", data.nonce)
    return "executed"

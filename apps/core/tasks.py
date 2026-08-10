import logging

from celery import shared_task

from apps.core.contracts import EmptyPayload

logger = logging.getLogger(__name__)


@shared_task(name="core.ping")
def ping(payload: dict) -> str:
    """Proves the queue works end to end. Removed after stage 0 (section 8.7).

    Idempotent by construction: it owns no state and writes one log line.
    """
    EmptyPayload.model_validate(payload)
    logger.info("core.ping")
    return "pong"

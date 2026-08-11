"""View counters (section 8.3).

Every visit increments a Redis key; the counters are folded into the database
once every five minutes. Redis being down costs a view count, never a page.
"""

import logging
from typing import Any

import redis
from django.conf import settings

logger = logging.getLogger(__name__)

WORK_KEY = "views:work:{identifier}"
POST_KEY = "views:post:{identifier}"
PATTERNS: dict[str, str] = {"work": "views:work:*", "post": "views:post:*"}


def get_client() -> Any:
    """A short-timeout client. The cache backend cannot do GETDEL for us."""
    return redis.Redis.from_url(
        str(settings.ENV.redis_url), socket_connect_timeout=1, socket_timeout=1
    )


def _record(key: str) -> None:
    try:
        get_client().incr(key)
    # Broad on purpose: a counter is never worth a 500.
    except Exception:
        logger.warning("view counter unavailable for %s", key, exc_info=True)


def record_work_view(work_id: int) -> None:
    _record(WORK_KEY.format(identifier=work_id))


def record_post_view(post_id: int) -> None:
    _record(POST_KEY.format(identifier=post_id))


def collect() -> dict[str, dict[int, int]]:
    """Take every counter with GETDEL and hand the amounts over.

    Idempotent by construction: what has been taken is gone, so a second run
    finds nothing to add.
    """
    collected: dict[str, dict[int, int]] = {kind: {} for kind in PATTERNS}
    try:
        client = get_client()
        for kind, pattern in PATTERNS.items():
            for raw_key in client.scan_iter(match=pattern, count=500):
                value = client.getdel(raw_key)
                if value is None:
                    continue
                key = raw_key.decode() if isinstance(raw_key, bytes) else str(raw_key)
                try:
                    identifier = int(key.rsplit(":", 1)[-1])
                    amount = int(value)
                except ValueError:
                    logger.warning("view counter key %s is malformed", key)
                    continue
                if amount:
                    collected[kind][identifier] = amount
    except Exception:
        logger.warning("view counters could not be collected", exc_info=True)
    return collected

"""tech.md §7: SETNX-on-Redis idempotency guard, the default mechanism for
Celery tasks and webhook handlers that don't already have a DB unique
constraint to lean on.
"""

from __future__ import annotations

from django.core.cache import cache


def acquire_idempotency_key(key: str, ttl_seconds: int) -> bool:
    """Atomically claim ``key``. True the first time, False on every repeat
    call within ``ttl_seconds`` — i.e. "already handled, skip the work".

    Maps to Redis ``SETNX`` + ``EXPIRE`` via the cache backend's ``add()``,
    which is atomic (no separate check-then-set race).
    """
    return bool(cache.add(key, 1, timeout=ttl_seconds))

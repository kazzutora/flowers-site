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


def release_idempotency_key(key: str) -> None:
    """Drop a claim taken by :func:`acquire_idempotency_key`.

    Claiming is atomic, so it necessarily happens *before* the work rather
    than after it. That ordering is what makes concurrent duplicates safe,
    but it also means a task whose work then raises has already burned its
    key: ``autoretry_for`` would re-enter, see the claim, and skip the work
    it never actually did. Releasing on failure keeps the retry policy
    required by tech.md §7 meaningful instead of decorative.
    """
    cache.delete(key)

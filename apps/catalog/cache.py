"""Gallery fragment cache (section 14.4).

The key carries a version number. Saving a work bumps that number and the whole
cache becomes unreachable at once - no key scan, no prefix walk, no list of
what to delete.

Redis being unavailable is not an error here: the caller renders the page and
carries on.
"""

import hashlib
import logging
from typing import Any

from django.core.cache import cache
from django.utils.translation import get_language

logger = logging.getLogger(__name__)

VERSION_KEY = "gallery:ver"
TTL = 300


def version() -> int:
    """The current cache generation. An unreachable cache reads as zero."""
    try:
        current = cache.get(VERSION_KEY)
    # Broad on purpose: a cache miss must never reach the visitor.
    except Exception:
        logger.warning("gallery cache unavailable while reading the version", exc_info=True)
        return 0
    return int(current or 0)


def bump() -> None:
    """Invalidate every gallery fragment at once."""
    try:
        try:
            cache.incr(VERSION_KEY)
        except ValueError:
            # incr needs the key to exist; the first bump creates it.
            cache.set(VERSION_KEY, 1, None)
    except Exception:
        logger.warning("gallery cache unavailable while bumping the version", exc_info=True)


def fragment_key(occasion: str, query: str, page: int) -> str:
    """`gallery:{ver}:{lang}:{sha1(query + occasion)}:{page}` (section 14.4)."""
    digest = hashlib.sha1(f"{occasion}|{query}".encode()).hexdigest()
    return f"gallery:{version()}:{get_language() or 'uk'}:{digest}:{page}"


def get(key: str) -> Any:
    try:
        return cache.get(key)
    except Exception:
        logger.warning("gallery cache unavailable on read", exc_info=True)
        return None


# Named after the cache API it wraps, not after the builtin.
def set(key: str, value: Any) -> None:
    try:
        cache.set(key, value, TTL)
    except Exception:
        logger.warning("gallery cache unavailable on write", exc_info=True)


def is_cacheable(request: Any) -> bool:
    """Only anonymous GETs. An admin preview is never served from a cache."""
    user = getattr(request, "user", None)
    return request.method == "GET" and not (user is not None and user.is_authenticated)

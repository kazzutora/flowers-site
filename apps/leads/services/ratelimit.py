"""Rate limits on Redis (section 15).

The window is a fixed calendar one, not a sliding one: two bursts across an
hour boundary are possible and accepted.

An unreachable Redis counts as "within the limits". Losing a real enquiry
because the cache is down is the one outcome that is not allowed.
"""

import logging
from datetime import UTC, datetime
from typing import Any

import redis
from django.conf import settings

logger = logging.getLogger(__name__)

# Twice the window, so a key never disappears while its window is still open.
IP_KEY_TTL = 2 * 3600
GLOBAL_KEY_TTL = 2 * 86400


def get_client() -> Any:
    return redis.Redis.from_url(
        str(settings.ENV.redis_url), socket_connect_timeout=1, socket_timeout=1
    )


def ip_key(scope: str, ip_hash: str, moment: datetime | None = None) -> str:
    stamp = (moment or datetime.now(UTC)).strftime("%Y%m%d%H")
    return f"{scope}:ip:{ip_hash}:{stamp}"


def global_key(scope: str, moment: datetime | None = None) -> str:
    stamp = (moment or datetime.now(UTC)).strftime("%Y%m%d")
    return f"{scope}:global:{stamp}"


def within_limits(scope: str, ip_hash: str, per_ip_hour: int, per_day: int) -> bool:
    """Count this submission and say whether it is still inside both limits."""
    try:
        client = get_client()
        moment = datetime.now(UTC)
        by_ip = ip_key(scope, ip_hash, moment)
        overall = global_key(scope, moment)

        pipeline = client.pipeline()
        pipeline.incr(by_ip)
        pipeline.expire(by_ip, IP_KEY_TTL)
        pipeline.incr(overall)
        pipeline.expire(overall, GLOBAL_KEY_TTL)
        ip_count, _ip_ttl, global_count, _global_ttl = pipeline.execute()
    # Broad on purpose: see the module docstring.
    except Exception:
        logger.warning("rate limiter unavailable, letting %s through", scope, exc_info=True)
        return True

    return int(ip_count) <= per_ip_hour and int(global_count) <= per_day

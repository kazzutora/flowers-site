"""The quiet layers of section 15: a trap field, a signed clock and Turnstile.

A bot is never told it was caught. The first two layers answer exactly like a
success and simply do not write a row.
"""

import hashlib
import logging
import time
from typing import Any

from django.conf import settings
from django.core import signing
from django.http import HttpRequest

logger = logging.getLogger(__name__)

HONEYPOT_FIELD = "website"
TIMESTAMP_FIELD = "ts"
TURNSTILE_FIELD = "cf-turnstile-response"
TIMESTAMP_SALT = "flowers.form.timestamp"
# A form older than this was probably left open in a tab; the clock check is
# about submissions that are too fast, not about tidy housekeeping.
TIMESTAMP_MAX_AGE = 24 * 3600


def hash_ip(ip: str) -> str:
    """sha256(ip + salt). The raw address is never written anywhere."""
    salt = str(settings.ENV.ip_hash_salt.get_secret_value())
    return hashlib.sha256(f"{ip}{salt}".encode()).hexdigest()


def client_ip(request: HttpRequest) -> str:
    forwarded = str(request.META.get("HTTP_X_FORWARDED_FOR") or "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return str(request.META.get("REMOTE_ADDR") or "")


def timestamp_token() -> str:
    """A signed "the form was rendered now", put into a hidden field."""
    return signing.dumps(time.time(), salt=TIMESTAMP_SALT)


def filled_too_fast(data: Any, minimum_seconds: int | None = None) -> bool:
    """True when the form came back faster than a human could fill it in.

    A missing or tampered signature counts as too fast: both mean the field
    did not come from a page we rendered.
    """
    minimum = settings.ENV.form_min_fill_seconds if minimum_seconds is None else minimum_seconds
    raw = data.get(TIMESTAMP_FIELD) or ""
    if not raw:
        return True
    try:
        rendered_at = float(signing.loads(raw, salt=TIMESTAMP_SALT, max_age=TIMESTAMP_MAX_AGE))
    except (signing.BadSignature, signing.SignatureExpired, TypeError, ValueError):
        return True
    return (time.time() - rendered_at) < minimum


def honeypot_filled(data: Any) -> bool:
    """The trap field is invisible, so only a robot ever puts anything in it."""
    return bool((data.get(HONEYPOT_FIELD) or "").strip())


def turnstile_passed(request: HttpRequest) -> bool:
    """With Turnstile disabled the verifier accepts everything (section 7)."""
    from clients.factory import get_turnstile_verifier

    token = request.POST.get(TURNSTILE_FIELD) or ""
    return bool(get_turnstile_verifier().verify(token, client_ip(request) or None).success)

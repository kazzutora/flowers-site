"""tech.md §4: phones are stored normalized to E.164, always through here."""

from __future__ import annotations

import re

_DIGITS_RE = re.compile(r"\D")
_E164_UA_RE = re.compile(r"^\+380\d{9}$")


class InvalidPhoneNumberError(ValueError):
    pass


def normalize_phone(raw: str) -> str:
    """Normalize a Ukrainian mobile number to E.164 (``+380XXXXXXXXX``).

    Accepts local (``0671234567``), spaced/punctuated
    (``+38 067 123 45 67``, ``38(067)1234567``) and already-normalized
    input. Idempotent: ``normalize_phone(normalize_phone(x)) == normalize_phone(x)``.
    """
    digits = _DIGITS_RE.sub("", raw)

    if digits.startswith("380") and len(digits) == 12:
        national = digits[3:]
    elif digits.startswith("0") and len(digits) == 10:
        national = digits[1:]
    elif len(digits) == 9:
        national = digits
    else:
        raise InvalidPhoneNumberError(f"cannot normalize phone number: {raw!r}")

    normalized = f"+380{national}"
    if not _E164_UA_RE.match(normalized):
        raise InvalidPhoneNumberError(f"cannot normalize phone number: {raw!r}")
    return normalized

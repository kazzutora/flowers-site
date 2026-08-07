"""Sentry ``before_send`` hook. Phone, address and card text must never
reach Sentry — CLAUDE.md red line, tech.md §10.4.
"""

from __future__ import annotations

from typing import Any

from sentry_sdk.types import Event, Hint

_SENSITIVE_KEYS = {
    "phone",
    "recipient_phone",
    "customer_phone",
    "delivery_address",
    "address",
    "card_text",
}


def scrub_sensitive_event(event: Event, hint: Hint) -> Event | None:
    _scrub(event)
    return event


def _scrub(node: Any) -> None:
    if isinstance(node, dict):
        for key in list(node.keys()):
            if key.lower() in _SENSITIVE_KEYS:
                node[key] = "[scrubbed]"
            else:
                _scrub(node[key])
    elif isinstance(node, list):
        for item in node:
            _scrub(item)

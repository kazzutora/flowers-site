"""Factories select an implementation by ``settings.SMS_PROVIDER`` /
``settings.MESSENGER_PROVIDER`` (tech.md §9.1). Services call these,
never a concrete provider class.
"""

from __future__ import annotations

from django.conf import settings

from apps.notifications.clients.base import MessengerClient, SmsClient
from apps.notifications.clients.fake import FakeMessengerClient, FakeSmsClient


def get_sms_client() -> SmsClient:
    provider = settings.SMS_PROVIDER
    if provider == "fake":
        return FakeSmsClient()
    raise NotImplementedError(f"SMS provider {provider!r} is not implemented yet")


def get_messenger_client() -> MessengerClient:
    provider = settings.MESSENGER_PROVIDER
    if provider == "fake":
        return FakeMessengerClient()
    raise NotImplementedError(f"messenger provider {provider!r} is not implemented yet")

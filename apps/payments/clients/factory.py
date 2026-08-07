"""Factory selects an implementation by ``settings.PAYMENT_PROVIDER``
(tech.md §9.1). Services call this, never a concrete provider class.
"""

from __future__ import annotations

from django.conf import settings

from apps.payments.clients.base import PaymentProvider
from apps.payments.clients.fake import FakePaymentProvider


def get_payment_provider() -> PaymentProvider:
    provider = settings.PAYMENT_PROVIDER
    if provider == "fake":
        return FakePaymentProvider()
    raise NotImplementedError(f"payment provider {provider!r} is not implemented yet")

"""S0.7 acceptance: factory returns the fake when PAYMENT_PROVIDER=fake."""

import pytest
from pytest_django.fixtures import Settings

from apps.payments.clients.factory import get_payment_provider
from apps.payments.clients.fake import FakePaymentProvider


def test_returns_fake_provider_when_configured(settings: Settings) -> None:
    settings.PAYMENT_PROVIDER = "fake"

    assert isinstance(get_payment_provider(), FakePaymentProvider)


def test_raises_for_unimplemented_provider(settings: Settings) -> None:
    settings.PAYMENT_PROVIDER = "liqpay"

    with pytest.raises(NotImplementedError):
        get_payment_provider()

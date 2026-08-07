from decimal import Decimal

import pytest

from apps.payments.clients.dto import OrderDTO, PaymentStatus
from apps.payments.clients.errors import PaymentProviderError
from apps.payments.clients.fake import FakePaymentProvider


def test_create_invoice_returns_invoice() -> None:
    provider = FakePaymentProvider()

    invoice = provider.create_invoice(OrderDTO(public_id="01ABC", total=Decimal("890.00")))

    assert invoice.provider_payment_id == "fake_01ABC"
    assert invoice.status == PaymentStatus.CREATED
    assert provider.created_invoices == [invoice]


def test_create_invoice_raises_on_fail_flag() -> None:
    provider = FakePaymentProvider(fail=True)

    with pytest.raises(PaymentProviderError):
        provider.create_invoice(OrderDTO(public_id="01ABC", total=Decimal("890.00")))


def test_verify_signature_true_unless_failing() -> None:
    assert FakePaymentProvider().verify_signature(b"body", {}) is True
    assert FakePaymentProvider(fail=True).verify_signature(b"body", {}) is False


def test_parse_callback_builds_result() -> None:
    provider = FakePaymentProvider()

    result = provider.parse_callback(
        {"provider_payment_id": "fake_01ABC", "status": "succeeded", "amount": "890.00"}
    )

    assert result.status == PaymentStatus.SUCCEEDED
    assert result.amount == Decimal("890.00")


def test_parse_callback_raises_on_fail_flag() -> None:
    with pytest.raises(PaymentProviderError):
        FakePaymentProvider(fail=True).parse_callback({})


def test_fetch_status_raises_on_fail_flag() -> None:
    with pytest.raises(PaymentProviderError):
        FakePaymentProvider(fail=True).fetch_status("fake_01ABC")

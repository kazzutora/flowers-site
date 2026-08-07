"""FakePaymentProvider — tech.md §9.1, S0.7. Every service is built and
tested against this from day one; real providers (LiqPay/Mono/WayForPay)
arrive in stage 6 and don't block anything until then.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from apps.payments.clients.base import PaymentProvider
from apps.payments.clients.dto import InvoiceDTO, OrderDTO, PaymentResult, PaymentStatus
from apps.payments.clients.errors import PaymentProviderError


class FakePaymentProvider(PaymentProvider):
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.created_invoices: list[InvoiceDTO] = []

    def create_invoice(self, order: OrderDTO) -> InvoiceDTO:
        if self.fail:
            raise PaymentProviderError("fake provider: create_invoice failed")
        invoice = InvoiceDTO(
            invoice_url=f"https://fake-pay.local/invoice/{order.public_id}",
            provider_payment_id=f"fake_{order.public_id}",
            status=PaymentStatus.CREATED,
        )
        self.created_invoices.append(invoice)
        return invoice

    def verify_signature(self, raw: bytes, headers: Mapping[str, str]) -> bool:
        return not self.fail

    def parse_callback(self, payload: dict[str, object]) -> PaymentResult:
        if self.fail:
            raise PaymentProviderError("fake provider: parse_callback failed")
        return PaymentResult(
            provider_payment_id=str(payload["provider_payment_id"]),
            status=PaymentStatus(payload.get("status", PaymentStatus.SUCCEEDED.value)),
            amount=Decimal(str(payload["amount"])),
            currency=str(payload.get("currency", "UAH")),
        )

    def fetch_status(self, provider_payment_id: str) -> PaymentStatus:
        if self.fail:
            raise PaymentProviderError("fake provider: fetch_status failed")
        return PaymentStatus.SUCCEEDED

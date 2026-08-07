"""tech.md §9.1 — frozen ABC signature."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping

from apps.payments.clients.dto import InvoiceDTO, OrderDTO, PaymentResult, PaymentStatus


class PaymentProvider(ABC):
    @abstractmethod
    def create_invoice(self, order: OrderDTO) -> InvoiceDTO: ...

    @abstractmethod
    def verify_signature(self, raw: bytes, headers: Mapping[str, str]) -> bool: ...

    @abstractmethod
    def parse_callback(self, payload: dict[str, object]) -> PaymentResult: ...

    @abstractmethod
    def fetch_status(self, provider_payment_id: str) -> PaymentStatus: ...

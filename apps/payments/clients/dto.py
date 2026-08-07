"""DTOs for the PaymentProvider boundary (tech.md §9.1).

``PaymentProvider``'s method signatures are frozen in tech.md §9.1
(``create_invoice`` / ``verify_signature`` / ``parse_callback`` /
``fetch_status``), but the exact field lists of ``OrderDTO`` /
``InvoiceDTO`` / ``PaymentResult`` aren't enumerated there — only
``PlaybackDTO`` (apps.live) gets a full field table in tech.md. These are
kept intentionally minimal, derived directly from the already-frozen
``Payment``/``Order`` columns (tech.md §4.5, §4.7); no new business field
is introduced. Flagged as a CONTRACT GAP in the S0.7 PR description —
revisit once stage 6 (payments) freezes the real shape.
"""

from __future__ import annotations

from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict


class PaymentStatus(str, Enum):
    """Mirrors ``Payment.status`` choices, tech.md §4.7."""

    CREATED = "created"
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class OrderDTO(BaseModel):
    """Minimal order projection a provider needs to open an invoice."""

    model_config = ConfigDict(extra="forbid")

    public_id: str
    total: Decimal
    currency: str = "UAH"


class InvoiceDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invoice_url: str
    provider_payment_id: str
    status: PaymentStatus


class PaymentResult(BaseModel):
    """Parsed webhook callback (tech.md §5.7)."""

    model_config = ConfigDict(extra="forbid")

    provider_payment_id: str
    status: PaymentStatus
    amount: Decimal
    currency: str

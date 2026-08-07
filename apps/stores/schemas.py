"""tech.md §5.1 — StoreListResponse, frozen shape."""

from __future__ import annotations

from decimal import Decimal

from pydantic import field_serializer

from apps.common.schemas import ApiModel
from apps.stores.domain import WorkHours


class StoreOut(ApiModel):
    slug: str
    name: str
    address: str
    phone: str
    lat: Decimal | None
    lng: Decimal | None
    work_hours: WorkHours
    is_open_now: bool

    @field_serializer("lat", "lng")
    def _serialize_coordinate(self, value: Decimal | None) -> float | None:
        # tech.md §5.1 shows lat/lng as bare JSON numbers (unlike money,
        # which is always a string) — Pydantic's Decimal default is a
        # string, so coordinates need an explicit float serializer.
        return float(value) if value is not None else None


class StoreListResponse(ApiModel):
    stores: list[StoreOut]

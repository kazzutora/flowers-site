"""Read-shaping for pages/endpoints — combines repositories + domain into
data templates and Pydantic schemas can render directly (tech.md §3.2).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from django.utils import timezone

from apps.stores.domain import WorkHours, is_open_now
from apps.stores.repositories import list_active_stores

_DAY_LABELS: tuple[tuple[str, str], ...] = (
    ("mon", "Пн"),
    ("tue", "Вт"),
    ("wed", "Ср"),
    ("thu", "Чт"),
    ("fri", "Пт"),
    ("sat", "Сб"),
    ("sun", "Нд"),
)
_MAP_BBOX_DELTA = Decimal("0.01")


@dataclass(frozen=True)
class StoreListItem:
    slug: str
    name: str
    address: str
    phone: str
    lat: Decimal | None
    lng: Decimal | None
    work_hours: WorkHours
    is_open_now: bool
    work_hours_rows: list[tuple[str, str]]
    map_embed_url: str | None


def _format_work_hours_rows(work_hours: WorkHours) -> list[tuple[str, str]]:
    rows = []
    for key, label in _DAY_LABELS:
        day_range = work_hours.get(key)
        rows.append((label, f"{day_range[0]}–{day_range[1]}" if day_range else "вихідний"))
    return rows


def _build_map_embed_url(lat: Decimal | None, lng: Decimal | None) -> str | None:
    if lat is None or lng is None:
        return None
    bbox = (
        f"{lng - _MAP_BBOX_DELTA},{lat - _MAP_BBOX_DELTA},"
        f"{lng + _MAP_BBOX_DELTA},{lat + _MAP_BBOX_DELTA}"
    )
    return f"https://www.openstreetmap.org/export/embed.html?bbox={bbox}&marker={lat},{lng}"


def list_stores_with_status(now: datetime | None = None) -> list[StoreListItem]:
    """tech.md §5.1 / DEV.md S0.9: ``is_open_now`` computed per store, in
    Europe/Kyiv (``settings.TIME_ZONE``, so plain ``timezone.localtime``
    already lands in the right zone).
    """
    reference_time = now or timezone.localtime(timezone.now())
    return [
        StoreListItem(
            slug=store.slug,
            name=store.name,
            address=store.address,
            phone=store.phone,
            lat=store.lat,
            lng=store.lng,
            work_hours=store.work_hours,
            is_open_now=is_open_now(store.work_hours, reference_time),
            work_hours_rows=_format_work_hours_rows(store.work_hours),
            map_embed_url=_build_map_embed_url(store.lat, store.lng),
        )
        for store in list_active_stores()
    ]

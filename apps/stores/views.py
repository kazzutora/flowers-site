"""Views stay thin: no ORM imports, no business logic (tech.md §3.1)."""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from apps.stores.schemas import StoreListResponse, StoreOut
from apps.stores.selectors import list_stores_with_status


def stores_page(request: HttpRequest) -> HttpResponse:
    stores = list_stores_with_status()
    breadcrumb_items = [
        {"label": "Головна", "url": "/"},
        {"label": "Наші магазини", "url": None},
    ]
    return render(
        request,
        "stores/list.html",
        {"stores": stores, "breadcrumb_items": breadcrumb_items},
    )


def stores_api(request: HttpRequest) -> HttpResponse:
    items = list_stores_with_status()
    body = StoreListResponse(
        stores=[
            StoreOut(
                slug=item.slug,
                name=item.name,
                address=item.address,
                phone=item.phone,
                lat=item.lat,
                lng=item.lng,
                work_hours=item.work_hours,
                is_open_now=item.is_open_now,
            )
            for item in items
        ]
    )
    return HttpResponse(body.model_dump_json(), content_type="application/json")

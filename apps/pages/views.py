"""Views stay thin: parse input, call a use-case/selector, render. This
module has none of those yet — the pages it serves are static chrome and
the design-system showcase — so it renders directly.
"""

from __future__ import annotations

from decimal import Decimal
from http import HTTPStatus
from typing import Any

from django.conf import settings
from django.core.paginator import Paginator
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render


def home(request: HttpRequest) -> HttpResponse:
    return render(request, "pages/home.html")


def kitchen_sink(request: HttpRequest) -> HttpResponse:
    """Design-system showcase — every UI primitive, every variant.

    tech.md §8: available only in DEBUG or to staff, so it never leaks
    into the public, indexable site.
    """
    is_staff = request.user.is_authenticated and request.user.is_staff
    if not (settings.DEBUG or is_staff):
        raise Http404

    context: dict[str, Any] = {
        "sample_product": {
            "title": "Букет «Весняний ранок»",
            "slug": "vesnyanyi-ranok",
            "price": Decimal("890.00"),
            "old_price": Decimal("990.00"),
            "image_url": "/static/dev/kitchen-sink/product-placeholder.svg",
            "badge": "Хіт",
        },
        "sample_stores": [
            {"slug": "centr", "name": "Центр", "is_open_now": True},
            {"slug": "poznyaky", "name": "Позняки", "is_open_now": False},
        ],
        "sample_gallery_items": [
            {
                "id": i,
                "title": f"Робота №{i}",
                "image_url": "/static/dev/kitchen-sink/gallery-placeholder.svg",
                "price_from": Decimal("650.00"),
            }
            for i in range(1, 9)
        ],
        "delivery_options": [
            {
                "code": "pickup",
                "title": "Самовивіз з магазину (2 адреси)",
                "description": "Безкоштовно.",
                "price_hint": None,
            },
            {
                "code": "taxi",
                "title": "Відправка по місту на таксі",
                "description": (
                    "Оплачується за тарифом таксі на момент замовлення, "
                    "зазвичай 60–150 грн. Менеджер називає точну суму до оплати."
                ),
                "price_hint": "60–150 грн",
            },
            {
                "code": "manager",
                "title": "Особливі випадки",
                "description": (
                    "За місто, точний час, велике замовлення — домовляємось з менеджером."
                ),
                "price_hint": None,
            },
        ],
        "live_states": [
            {
                "state": "live",
                "poster_url": "/static/dev/kitchen-sink/live-poster.svg",
            },
            {
                "state": "closed",
                "poster_url": "/static/dev/kitchen-sink/live-poster.svg",
                "message": "Зараз зачинено. Відкриємось о 09:00",
            },
            {
                "state": "offline",
                "poster_url": "/static/dev/kitchen-sink/live-poster.svg",
                "message": "Камера тимчасово недоступна, ми вже розбираємось",
            },
            {
                "state": "disabled",
            },
        ],
        "page_obj": Paginator(list(range(1, 61)), 12).get_page(2),
        "breadcrumb_items": [
            {"label": "Головна", "url": "/"},
            {"label": "Каталог", "url": "/catalog/"},
            {"label": "Букет «Весняний ранок»", "url": None},
        ],
        "filter_groups": [
            {
                "key": "occasion",
                "label": "Привід",
                "options": [
                    {"value": "den-narodzhennya", "label": "День народження", "active": True},
                    {"value": "vesillya", "label": "Весілля", "active": False},
                ],
            },
            {
                "key": "color",
                "label": "Колір",
                "options": [
                    {"value": "pink", "label": "Рожевий", "active": False},
                    {"value": "white", "label": "Білий", "active": False},
                ],
            },
        ],
        "checkout_steps": [
            {"label": "Кому і коли"},
            {"label": "Як отримати"},
            {"label": "Хто замовляє"},
            {"label": "Оплата"},
        ],
        "select_demo_options": [
            {"value": "10-13", "label": "10:00–13:00"},
            {"value": "13-16", "label": "13:00–16:00"},
            {"value": "16-19", "label": "16:00–19:00"},
            {"value": "asap", "label": "Якнайшвидше"},
        ],
    }
    response = render(request, "pages/kitchen_sink.html", context)
    response.status_code = HTTPStatus.OK
    return response

"""Data every template needs regardless of which view rendered it."""

from __future__ import annotations

from typing import Any

from django.http import HttpRequest

from apps.pages.navigation import MAIN_NAV
from apps.stores.repositories import list_active_stores


def header_data(request: HttpRequest) -> dict[str, Any]:
    stores = list(list_active_stores())
    return {
        "main_nav": MAIN_NAV,
        "header_stores": stores,
        # Cookie-backed "current store" selection is S1.2
        # (apps.stores.selectors.get_current_store); until then the
        # header switcher defaults to the first store by sort_order.
        "header_current_store": stores[0] if stores else None,
    }

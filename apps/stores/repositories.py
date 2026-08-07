"""Only place in apps.stores that touches the ORM (tech.md §3.1)."""

from __future__ import annotations

from django.db.models import QuerySet

from apps.stores.models import Store


def list_active_stores() -> QuerySet[Store]:
    return Store.objects.filter(is_active=True).order_by("sort_order", "name")


def get_active_store_by_slug(slug: str) -> Store | None:
    return Store.objects.filter(is_active=True, slug=slug).first()

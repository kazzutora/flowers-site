import pytest

from apps.stores.repositories import get_active_store_by_slug, list_active_stores
from apps.stores.tests.factories import StoreFactory

pytestmark = pytest.mark.django_db


def test_list_active_stores_excludes_inactive() -> None:
    StoreFactory(slug="active-1", is_active=True, sort_order=1)
    StoreFactory(slug="inactive-1", is_active=False, sort_order=0)

    slugs = [store.slug for store in list_active_stores()]

    assert slugs == ["active-1"]


def test_list_active_stores_orders_by_sort_order_then_name() -> None:
    StoreFactory(slug="second", name="Б", sort_order=2)
    StoreFactory(slug="first", name="А", sort_order=1)

    slugs = [store.slug for store in list_active_stores()]

    assert slugs == ["first", "second"]


def test_get_active_store_by_slug_returns_none_for_inactive() -> None:
    StoreFactory(slug="hidden", is_active=False)

    assert get_active_store_by_slug("hidden") is None


def test_get_active_store_by_slug_returns_none_for_missing() -> None:
    assert get_active_store_by_slug("does-not-exist") is None


def test_get_active_store_by_slug_returns_match() -> None:
    StoreFactory(slug="centr")

    store = get_active_store_by_slug("centr")

    assert store is not None
    assert store.slug == "centr"

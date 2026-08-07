"""tech.md §5.1: GET /api/v1/stores/ -> 200 StoreListResponse.

The path is asserted as a literal string, not via reverse(): this test
exists to catch drift from the frozen contract path, and reverse() would
silently follow a routing change instead of catching it.
"""

import pytest
from django.test import Client

from apps.stores.schemas import StoreListResponse
from apps.stores.tests.factories import StoreFactory

pytestmark = pytest.mark.django_db


def test_stores_api_matches_response_schema(client: Client) -> None:
    StoreFactory(slug="centr", name="Центр")

    response = client.get("/api/v1/stores/")

    assert response.status_code == 200
    assert response["Content-Type"] == "application/json"
    parsed = StoreListResponse.model_validate_json(response.content)
    assert parsed.stores[0].slug == "centr"


def test_stores_api_empty_db_returns_empty_list(client: Client) -> None:
    response = client.get("/api/v1/stores/")

    assert response.status_code == 200
    parsed = StoreListResponse.model_validate_json(response.content)
    assert parsed.stores == []


def test_stores_api_excludes_inactive_stores(client: Client) -> None:
    StoreFactory(slug="hidden", is_active=False)

    response = client.get("/api/v1/stores/")

    parsed = StoreListResponse.model_validate_json(response.content)
    assert parsed.stores == []

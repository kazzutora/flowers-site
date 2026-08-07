from datetime import date, datetime, time
from zoneinfo import ZoneInfo

import pytest

from apps.stores.selectors import list_stores_with_status
from apps.stores.tests.factories import StoreFactory

pytestmark = pytest.mark.django_db

KYIV = ZoneInfo("Europe/Kyiv")
_MONDAY = date.fromisocalendar(2026, 32, 1)


def test_combines_domain_status_with_repository_data() -> None:
    StoreFactory(
        slug="centr",
        name="Центр",
        work_hours={
            "mon": ["09:00", "20:00"],
            "tue": None,
            "wed": None,
            "thu": None,
            "fri": None,
            "sat": None,
            "sun": None,
        },
    )
    monday_noon = datetime.combine(_MONDAY, time(12, 0), tzinfo=KYIV)

    [item] = list_stores_with_status(now=monday_noon)

    assert item.slug == "centr"
    assert item.is_open_now is True
    assert item.work_hours_rows[0] == ("Пн", "09:00–20:00")
    assert item.work_hours_rows[6] == ("Нд", "вихідний")


def test_map_embed_url_omitted_without_coordinates() -> None:
    StoreFactory(slug="no-coords", lat=None, lng=None)

    [item] = list_stores_with_status()

    assert item.map_embed_url is None


def test_map_embed_url_present_with_coordinates() -> None:
    StoreFactory(slug="with-coords", lat="50.44", lng="30.52")

    [item] = list_stores_with_status()

    assert item.map_embed_url is not None
    assert "50.44" in item.map_embed_url
    assert "30.52" in item.map_embed_url

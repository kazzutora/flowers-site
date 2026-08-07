"""DEV.md S0.9: snapshot test on the /stores/ template.

No snapshot library is in tech.md's frozen test stack, so this is a small
dependency-free golden-file check: render with a fixed context, compare
against a checked-in HTML file. First run creates the snapshot and skips;
commit the generated file and subsequent runs enforce it byte-for-byte.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from django.template.loader import render_to_string

from apps.stores.selectors import StoreListItem

SNAPSHOT_PATH = Path(__file__).parent / "__snapshots__" / "stores_list.html"


def _fixed_context() -> dict[str, object]:
    store = StoreListItem(
        slug="centr",
        name="Центр",
        address="вул. Хрещатик, 1",
        phone="+380671234567",
        lat=None,
        lng=None,
        work_hours={
            "mon": ["09:00", "20:00"],
            "tue": ["09:00", "20:00"],
            "wed": ["09:00", "20:00"],
            "thu": ["09:00", "20:00"],
            "fri": ["09:00", "20:00"],
            "sat": ["10:00", "18:00"],
            "sun": None,
        },
        is_open_now=True,
        work_hours_rows=[
            ("Пн", "09:00–20:00"),
            ("Вт", "09:00–20:00"),
            ("Ср", "09:00–20:00"),
            ("Чт", "09:00–20:00"),
            ("Пт", "09:00–20:00"),
            ("Сб", "10:00–18:00"),
            ("Нд", "вихідний"),
        ],
        map_embed_url=None,
    )
    return {
        "stores": [store],
        "breadcrumb_items": [
            {"label": "Головна", "url": "/"},
            {"label": "Наші магазини", "url": None},
        ],
        "main_nav": [],
        "header_stores": [],
        "header_current_store": None,
    }


def test_stores_list_template_matches_snapshot() -> None:
    rendered = render_to_string("stores/list.html", _fixed_context())

    if not SNAPSHOT_PATH.exists():
        SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT_PATH.write_text(rendered, encoding="utf-8")
        pytest.skip("snapshot created — re-run to verify")

    expected = SNAPSHOT_PATH.read_text(encoding="utf-8")
    assert rendered == expected, (
        "templates/stores/list.html rendering drifted from the stored "
        f"snapshot. If intentional, delete {SNAPSHOT_PATH} and re-run to "
        "regenerate it."
    )

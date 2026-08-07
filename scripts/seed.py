#!/usr/bin/env python
"""Idempotent seed script — tech.md §12.

Run as ``python scripts/seed.py`` (not a management command, per the
acceptance criterion in DEV.md S0.8). Every ``seed_*`` function is
idempotent: it upserts by a natural unique key, so re-running never
creates duplicates.

tech.md §12 describes the *eventual* full fixture set (stores, catalog,
live streams, gallery, orders, staff). Stage 0 only ships apps.stores, so
that's all this seeds today — each later slice adds its own seed_*
function here as its models land (S1.1 catalog, S2.1 live, S2.9 gallery,
S4.4 orders, S8.1 staff roles).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

import django

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.db import transaction  # noqa: E402

from apps.stores.models import Store  # noqa: E402

STORES: list[dict[str, Any]] = [
    {
        "name": "Центр",
        "slug": "centr",
        "address": "вул. Хрещатик, 15",
        "lat": "50.447500",
        "lng": "30.523400",
        "phone": "+380671112233",
        "work_hours": {
            "mon": ["09:00", "20:00"],
            "tue": ["09:00", "20:00"],
            "wed": ["09:00", "20:00"],
            "thu": ["09:00", "20:00"],
            "fri": ["09:00", "20:00"],
            "sat": ["10:00", "18:00"],
            "sun": ["10:00", "16:00"],
        },
        "is_active": True,
        "sort_order": 0,
    },
    {
        "name": "Позняки",
        "slug": "poznyaky",
        "address": "просп. Осокорський, 8",
        "lat": "50.401700",
        "lng": "30.627600",
        "phone": "+380672223344",
        "work_hours": {
            "mon": ["09:00", "20:00"],
            "tue": ["09:00", "20:00"],
            "wed": ["09:00", "20:00"],
            "thu": ["09:00", "20:00"],
            "fri": ["09:00", "20:00"],
            "sat": ["10:00", "18:00"],
            "sun": None,
        },
        "is_active": True,
        "sort_order": 1,
    },
]


def seed_stores() -> None:
    for data in STORES:
        slug = data["slug"]
        Store.objects.update_or_create(slug=slug, defaults=data)
    print(f"stores: {Store.objects.count()} present")


def seed_superuser() -> None:
    """Dev-only admin account for exploring /manage/ locally. Never used
    in prod — prod deploys don't run this script (tech.md §12: the
    fixture set is a local/test convenience, not a prod provisioning
    tool)."""
    user_model = get_user_model()
    user, _ = user_model.objects.get_or_create(
        username="admin",
        defaults={"is_staff": True, "is_superuser": True},
    )
    user.is_staff = True
    user.is_superuser = True
    user.set_password("admin12345")
    user.save()
    print("superuser: admin / admin12345 (dev only, do not use in prod)")


@transaction.atomic
def main() -> None:
    seed_stores()
    seed_superuser()
    print("Seed complete.")


if __name__ == "__main__":
    main()

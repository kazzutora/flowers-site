from __future__ import annotations

import factory
from factory.django import DjangoModelFactory, ImageField

from apps.stores.models import Store, StorePhoto

_DEFAULT_WORK_HOURS = {
    "mon": ["09:00", "20:00"],
    "tue": ["09:00", "20:00"],
    "wed": ["09:00", "20:00"],
    "thu": ["09:00", "20:00"],
    "fri": ["09:00", "20:00"],
    "sat": ["10:00", "18:00"],
    "sun": None,
}


class StoreFactory(DjangoModelFactory):
    class Meta:
        model = Store
        django_get_or_create = ("slug",)

    name = factory.Sequence(lambda n: f"Магазин {n}")
    slug = factory.Sequence(lambda n: f"store-{n}")
    address = "вул. Тестова, 1"
    lat = None
    lng = None
    phone = "+380671234567"
    work_hours = factory.LazyFunction(lambda: dict(_DEFAULT_WORK_HOURS))
    is_active = True
    sort_order = 0


class StorePhotoFactory(DjangoModelFactory):
    class Meta:
        model = StorePhoto

    store = factory.SubFactory(StoreFactory)
    sort_order = 0
    image = ImageField(filename="photo.jpg", width=800, height=600)

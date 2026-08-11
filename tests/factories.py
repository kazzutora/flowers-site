"""factory_boy factories. Every slice adds the models it introduces."""

import factory

from apps.core.models import HowToStep, SiteSettings, StaticPage


class SiteSettingsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SiteSettings
        django_get_or_create = ("id",)

    id = 1
    phone_primary = "+380501112233"
    site_name_uk = "Квіткова майстерня"
    site_name_ru = "Цветочная мастерская"
    working_hours_uk = "Щодня 9:00 - 20:00"


class StaticPageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StaticPage
        django_get_or_create = ("slug",)

    slug = factory.Sequence(lambda n: f"page-{n}")
    title_uk = factory.Sequence(lambda n: f"Сторінка {n}")
    body_uk = "<p>Текст сторінки</p>"
    is_published = True


class HowToStepFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = HowToStep

    order = factory.Sequence(lambda n: n)
    title_uk = factory.Sequence(lambda n: f"Крок {n}")
    text_uk = "Опис кроку"
    icon = "flower"
    is_active = True

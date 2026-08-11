#!/usr/bin/env python
"""Idempotent fixtures for development, tests and demos.

Every slice that adds a model appends to this script (section 18 of tech.md).
Stage 0 fills the core models only.
"""

from typing import Any


def seed_site_settings() -> None:
    from apps.core.models import SiteSettings

    settings = SiteSettings.load()
    settings.phone_primary = settings.phone_primary or "+380501112233"
    settings.email = settings.email or "hello@example.com"
    settings.viber_url = settings.viber_url or "viber://chat?number=%2B380501112233"
    settings.telegram_url = settings.telegram_url or "https://t.me/example"
    settings.instagram_url = settings.instagram_url or "https://instagram.com/example"
    settings.site_name_uk = settings.site_name_uk or "Квіткова майстерня"
    settings.site_name_ru = settings.site_name_ru or "Цветочная мастерская"
    settings.address_uk = settings.address_uk or "вул. Квіткова, 1"
    settings.address_ru = settings.address_ru or "ул. Цветочная, 1"
    settings.working_hours_uk = settings.working_hours_uk or "Щодня 9:00 - 20:00"
    settings.working_hours_ru = settings.working_hours_ru or "Ежедневно 9:00 - 20:00"
    settings.hero_title_uk = settings.hero_title_uk or "Квіти, які запам'ятовують"
    settings.hero_title_ru = settings.hero_title_ru or "Цветы, которые запоминают"
    settings.hero_subtitle_uk = (
        settings.hero_subtitle_uk or "Букети, композиції та оформлення залів ручної роботи."
    )
    settings.hero_subtitle_ru = (
        settings.hero_subtitle_ru or "Букеты, композиции и оформление залов ручной работы."
    )
    settings.save()


STATIC_PAGES: tuple[dict[str, Any], ...] = (
    {
        "slug": "pro-nas",
        "title_uk": "Про нас",
        "title_ru": "О нас",
        "body_uk": "<p>Ми збираємо букети вручну і працюємо з квітами щодня.</p>",
        "body_ru": "<p>Мы собираем букеты вручную и работаем с цветами каждый день.</p>",
    },
    {
        "slug": "dostavka-i-oplata",
        "title_uk": "Доставка і оплата",
        "title_ru": "Доставка и оплата",
        "body_uk": "<p>Доставляємо по місту. Оплата картою або готівкою.</p>",
        "body_ru": "<p>Доставляем по городу. Оплата картой или наличными.</p>",
    },
    {
        "slug": "faq",
        "title_uk": "Питання і відповіді",
        "title_ru": "Вопросы и ответы",
        "body_uk": (
            "<h2>За скільки замовляти?</h2><p>Букет - за день, оформлення залу - за тиждень.</p>"
        ),
        "body_ru": (
            "<h2>За сколько заказывать?</h2><p>Букет - за день, оформление зала - за неделю.</p>"
        ),
    },
    {
        "slug": "polityka-konfidentsiynosti",
        "title_uk": "Політика конфіденційності",
        "title_ru": "Политика конфиденциальности",
        "body_uk": "<p>Ми зберігаємо лише те, що потрібно для звʼязку з вами.</p>",
        "body_ru": "<p>Мы храним только то, что нужно для связи с вами.</p>",
    },
)

HOW_TO_STEPS: tuple[dict[str, Any], ...] = (
    {
        "order": 1,
        "icon": "search",
        "title_uk": "Оберіть роботу",
        "title_ru": "Выберите работу",
        "text_uk": "Знайдіть у галереї те, що подобається, і запамʼятайте номер.",
        "text_ru": "Найдите в галерее то, что нравится, и запомните номер.",
    },
    {
        "order": 2,
        "icon": "phone",
        "title_uk": "Зателефонуйте",
        "title_ru": "Позвоните",
        "text_uk": "Назвіть номер роботи, дату і бюджет. Підкажемо, що можливо.",
        "text_ru": "Назовите номер работы, дату и бюджет. Подскажем, что возможно.",
    },
    {
        "order": 3,
        "icon": "gift",
        "title_uk": "Заберіть або отримайте",
        "title_ru": "Заберите или получите",
        "text_uk": "Зберемо до потрібної години. Доставимо або віддамо в майстерні.",
        "text_ru": "Соберём к нужному часу. Доставим или отдадим в мастерской.",
    },
)


def seed_static_pages() -> None:
    from apps.core.models import StaticPage

    for page in STATIC_PAGES:
        StaticPage.objects.update_or_create(slug=page["slug"], defaults=page)


def seed_how_to_steps() -> None:
    from apps.core.models import HowToStep

    for step in HOW_TO_STEPS:
        HowToStep.objects.update_or_create(order=step["order"], defaults=step)


def run() -> dict[str, int]:
    """Fill the database. Running it twice changes nothing."""
    from apps.core.models import HowToStep, SiteSettings, StaticPage

    seed_site_settings()
    seed_static_pages()
    seed_how_to_steps()
    return {
        "site_settings": SiteSettings.objects.count(),
        "static_pages": StaticPage.objects.count(),
        "how_to_steps": HowToStep.objects.count(),
    }


def main() -> None:
    import django

    django.setup()
    for name, count in run().items():
        print(f"{name}: {count}")


if __name__ == "__main__":
    main()

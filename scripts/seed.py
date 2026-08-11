#!/usr/bin/env python
"""Idempotent fixtures for development, tests and demos.

Every slice that adds a model appends to this script (section 18 of tech.md).
"""

import io
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


OCCASIONS: tuple[dict[str, Any], ...] = (
    {"slug": "podarunok", "name_uk": "Подарунок", "name_ru": "Подарок", "order": 1},
    {"slug": "vesillya", "name_uk": "Весілля", "name_ru": "Свадьба", "order": 2},
    {"slug": "yuvilei", "name_uk": "Ювілей", "name_ru": "Юбилей", "order": 3},
    {
        "slug": "den-narodzhennya",
        "name_uk": "День народження",
        "name_ru": "День рождения",
        "order": 4,
    },
    {"slug": "korporatyv", "name_uk": "Корпоратив", "name_ru": "Корпоратив", "order": 5},
    {"slug": "traurni", "name_uk": "Траурні", "name_ru": "Траурные", "order": 6},
    {
        "slug": "oformlennya-zaly",
        "name_uk": "Оформлення залу",
        "name_ru": "Оформление зала",
        "order": 7,
    },
)

TAG_GROUPS: tuple[dict[str, Any], ...] = (
    {
        "slug": "type",
        "name_uk": "Тип виробу",
        "name_ru": "Тип изделия",
        "filter_kind": "checkbox",
        "order": 1,
        "tags": (
            ("buket", "Букет", "Букет", ""),
            ("kompozytsiya", "Композиція", "Композиция", ""),
            ("koshyk", "Кошик", "Корзина", ""),
            ("korobka", "Коробка", "Коробка", ""),
            ("vinok", "Вінок", "Венок", ""),
        ),
    },
    {
        "slug": "color",
        "name_uk": "Колір",
        "name_ru": "Цвет",
        "filter_kind": "color_swatch",
        "order": 2,
        "tags": (
            ("bilyi", "Білий", "Белый", "#FFFFFF"),
            ("rozhevyi", "Рожевий", "Розовый", "#F2C9C9"),
            ("chervonyi", "Червоний", "Красный", "#C0392B"),
            ("zhovtyi", "Жовтий", "Жёлтый", "#F1C40F"),
            ("fioletovyi", "Фіолетовий", "Фиолетовый", "#8E6BB0"),
            ("zelenyi", "Зелений", "Зелёный", "#5E7355"),
        ),
    },
    {
        "slug": "flower",
        "name_uk": "Квіти",
        "name_ru": "Цветы",
        "filter_kind": "checkbox",
        "order": 3,
        "tags": (
            ("troyandy", "Троянди", "Розы", ""),
            ("pivonii", "Півонії", "Пионы", ""),
            ("tyulpany", "Тюльпани", "Тюльпаны", ""),
            ("hortenziyi", "Гортензії", "Гортензии", ""),
            ("eustoma", "Еустома", "Эустома", ""),
        ),
    },
    {
        "slug": "season",
        "name_uk": "Сезон",
        "name_ru": "Сезон",
        "filter_kind": "checkbox",
        "order": 4,
        "tags": (
            ("vesna", "Весна", "Весна", ""),
            ("lito", "Літо", "Лето", ""),
            ("osin", "Осінь", "Осень", ""),
            ("zyma", "Зима", "Зима", ""),
        ),
    },
)

WORK_TITLES: tuple[tuple[str, str], ...] = (
    ("Букет із троянд", "Букет из роз"),
    ("Композиція з півоній", "Композиция из пионов"),
    ("Кошик польових квітів", "Корзина полевых цветов"),
    ("Коробка з еустомою", "Коробка с эустомой"),
    ("Весільний букет нареченої", "Свадебный букет невесты"),
    ("Букет тюльпанів", "Букет тюльпанов"),
    ("Гортензії в коробці", "Гортензии в коробке"),
    ("Осіння композиція", "Осенняя композиция"),
    ("Зимовий вінок", "Зимний венок"),
    ("Букет на день народження", "Букет на день рождения"),
)

# Which tags each seeded work carries, by position in WORK_TITLES.
WORK_TAGS: tuple[tuple[str, ...], ...] = (
    ("buket", "chervonyi", "troyandy", "zyma"),
    ("kompozytsiya", "rozhevyi", "pivonii", "vesna"),
    ("koshyk", "bilyi", "eustoma", "lito"),
    ("korobka", "zelenyi", "eustoma", "lito"),
    ("buket", "bilyi", "troyandy", "vesna"),
    ("buket", "zhovtyi", "tyulpany", "vesna"),
    ("korobka", "fioletovyi", "hortenziyi", "osin"),
    ("kompozytsiya", "zhovtyi", "hortenziyi", "osin"),
    ("vinok", "zelenyi", "troyandy", "zyma"),
    ("buket", "rozhevyi", "pivonii", "lito"),
)

WORK_OCCASIONS: tuple[tuple[str, ...], ...] = (
    ("podarunok", "den-narodzhennya"),
    ("podarunok", "yuvilei"),
    ("podarunok",),
    ("den-narodzhennya",),
    ("vesillya",),
    ("den-narodzhennya", "podarunok"),
    ("yuvilei", "korporatyv"),
    ("korporatyv",),
    ("oformlennya-zaly",),
    ("den-narodzhennya",),
)

WORKS_TOTAL = 30
PLACEHOLDER_COLORS = ("#F2E3DF", "#E7E0D8", "#F1E4C3", "#DFE7DC", "#EFE0EC")


def seed_occasions() -> None:
    from apps.catalog.models import Occasion

    for occasion in OCCASIONS:
        Occasion.objects.update_or_create(slug=occasion["slug"], defaults=occasion)


def seed_tags() -> None:
    from apps.catalog.models import Tag, TagGroup

    for group_data in TAG_GROUPS:
        tags = group_data["tags"]
        group, _created = TagGroup.objects.update_or_create(
            slug=group_data["slug"],
            defaults={key: value for key, value in group_data.items() if key != "tags"},
        )
        for order, (slug, name_uk, name_ru, color_hex) in enumerate(tags, start=1):
            Tag.objects.update_or_create(
                slug=slug,
                defaults={
                    "group": group,
                    "name_uk": name_uk,
                    "name_ru": name_ru,
                    "color_hex": color_hex,
                    "order": order,
                },
            )


def _placeholder_image(index: int) -> bytes:
    """A flat coloured JPEG. Real pixels, so the rendition pipeline has work."""
    from PIL import Image

    color = PLACEHOLDER_COLORS[index % len(PLACEHOLDER_COLORS)]
    buffer = io.BytesIO()
    Image.new("RGB", (1200, 1500), color).save(buffer, format="JPEG", quality=70)
    return buffer.getvalue()


def seed_works() -> None:
    from django.core.files.base import ContentFile

    from apps.catalog.models import Occasion, Tag, Work, WorkImage

    occasions = {item.slug: item for item in Occasion.objects.all()}
    tags = {item.slug: item for item in Tag.objects.all()}

    for index in range(WORKS_TOTAL):
        position = index % len(WORK_TITLES)
        title_uk, title_ru = WORK_TITLES[position]
        # The title carries the run number so the natural key stays stable
        # across runs while the article is left to the sequence.
        numbered_uk = title_uk if index < len(WORK_TITLES) else f"{title_uk} №{index + 1}"
        numbered_ru = title_ru if index < len(WORK_TITLES) else f"{title_ru} №{index + 1}"

        work = Work.objects.filter(title_uk=numbered_uk).first()
        if work is None:
            work = Work(title_uk=numbered_uk)
        work.title_ru = numbered_ru
        work.composition_uk = "троянди, евкаліпт, гіпсофіла"
        work.composition_ru = "розы, эвкалипт, гипсофила"
        work.size_text_uk = "висота 45 см"
        work.size_text_ru = "высота 45 см"
        work.status = Work.Status.PUBLISHED
        work.price_from = 750 + position * 50
        work.save()

        work.occasions.set(
            [occasions[slug] for slug in WORK_OCCASIONS[position] if slug in occasions]
        )
        work.tags.set([tags[slug] for slug in WORK_TAGS[position] if slug in tags])

        if not work.images.exists():
            WorkImage.objects.create(
                work=work,
                alt_uk=numbered_uk,
                alt_ru=numbered_ru,
                image=ContentFile(_placeholder_image(index), name=f"seed-{work.article}.jpg"),
            )


def run() -> dict[str, int]:
    """Fill the database. Running it twice changes nothing."""
    from apps.catalog.models import Occasion, Tag, TagGroup, Work, WorkImage
    from apps.core.models import HowToStep, SiteSettings, StaticPage

    seed_site_settings()
    seed_static_pages()
    seed_how_to_steps()
    seed_occasions()
    seed_tags()
    seed_works()
    return {
        "site_settings": SiteSettings.objects.count(),
        "static_pages": StaticPage.objects.count(),
        "how_to_steps": HowToStep.objects.count(),
        "occasions": Occasion.objects.count(),
        "tag_groups": TagGroup.objects.count(),
        "tags": Tag.objects.count(),
        "works": Work.objects.count(),
        "work_images": WorkImage.objects.count(),
    }


def main() -> None:
    import django

    django.setup()
    for name, count in run().items():
        print(f"{name}: {count}")


if __name__ == "__main__":
    main()

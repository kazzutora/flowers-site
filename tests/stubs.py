"""Model shaped stubs for the kitchen sink.

The page must render every primitive without a database and without the catalog
models, which land in stage 1. Field names match tech.md exactly, so a primitive
that renders here renders against the real models too.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from django.core.paginator import Paginator
from django.templatetags.static import static

from apps.core.models import TranslatedMixin


class Related(list):  # type: ignore[type-arg]
    """Stands in for a related manager: templates call `.all`."""

    def all(self) -> "Related":
        return self


@dataclass
class StubFile:
    url: str


@dataclass
class StubRendition:
    preset: str
    image_format: str
    file: StubFile
    width: int
    height: int


@dataclass
class StubImage(TranslatedMixin):
    alt_uk: str = "Букет із троянд"
    alt_ru: str = "Букет из роз"
    renditions_ready: bool = True
    renditions: Related = field(default_factory=Related)


@dataclass
class StubWork(TranslatedMixin):
    article: int = 147
    slug: str = "147-buket-troyand"
    title_uk: str = "Букет із троянд"
    title_ru: str = "Букет из роз"
    composition_uk: str = "троянди, евкаліпт, гіпсофіла"
    composition_ru: str = "розы, эвкалипт, гипсофила"
    price_from: Decimal | None = Decimal("950.00")
    main_image: StubImage | None = None

    def get_absolute_url(self) -> str:
        return f"/robota/{self.slug}/"


@dataclass
class StubPost(TranslatedMixin):
    slug: str = "yak-obraty-buket"
    title_uk: str = "Як обрати букет"
    title_ru: str = "Как выбрать букет"
    excerpt_uk: str = "Коротка інструкція для тих, хто обирає квіти вперше."
    excerpt_ru: str = "Короткая инструкция для тех, кто выбирает цветы впервые."
    cover: StubFile | None = None

    def get_absolute_url(self) -> str:
        return f"/blog/{self.slug}/"


@dataclass
class StubReview(TranslatedMixin):
    author_name: str = "Олена"
    text_uk: str = "Букет був свіжий, зібрали за годину. Дякую!"
    text_ru: str = "Букет был свежий, собрали за час. Спасибо!"
    rating: int | None = 5
    photo: StubFile | None = None
    work: StubWork | None = None


@dataclass
class StubTagGroup(TranslatedMixin):
    slug: str = "type"
    name_uk: str = "Тип виробу"
    name_ru: str = "Тип изделия"
    filter_kind: str = "checkbox"
    tags: Related = field(default_factory=Related)


@dataclass
class StubTag(TranslatedMixin):
    slug: str = "buket"
    name_uk: str = "Букет"
    name_ru: str = "Букет"
    color_hex: str = ""
    group: StubTagGroup | None = None


def _renditions() -> Related:
    """Real sample files, so the browser actually decodes avif and webp."""
    sizes = {"thumb": (400, 500), "card": (800, 1000)}
    items = Related()
    for preset, (width, height) in sizes.items():
        for image_format in ("avif", "webp"):
            items.append(
                StubRendition(
                    preset=preset,
                    image_format=image_format,
                    file=StubFile(static(f"img/sample-{width}.{image_format}")),
                    width=width,
                    height=height,
                )
            )
    return items


def kitchen_sink_context() -> dict[str, Any]:
    image = StubImage(renditions=_renditions())
    empty_image = StubImage(renditions_ready=False)
    work = StubWork(main_image=image)
    sample = StubFile(static("img/sample-800.webp"))
    page_obj = Paginator(list(range(48)), 12).get_page(2)

    colors = StubTagGroup(slug="color", name_uk="Колір", name_ru="Цвет", filter_kind="color_swatch")
    colors.tags = Related(
        [
            StubTag(
                slug="bilyi", name_uk="Білий", name_ru="Белый", color_hex="#FFFFFF", group=colors
            ),
            StubTag(
                slug="rozhevyi",
                name_uk="Рожевий",
                name_ru="Розовый",
                color_hex="#F2C9C9",
                group=colors,
            ),
        ]
    )

    types = StubTagGroup()
    types.tags = Related(
        [
            StubTag(slug="buket", name_uk="Букет", name_ru="Букет", group=types),
            StubTag(slug="kompozytsiya", name_uk="Композиція", name_ru="Композиция", group=types),
        ]
    )

    return {
        "work": work,
        "work_without_renditions": StubWork(article=148, main_image=empty_image),
        "work_without_image": StubWork(article=149, title_uk="", title_ru=""),
        "image": image,
        "image_pending": empty_image,
        "images": Related([image, image]),
        "post": StubPost(cover=sample),
        "post_without_cover": StubPost(title_uk="Пост без обкладинки", cover=None),
        "review": StubReview(work=work, photo=sample),
        "review_plain": StubReview(author_name="Ігор", rating=None),
        "page_obj": page_obj,
        "tag_group_checkbox": types,
        "tag_group_colors": colors,
        "active_slugs": ["buket", "bilyi"],
        "select_options": [("phone", "Телефон"), ("viber", "Viber"), ("telegram", "Telegram")],
        "breadcrumb_items": [
            {"label": "Головна", "url": "/"},
            {"label": "Галерея", "url": "/galereya/"},
            {"label": "Букет із троянд"},
        ],
    }

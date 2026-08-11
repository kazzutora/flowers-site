"""factory_boy factories. Every slice adds the models it introduces."""

import io

import factory
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.catalog.models import Occasion, Tag, TagGroup, Work, WorkImage
from apps.core.models import HowToStep, SiteSettings, StaticPage
from apps.reviews.models import Review


def photo_bytes(
    width: int = 1200, height: int = 1500, color: str = "#F2C9C9", image_format: str = "JPEG"
) -> bytes:
    """Real pixels for the upload and rendition paths."""
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), color).save(buffer, format=image_format)
    return buffer.getvalue()


def uploaded_photo(name: str = "photo.jpg", **kwargs: object) -> SimpleUploadedFile:
    return SimpleUploadedFile(name, photo_bytes(**kwargs), content_type="image/jpeg")  # type: ignore[arg-type]


class SiteSettingsFactory(factory.django.DjangoModelFactory[SiteSettings]):
    class Meta:
        model = SiteSettings
        django_get_or_create = ("id",)

    id = 1
    phone_primary = "+380501112233"
    site_name_uk = "Квіткова майстерня"
    site_name_ru = "Цветочная мастерская"
    working_hours_uk = "Щодня 9:00 - 20:00"


class StaticPageFactory(factory.django.DjangoModelFactory[StaticPage]):
    class Meta:
        model = StaticPage
        django_get_or_create = ("slug",)

    slug = factory.Sequence(lambda n: f"page-{n}")
    title_uk = factory.Sequence(lambda n: f"Сторінка {n}")
    body_uk = "<p>Текст сторінки</p>"
    is_published = True


class HowToStepFactory(factory.django.DjangoModelFactory[HowToStep]):
    class Meta:
        model = HowToStep

    order = factory.Sequence(lambda n: n)
    title_uk = factory.Sequence(lambda n: f"Крок {n}")
    text_uk = "Опис кроку"
    icon = "flower"
    is_active = True


class OccasionFactory(factory.django.DjangoModelFactory[Occasion]):
    class Meta:
        model = Occasion
        django_get_or_create = ("slug",)

    slug = factory.Sequence(lambda n: f"pryvid-{n}")
    name_uk = factory.Sequence(lambda n: f"Привід {n}")
    name_ru = factory.Sequence(lambda n: f"Повод {n}")
    is_active = True
    show_on_home = True


class TagGroupFactory(factory.django.DjangoModelFactory[TagGroup]):
    class Meta:
        model = TagGroup
        django_get_or_create = ("slug",)

    slug = factory.Sequence(lambda n: f"hrupa-{n}")
    name_uk = factory.Sequence(lambda n: f"Група {n}")
    filter_kind = TagGroup.FilterKind.CHECKBOX
    is_active = True


class TagFactory(factory.django.DjangoModelFactory[Tag]):
    class Meta:
        model = Tag
        django_get_or_create = ("slug",)

    group = factory.SubFactory(TagGroupFactory)
    slug = factory.Sequence(lambda n: f"teh-{n}")
    name_uk = factory.Sequence(lambda n: f"Тег {n}")
    is_active = True


class WorkFactory(factory.django.DjangoModelFactory[Work]):
    class Meta:
        model = Work
        skip_postgeneration_save = True

    title_uk = factory.Sequence(lambda n: f"Робота {n}")
    status = Work.Status.PUBLISHED

    @factory.post_generation
    def occasions(self, create: bool, extracted: list[Occasion] | None, **kwargs: object) -> None:
        if create and extracted:
            self.occasions.set(extracted)

    @factory.post_generation
    def tags(self, create: bool, extracted: list[Tag] | None, **kwargs: object) -> None:
        if create and extracted:
            self.tags.set(extracted)


class ReviewFactory(factory.django.DjangoModelFactory[Review]):
    class Meta:
        model = Review

    author_name = factory.Sequence(lambda n: f"Автор {n}")
    text_uk = "Букет був свіжий, зібрали за годину."
    rating = 5
    source = Review.Source.ADMIN
    status = Review.Status.PUBLISHED
    consent = True


class WorkImageFactory(factory.django.DjangoModelFactory[WorkImage]):
    class Meta:
        model = WorkImage

    work = factory.SubFactory(WorkFactory)
    # Real pixels: the rendition pipeline has to have something to resize.
    image = factory.django.ImageField(width=800, height=1000, color="#F2C9C9", format="JPEG")

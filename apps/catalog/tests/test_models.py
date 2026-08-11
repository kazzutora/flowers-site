"""Sections 4.1 to 4.6 and 5: the schema and the rules baked into it."""

import re
from collections.abc import Iterator
from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.utils import timezone, translation
from hypothesis import given
from hypothesis import strategies as st

from apps.catalog.models import (
    ARTICLE_SEQUENCE,
    SLUG_TITLE_LIMIT,
    Tag,
    TagGroup,
    Work,
    WorkImage,
    build_work_slug,
    next_article,
    translit,
)
from tests.factories import (
    OccasionFactory,
    TagFactory,
    TagGroupFactory,
    WorkFactory,
    WorkImageFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def fresh_sequence() -> Iterator[None]:
    """Rewind the article sequence: other tests leave it wherever they stopped."""
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT setval('{ARTICLE_SEQUENCE}', 100, false)")
    yield


# --- articles and slugs -------------------------------------------------------


def test_first_work_gets_article_100_and_the_next_one_101(fresh_sequence: None) -> None:
    first = WorkFactory.create(title_uk="Перша робота")
    second = WorkFactory.create(title_uk="Друга робота")

    assert first.article == 100
    assert second.article == 101


def test_article_and_slug_survive_a_title_change() -> None:
    work = WorkFactory.create(title_uk="Букет із троянд")
    article, slug = work.article, work.slug

    work.title_uk = "Зовсім інша назва"
    work.save()
    work.refresh_from_db()

    assert work.article == article
    assert work.slug == slug


def test_work_without_a_title_is_slugged_by_its_article() -> None:
    work = WorkFactory.create(title_uk="")

    assert work.slug == str(work.article)


def test_slug_is_transliterated_from_the_ukrainian_title() -> None:
    work = WorkFactory.create(title_uk="Їжачок у тумані")

    assert work.slug == f"{work.article}-yizhachok-u-tumani"


def test_two_reads_of_the_sequence_differ_and_a_rollback_keeps_the_number() -> None:
    first = next_article()

    with pytest.raises(RuntimeError), transaction.atomic():
        next_article()
        raise RuntimeError("rolled back on purpose")

    third = next_article()

    assert third > first + 1, "a rolled back transaction must not hand the number back"


@given(st.text(max_size=250))
def test_slug_is_always_a_bounded_ascii_slug(title: str) -> None:
    slug = build_work_slug(147, title)

    assert slug.isascii()
    assert re.fullmatch(r"[a-z0-9][a-z0-9_-]*", slug), slug
    assert len(slug) <= 200


@given(st.text(alphabet="абвгґдеєжзиіїйклмнопрстуфхцчшщьюя ʼ", max_size=250))
def test_cyrillic_titles_never_leak_into_the_slug(title: str) -> None:
    slug = build_work_slug(1000, title)

    assert slug.startswith("1000")
    assert len(slug) <= len("1000-") + SLUG_TITLE_LIMIT


@pytest.mark.parametrize(
    "title",
    ["", "   ", "🌸🌸🌸", "—", "Х" * 200],
)
def test_awkward_titles_still_produce_a_usable_slug(title: str) -> None:
    slug = build_work_slug(147, title)

    assert slug.startswith("147")
    assert re.fullmatch(r"[a-z0-9][a-z0-9_-]*", slug)


def test_articles_make_slugs_unique_for_identical_titles() -> None:
    assert build_work_slug(100, "Букет") != build_work_slug(101, "Букет")


def test_transliteration_uses_the_word_start_forms() -> None:
    assert translit("Ялинка") == "yalynka"
    assert translit("Мая") == "maia"


# --- constraints --------------------------------------------------------------


def test_a_work_cannot_have_two_main_photos() -> None:
    work = WorkFactory.create()
    first = WorkImageFactory.create(work=work)
    second = WorkImageFactory.create(work=work)

    assert first.is_main is True
    assert second.is_main is False

    # Straight to the database: the model would politely demote the other one.
    with pytest.raises(IntegrityError), transaction.atomic():
        WorkImage.objects.filter(pk=second.pk).update(is_main=True)


def test_price_to_below_price_from_is_rejected() -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        WorkFactory.create(price_from=Decimal("900.00"), price_to=Decimal("500.00"))


def test_an_open_price_range_is_allowed() -> None:
    WorkFactory.create(price_from=Decimal("900.00"), price_to=None)
    WorkFactory.create(price_from=None, price_to=Decimal("900.00"))


def test_a_rendition_variant_exists_only_once() -> None:
    image = WorkImageFactory.create()
    image.renditions.create(preset="card", image_format="avif", file="renditions/a.avif")

    with pytest.raises(IntegrityError), transaction.atomic():
        image.renditions.create(preset="card", image_format="avif", file="renditions/b.avif")


# --- tag validation -----------------------------------------------------------


@pytest.mark.parametrize("slug", ["sort", "page", "q", "a"])
def test_a_tag_cannot_take_a_reserved_parameter_name(slug: str) -> None:
    group = TagGroupFactory.create(slug="type")
    tag = Tag(group=group, slug=slug, name_uk="Щось")

    with pytest.raises(ValidationError) as error:
        tag.full_clean()

    assert "slug" in error.value.error_dict


def test_a_tag_cannot_take_the_slug_of_a_group() -> None:
    TagGroupFactory.create(slug="color", filter_kind=TagGroup.FilterKind.COLOR_SWATCH)
    group = TagGroupFactory.create(slug="type")
    tag = Tag(group=group, slug="color", name_uk="Колір")

    with pytest.raises(ValidationError) as error:
        tag.full_clean()

    assert "slug" in error.value.error_dict


def test_a_colour_swatch_tag_needs_a_colour() -> None:
    group = TagGroupFactory.create(slug="color", filter_kind=TagGroup.FilterKind.COLOR_SWATCH)
    tag = Tag(group=group, slug="bilyi", name_uk="Білий")

    with pytest.raises(ValidationError) as error:
        tag.full_clean()

    assert "color_hex" in error.value.error_dict


def test_a_checkbox_tag_carries_no_colour() -> None:
    group = TagGroupFactory.create(slug="type")
    tag = Tag(group=group, slug="buket", name_uk="Букет", color_hex="#FFFFFF")

    with pytest.raises(ValidationError) as error:
        tag.full_clean()

    assert "color_hex" in error.value.error_dict


def test_a_valid_tag_passes_validation() -> None:
    group = TagGroupFactory.create(slug="type")

    Tag(group=group, slug="buket", name_uk="Букет").full_clean()


# --- translations -------------------------------------------------------------


def test_translation_follows_the_active_language() -> None:
    work = WorkFactory.create(title_uk="Букет із троянд", title_ru="Букет из роз")

    with translation.override("ru"):
        assert work.tr("title") == "Букет из роз"
    with translation.override("uk"):
        assert work.tr("title") == "Букет із троянд"


def test_an_empty_russian_field_falls_back_to_ukrainian() -> None:
    work = WorkFactory.create(title_uk="Букет із троянд", title_ru="")

    with translation.override("ru"):
        assert work.tr("title") == "Букет із троянд"


# --- ordering and managers ----------------------------------------------------


def test_drafts_do_not_float_to_the_top_of_a_list() -> None:
    WorkFactory.create(title_uk="Чернетка", status=Work.Status.DRAFT)
    published = WorkFactory.create(title_uk="Опублікована", status=Work.Status.PUBLISHED)

    assert Work.objects.first() == published


def test_the_published_manager_hides_drafts_and_archives() -> None:
    published = WorkFactory.create(status=Work.Status.PUBLISHED)
    WorkFactory.create(status=Work.Status.DRAFT)
    WorkFactory.create(status=Work.Status.ARCHIVED)

    assert list(Work.published.all()) == [published]


def test_publishing_stamps_published_at_once() -> None:
    work = WorkFactory.create(status=Work.Status.DRAFT)
    assert work.published_at is None

    work.status = Work.Status.PUBLISHED
    work.save()
    first_stamp = work.published_at

    work.title_uk = "Нова назва"
    work.save()

    assert work.published_at == first_stamp


def test_a_scheduled_work_is_not_published_yet() -> None:
    work = WorkFactory.create(status=Work.Status.PUBLISHED)
    Work.objects.filter(pk=work.pk).update(published_at=timezone.now() + timedelta(days=1))

    assert Work.published.count() == 0


def test_pinned_works_come_first() -> None:
    WorkFactory.create(title_uk="Звичайна")
    pinned = WorkFactory.create(title_uk="Закріплена", is_pinned=True)

    assert Work.objects.first() == pinned


# --- photos -------------------------------------------------------------------


def test_photos_line_up_and_only_the_first_one_is_main() -> None:
    work = WorkFactory.create()
    images = [WorkImageFactory.create(work=work) for _ in range(3)]

    assert [image.order for image in images] == [0, 1, 2]
    assert [image.is_main for image in images] == [True, False, False]
    assert work.images.filter(is_main=True).count() == 1


def test_deleting_the_main_photo_promotes_the_next_one() -> None:
    work = WorkFactory.create()
    first = WorkImageFactory.create(work=work)
    second = WorkImageFactory.create(work=work)

    first.delete()
    second.refresh_from_db()

    assert second.is_main is True


def test_main_image_is_the_flagged_one() -> None:
    work = WorkFactory.create()
    WorkImageFactory.create(work=work)
    second = WorkImageFactory.create(work=work)
    second.is_main = True
    second.save()

    assert work.main_image == second
    assert work.images.filter(is_main=True).count() == 1


def test_alt_text_falls_back_to_the_work_title_and_occasion() -> None:
    occasion = OccasionFactory.create(name_uk="Весілля")
    work = WorkFactory.create(title_uk="Букет нареченої", occasions=[occasion])
    image = WorkImageFactory.create(work=work)

    assert image.alt_text == "Букет нареченої"

    work.title_uk = ""
    work.save()
    image.refresh_from_db()

    assert image.alt_text == "Весілля"


def test_tags_and_occasions_attach_to_a_work() -> None:
    occasion = OccasionFactory.create(slug="vesillya")
    tag = TagFactory.create(slug="buket")
    work = WorkFactory.create(occasions=[occasion], tags=[tag])

    assert list(work.occasions.all()) == [occasion]
    assert list(work.tags.all()) == [tag]

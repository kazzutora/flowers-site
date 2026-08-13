"""Section 4.4 and 4.5 as the owner meets them: the admin form and its rules."""

from typing import Any

import pytest
from django.test import Client

from apps.catalog.models import Work
from tests.factories import (
    OccasionFactory,
    TagGroupFactory,
    WorkFactory,
    WorkImageFactory,
    uploaded_photo,
)

pytestmark = pytest.mark.django_db

ADD_URL = "/admin/catalog/work/add/"


def _work_form(**overrides: Any) -> dict[str, Any]:
    """Everything the change form posts, with the photo formset left empty."""
    data: dict[str, Any] = {
        "title_uk": "Букет із троянд",
        "title_ru": "",
        "description_uk": "",
        "description_ru": "",
        "composition_uk": "",
        "composition_ru": "",
        "size_text_uk": "",
        "size_text_ru": "",
        "price_from": "",
        "price_to": "",
        "price_note_uk": "",
        "price_note_ru": "",
        "cost": "",
        "status": Work.Status.DRAFT,
        "order": "0",
        "published_at_0": "",
        "published_at_1": "",
        "seo_title_uk": "",
        "seo_title_ru": "",
        "seo_description_uk": "",
        "seo_description_ru": "",
        "images-TOTAL_FORMS": "0",
        "images-INITIAL_FORMS": "0",
        "images-MIN_NUM_FORMS": "0",
        "images-MAX_NUM_FORMS": "1000",
    }
    data.update(overrides)
    return data


def _with_photos(count: int, **overrides: Any) -> dict[str, Any]:
    data = _work_form(**overrides)
    data["images-TOTAL_FORMS"] = str(count)
    for index in range(count):
        data[f"images-{index}-image"] = uploaded_photo(f"photo-{index}.jpg")
        data[f"images-{index}-alt_uk"] = ""
        data[f"images-{index}-alt_ru"] = ""
        # A freshly added row carries no position yet, exactly like in a browser.
        data[f"images-{index}-order"] = ""
    return data


def test_publishing_without_a_photo_is_rejected(admin_client: Client) -> None:
    response = admin_client.post(ADD_URL, _work_form(status=Work.Status.PUBLISHED))

    assert response.status_code == 200, "the form is redisplayed, not saved"
    assert Work.objects.count() == 0


def test_a_draft_may_be_saved_without_photos(admin_client: Client) -> None:
    response = admin_client.post(ADD_URL, _work_form(status=Work.Status.DRAFT))

    assert response.status_code == 302
    assert Work.objects.get().status == Work.Status.DRAFT


def test_a_new_work_published_with_photos_goes_through(admin_client: Client) -> None:
    response = admin_client.post(ADD_URL, _with_photos(3, status=Work.Status.PUBLISHED))

    assert response.status_code == 302
    work = Work.objects.get()
    assert work.status == Work.Status.PUBLISHED
    assert work.published_at is not None
    assert [image.order for image in work.images.all()] == [0, 1, 2]
    assert work.images.filter(is_main=True).count() == 1


def test_the_first_photo_added_becomes_the_main_one(admin_client: Client) -> None:
    admin_client.post(ADD_URL, _with_photos(2, status=Work.Status.PUBLISHED))

    work = Work.objects.get()
    assert work.main_image == work.images.order_by("order").first()


def test_the_publish_action_skips_works_without_photos(admin_client: Client) -> None:
    work = WorkFactory.create(status=Work.Status.DRAFT)

    admin_client.post(
        "/admin/catalog/work/",
        {"action": "publish", "_selected_action": [str(work.pk)], "index": "0"},
        follow=True,
    )
    work.refresh_from_db()

    assert work.status == Work.Status.DRAFT


def test_the_archive_action_moves_works_out_of_the_gallery(admin_client: Client) -> None:
    work = WorkFactory.create(status=Work.Status.PUBLISHED)

    admin_client.post(
        "/admin/catalog/work/",
        {"action": "archive", "_selected_action": [str(work.pk)], "index": "0"},
        follow=True,
    )
    work.refresh_from_db()

    assert work.status == Work.Status.ARCHIVED
    assert Work.published.count() == 0


def test_admin_pages_open(admin_client: Client) -> None:
    """Guards the drag-and-drop wiring: a template clash shows up here first."""
    OccasionFactory.create(slug="vesillya")
    TagGroupFactory.create(slug="type")
    work = WorkFactory.create()

    for url in (
        "/admin/catalog/work/",
        ADD_URL,
        f"/admin/catalog/work/{work.pk}/change/",
        "/admin/catalog/occasion/",
        "/admin/catalog/taggroup/",
        "/admin/catalog/tag/",
    ):
        assert admin_client.get(url).status_code == 200, url


def test_the_admin_finds_a_work_by_its_article(admin_client: Client) -> None:
    work = WorkFactory.create(title_uk="Букет із троянд")

    body = admin_client.get(f"/admin/catalog/work/?q=№{work.article}").content.decode()

    assert "Букет із троянд" in body


def test_the_cost_stays_out_of_the_change_list(admin_client: Client) -> None:
    WorkFactory.create(title_uk="Букет", cost="777.00")

    body = admin_client.get("/admin/catalog/work/").content.decode()

    assert "777" not in body


def test_a_work_that_has_a_photo_can_be_opened_for_editing(admin_client: Client) -> None:
    """The change page used to answer 500 for every work with a photo.

    Originals live in a storage that refuses to build URLs, on purpose, and the
    stock file widget links to the current file. The existing "pages open" test
    misses it because its work has no photo at all, which is exactly the case
    that works.
    """
    work = WorkFactory.create(title_uk="Букет із троянд")
    WorkImageFactory.create(work=work)

    response = admin_client.get(f"/admin/catalog/work/{work.pk}/change/")

    assert response.status_code == 200


def test_saving_a_work_again_keeps_its_photo() -> None:
    """Validators run on the stored FieldFile when nothing new is uploaded.

    That file is closed, so reading it raised and the owner could not save an
    edit. It passed the same check on the day it arrived.
    """
    image = WorkImageFactory.create()

    image.full_clean()

    image.refresh_from_db()
    assert image.image.name

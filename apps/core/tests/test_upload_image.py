"""Section 9 (/admin/upload-image/) and 14.2: pictures inside a text."""

from typing import Any

import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from PIL import Image

from apps.catalog.models import WorkImageRendition
from tests.factories import photo_bytes

pytestmark = pytest.mark.django_db

UPLOAD_URL = "/admin/upload-image/"


def _picture(name: str = "photo.jpg", width: int = 3000, height: int = 2000) -> SimpleUploadedFile:
    return SimpleUploadedFile(
        name, photo_bytes(width=width, height=height), content_type="image/jpeg"
    )


def test_an_anonymous_upload_is_refused(client: Client) -> None:
    response = client.post(UPLOAD_URL, {"file": _picture()})

    assert response.status_code == 403


def test_a_signed_in_visitor_without_staff_rights_is_refused(client: Client) -> None:
    User.objects.create_user("visitor", password="not-a-secret-either")
    client.login(username="visitor", password="not-a-secret-either")

    response = client.post(UPLOAD_URL, {"file": _picture()})

    assert response.status_code == 403


def test_a_get_is_not_an_upload(admin_client: Client) -> None:
    assert admin_client.get(UPLOAD_URL).status_code == 405


def test_staff_upload_is_converted_to_webp_and_shrunk(admin_client: Client) -> None:
    response = admin_client.post(UPLOAD_URL, {"file": _picture()})
    location = response.json()["location"]

    assert response.status_code == 200
    assert location.endswith(".webp")
    assert location.startswith("/media/content/")

    from config.storages import public_storage

    stored = public_storage().open(location.replace("/media/", ""))
    with Image.open(stored) as image:
        assert image.format == "WEBP"
        assert max(image.size) == 1600


def test_an_uploaded_picture_gets_no_renditions(admin_client: Client) -> None:
    admin_client.post(UPLOAD_URL, {"file": _picture()})

    assert WorkImageRendition.objects.count() == 0


def test_a_file_that_is_not_an_image_is_refused(admin_client: Client) -> None:
    response = admin_client.post(
        UPLOAD_URL, {"file": SimpleUploadedFile("note.txt", b"not an image")}
    )

    assert response.status_code == 400
    assert "error" in response.json()


def test_an_upload_without_a_file_is_refused(admin_client: Client) -> None:
    assert admin_client.post(UPLOAD_URL, {}).status_code == 400


def test_the_editor_knows_where_to_send_pictures(admin_client: Client, settings: Any) -> None:
    from apps.core.models import StaticPage

    page = StaticPage.objects.create(slug="pro-nas", title_uk="Про нас")

    body = admin_client.get(f"/admin/core/staticpage/{page.pk}/change/").content.decode()

    assert "uploadEditorImage" in body
    assert "js/tinymce-upload.js" in body

"""Section 6 of tech.md: originals live in a storage that has no URL at all."""

from pathlib import Path

import pytest
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from config.storages import private_storage, public_storage
from tests.factories import OccasionFactory, WorkImageFactory, photo_bytes

# The 404 page is a real page now: it reads the site settings like every other.
pytestmark = pytest.mark.django_db


def test_private_storage_file_is_not_reachable_over_http(client: Client) -> None:
    name = private_storage().save("original.txt", ContentFile(b"gps metadata inside"))

    assert private_storage().exists(name)
    for url in (f"/media/{name}", f"/media/private/{name}", f"/{name}"):
        assert client.get(url).status_code == 404


def test_private_storage_has_no_public_url() -> None:
    name = private_storage().save("original.txt", ContentFile(b"gps metadata inside"))

    with pytest.raises(ValueError):
        private_storage().url(name)


def test_public_and_private_storages_are_separate() -> None:
    public_name = public_storage().save("cover.txt", ContentFile(b"public"))

    assert public_storage().url(public_name).startswith("/media/")
    assert not private_storage().exists(public_name)


def test_uploads_stay_out_of_the_developers_media_directory(tmp_path: Path) -> None:
    """A field carrying an explicit storage resolved it at import time, so it
    used to write into media/ no matter what the test settings said."""
    occasion = OccasionFactory(cover=SimpleUploadedFile("t.jpg", photo_bytes(), "image/jpeg"))
    work_image = WorkImageFactory()

    for stored in (occasion.cover, work_image.image):
        assert Path(stored.path).is_relative_to(tmp_path)

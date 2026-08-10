"""Section 6 of tech.md: originals live in a storage that has no URL at all."""

from pathlib import Path
from typing import Any

import pytest
from django.core.files.base import ContentFile
from django.test import Client

from config.storages import private_storage, public_storage


@pytest.fixture
def isolated_media(settings: Any, tmp_path: Path) -> None:
    settings.MEDIA_ROOT = tmp_path / "public"
    settings.STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
            "OPTIONS": {"location": tmp_path / "public", "base_url": "/media/"},
        },
        "private": {
            "BACKEND": "config.storages.PrivateFileSystemStorage",
            "OPTIONS": {"location": tmp_path / "private"},
        },
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }


def test_private_storage_file_is_not_reachable_over_http(
    client: Client, isolated_media: None
) -> None:
    name = private_storage().save("original.txt", ContentFile(b"gps metadata inside"))

    assert private_storage().exists(name)
    for url in (f"/media/{name}", f"/media/private/{name}", f"/{name}"):
        assert client.get(url).status_code == 404


def test_private_storage_has_no_public_url(isolated_media: None) -> None:
    name = private_storage().save("original.txt", ContentFile(b"gps metadata inside"))

    with pytest.raises(ValueError):
        private_storage().url(name)


def test_public_and_private_storages_are_separate(isolated_media: None) -> None:
    public_name = public_storage().save("cover.txt", ContentFile(b"public"))

    assert public_storage().url(public_name).startswith("/media/")
    assert not private_storage().exists(public_name)

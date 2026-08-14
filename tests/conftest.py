from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from django.apps import apps
from django.core.cache import cache
from django.core.files.storage import DefaultStorage, FileSystemStorage
from django.db.models import FileField

from config.storages import PrivateFileSystemStorage


@pytest.fixture(autouse=True)
def isolated_media(settings: Any, tmp_path: Path) -> Iterator[None]:
    """Every test writes its uploads into its own directory, never into media/."""
    settings.MEDIA_ROOT = tmp_path / "public"
    settings.MEDIA_PRIVATE_ROOT = tmp_path / "private"
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

    # A field declared with `storage=public_storage` called that callable once,
    # at import, and kept the answer. Rewriting STORAGES above moves the default
    # storage and nothing else, so those fields would keep filling the developer's
    # media/ volume with test uploads. Point them at the same temporary directory
    # for the length of the test and hand them back afterwards.
    public = FileSystemStorage(location=tmp_path / "public", base_url="/media/")
    private = PrivateFileSystemStorage(location=tmp_path / "private")
    swapped: list[tuple[Any, Any]] = []
    for model in apps.get_models():
        for field in model._meta.get_fields():
            if not isinstance(field, FileField) or isinstance(field.storage, DefaultStorage):
                continue
            swapped.append((field, field.storage))
            field.storage = (
                private if isinstance(field.storage, PrivateFileSystemStorage) else public
            )

    yield

    for field, original in swapped:
        field.storage = original


@pytest.fixture(autouse=True)
def isolated_cache(settings: Any) -> Iterator[None]:
    """Tests run against an in-process cache: no shared state between them."""
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "tests",
        }
    }
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def broken_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulate an unreachable Redis for every cache operation."""

    def explode(*args: Any, **kwargs: Any) -> Any:
        raise ConnectionError("redis is down")

    for method in ("get", "set", "delete"):
        monkeypatch.setattr(f"django.core.cache.cache.{method}", explode, raising=False)

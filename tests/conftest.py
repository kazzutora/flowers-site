from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def isolated_media(settings: Any, tmp_path: Path) -> None:
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

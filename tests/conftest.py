from collections.abc import Iterator
from typing import Any

import pytest
from django.core.cache import cache


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

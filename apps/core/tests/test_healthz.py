"""Section 9: the endpoint the load balancer watches."""

from typing import Any

import pytest
from django.test import Client

pytestmark = pytest.mark.django_db


def test_it_answers_200_while_the_dependencies_answer(client: Client) -> None:
    response = client.get("/healthz/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok", "cache": "ok"}


def test_it_answers_503_when_the_database_is_gone(
    client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    class DeadCursor:
        def __enter__(self) -> Any:
            raise ConnectionError("the database went away")

        def __exit__(self, *args: Any) -> None:
            return None

    monkeypatch.setattr("django.db.connection.cursor", lambda: DeadCursor())

    response = client.get("/healthz/")

    assert response.status_code == 503
    assert response.json()["status"] == "error"
    assert response.json()["database"].startswith("error")


def test_it_answers_503_when_the_cache_is_gone(
    client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    def explode(*args: Any, **kwargs: Any) -> Any:
        raise ConnectionError("redis is down")

    monkeypatch.setattr("django.core.cache.cache.set", explode, raising=False)

    response = client.get("/healthz/")

    assert response.status_code == 503
    assert response.json()["cache"].startswith("error")


def test_it_takes_no_language_prefix(client: Client) -> None:
    """It is watched by a machine, not read by a person."""
    assert client.get("/ru/healthz/").status_code == 404


def test_it_stays_out_of_the_sitemap(client: Client) -> None:
    from tests.factories import SiteSettingsFactory

    SiteSettingsFactory.create()

    assert "healthz" not in client.get("/sitemap.xml").content.decode()

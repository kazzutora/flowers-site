"""Section 14.4: the gallery cache and the query budget of section 19."""

from typing import Any

import pytest
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext

from apps.catalog import cache
from apps.catalog.models import Occasion, Tag, Work
from apps.core.models import SiteSettings
from tests.factories import (
    OccasionFactory,
    SiteSettingsFactory,
    TagFactory,
    TagGroupFactory,
    WorkFactory,
    WorkImageFactory,
)

pytestmark = pytest.mark.django_db

FRAGMENT_URL = "/hx/gallery/"


@pytest.fixture
def catalog() -> dict[str, Any]:
    SiteSettingsFactory.create()
    occasion = OccasionFactory.create(slug="vesillya")
    group = TagGroupFactory.create(slug="type")
    tag = TagFactory.create(group=group, slug="buket")
    work = WorkFactory.create(title_uk="Білий букет", occasions=[occasion], tags=[tag])
    return {"occasion": occasion, "tag": tag, "work": work}


# --- the version key ----------------------------------------------------------


def test_saving_a_work_bumps_the_version(catalog: dict[str, Any]) -> None:
    before = cache.version()

    WorkFactory.create(title_uk="Ще одна")

    assert cache.version() > before


@pytest.mark.parametrize("model", ["work", "image", "tag", "occasion"])
def test_every_model_of_section_14_4_bumps_the_version(catalog: dict[str, Any], model: str) -> None:
    before = cache.version()

    if model == "work":
        WorkFactory.create()
    elif model == "image":
        WorkImageFactory.create(work=catalog["work"])
    elif model == "tag":
        TagFactory.create(group=catalog["tag"].group, slug="koshyk")
    else:
        OccasionFactory.create(slug="yuvilei")

    assert cache.version() > before, model


def test_deleting_bumps_the_version_too(catalog: dict[str, Any]) -> None:
    work = WorkFactory.create()
    before = cache.version()

    work.delete()

    assert cache.version() > before


def test_the_key_changes_with_the_version(catalog: dict[str, Any]) -> None:
    first = cache.fragment_key("vesillya", "?type=buket", 1)
    WorkFactory.create()
    second = cache.fragment_key("vesillya", "?type=buket", 1)

    assert first != second


def test_the_key_separates_occasion_query_page_and_language(catalog: dict[str, Any]) -> None:
    from django.utils import translation

    base = cache.fragment_key("vesillya", "?type=buket", 1)

    assert base != cache.fragment_key("yuvilei", "?type=buket", 1)
    assert base != cache.fragment_key("vesillya", "?type=koshyk", 1)
    assert base != cache.fragment_key("vesillya", "?type=buket", 2)
    with translation.override("ru"):
        assert base != cache.fragment_key("vesillya", "?type=buket", 1)


# --- serving from the cache ---------------------------------------------------


def _count(client: Client, url: str) -> int:
    with CaptureQueriesContext(connection) as captured:
        client.get(url)
    return len(captured.captured_queries)


def test_a_repeated_fragment_is_served_from_the_cache(
    client: Client, catalog: dict[str, Any]
) -> None:
    """The key is built from the normalised query (section 14.4), so the groups
    and the occasion are read before the lookup. What the hit saves is the
    grid: the works, their photos and every rendition of those photos."""
    SiteSettings.load()
    url = f"{FRAGMENT_URL}?occasion=vesillya&type=buket"

    with CaptureQueriesContext(connection) as first_pass:
        first = client.get(url)
    with CaptureQueriesContext(connection) as second_pass:
        second = client.get(url)

    assert first.content == second.content
    assert second.headers["HX-Push-Url"] == "/galereya/vesillya/?type=buket"
    assert len(second_pass.captured_queries) < len(first_pass.captured_queries)
    assert len(second_pass.captured_queries) <= 3


def test_a_cache_hit_does_not_grow_with_the_catalogue(
    client: Client, catalog: dict[str, Any]
) -> None:
    SiteSettings.load()
    client.get(FRAGMENT_URL)
    small = _count(client, FRAGMENT_URL)

    for index in range(30):
        WorkFactory.create(title_uk=f"Робота {index}")
    client.get(FRAGMENT_URL)  # the version moved, so this one fills the cache again

    assert _count(client, FRAGMENT_URL) == small


def test_saving_a_work_makes_the_cached_fragment_unreachable(
    client: Client, catalog: dict[str, Any]
) -> None:
    client.get(FRAGMENT_URL)

    WorkFactory.create(title_uk="Свіжа робота")
    body = client.get(FRAGMENT_URL).content.decode()

    assert "Свіжа робота" in body


def test_an_admin_preview_is_never_served_from_the_cache(
    client: Client, admin_client: Client, catalog: dict[str, Any]
) -> None:
    client.get(FRAGMENT_URL)

    with CaptureQueriesContext(connection) as captured:
        admin_client.get(FRAGMENT_URL)

    assert len(captured.captured_queries) > 0


def test_an_unreachable_cache_still_renders(
    client: Client, catalog: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    def explode(*args: Any, **kwargs: Any) -> Any:
        raise ConnectionError("redis is down")

    for method in ("get", "set", "incr"):
        monkeypatch.setattr(f"django.core.cache.cache.{method}", explode, raising=False)

    response = client.get(FRAGMENT_URL)

    assert response.status_code == 200
    assert "Білий букет" in response.content.decode()


def test_an_unreachable_cache_does_not_break_a_save(
    catalog: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    def explode(*args: Any, **kwargs: Any) -> Any:
        raise ConnectionError("redis is down")

    for method in ("get", "set", "incr"):
        monkeypatch.setattr(f"django.core.cache.cache.{method}", explode, raising=False)

    assert WorkFactory.create(title_uk="Попри все").pk is not None


# --- the query budget ---------------------------------------------------------


def test_no_public_page_goes_past_fifteen_queries(client: Client, catalog: dict[str, Any]) -> None:
    """Section 14.4. Measured on a filled catalogue, not on an empty one."""
    from apps.blog.models import Post
    from tests.factories import ReviewFactory, StaticPageFactory

    for index in range(30):
        WorkFactory.create(title_uk=f"Робота {index}", occasions=[catalog["occasion"]])
    WorkImageFactory.create(work=catalog["work"])
    for index in range(5):
        ReviewFactory.create(author_name=f"Автор {index}", is_featured=True)
        Post.objects.create(
            slug=f"post-{index}", title_uk=f"Пост {index}", status=Post.Status.PUBLISHED
        )
    StaticPageFactory.create(slug="pro-nas")
    SiteSettings.load()

    pages = {
        "/": None,
        "/galereya/": None,
        "/galereya/vesillya/": None,
        "/galereya/?type=buket": None,
        catalog["work"].get_absolute_url(): None,
        "/poshuk/?q=букет": None,
        "/obrane/?a=100,101": None,
        "/kontakty/": None,
        "/vidhuky/": None,
        "/blog/": None,
        "/blog/post-1/": None,
        "/pro-nas/": None,
        "/dyakuyemo/": None,
    }
    for url in pages:
        assert _count(client, url) <= 15, url


def test_the_gallery_costs_the_same_on_a_bigger_catalogue(
    client: Client, catalog: dict[str, Any]
) -> None:
    SiteSettings.load()
    small = _count(client, "/galereya/")

    for index in range(30):
        WorkFactory.create(title_uk=f"Робота {index}")

    assert _count(client, "/galereya/") == small


def test_the_seeded_site_stays_inside_the_budget(client: Client) -> None:
    """The real fixture set, not a handful of rows."""
    from scripts.seed import run

    run()
    SiteSettings.load()

    assert Work.published.count() == 30
    assert Occasion.objects.count() == 7
    assert Tag.objects.count() == 20

    for url in ("/", "/galereya/", "/galereya/vesillya/", "/vidhuky/", "/blog/"):
        assert _count(client, url) <= 15, url

"""Sections 9 and 16: what a crawler is told."""

from typing import Any
from xml.etree import ElementTree

import pytest
from django.test import Client

from apps.blog.models import Post
from apps.catalog.models import Work
from tests.factories import (
    OccasionFactory,
    SiteSettingsFactory,
    StaticPageFactory,
    WorkFactory,
)

pytestmark = pytest.mark.django_db

NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9", "x": "http://www.w3.org/1999/xhtml"}


@pytest.fixture(autouse=True)
def site() -> Any:
    return SiteSettingsFactory.create()


def _locations(client: Client) -> list[str]:
    """Every address in the sitemap, walking the index into its sections."""
    index = ElementTree.fromstring(client.get("/sitemap.xml").content)
    found: list[str] = []
    for node in index.findall("s:sitemap/s:loc", NS):
        section = node.text or ""
        body = client.get(section[section.index("/sitemap-") :]).content
        found.extend(
            item.text or "" for item in ElementTree.fromstring(body).findall("s:url/s:loc", NS)
        )
    return found


# --- robots.txt ---------------------------------------------------------------


def test_robots_closes_only_the_fragments_and_the_admin(client: Client) -> None:
    body = client.get("/robots.txt").content.decode()

    assert "Disallow: /hx/" in body
    assert "Disallow: /admin/" in body
    assert "Disallow: /ru/hx/" in body
    assert "Disallow: /ru/admin/" in body


def test_robots_leaves_the_noindex_pages_crawlable(client: Client) -> None:
    """They are closed by a meta tag, which a blocked crawler could never read."""
    body = client.get("/robots.txt").content.decode()

    for path in ("/obrane/", "/poshuk/", "/dyakuyemo/", "/galereya/", "/blog/"):
        assert f"Disallow: {path}" not in body


def test_robots_points_at_the_sitemap(client: Client) -> None:
    body = client.get("/robots.txt").content.decode()

    assert "Sitemap: http://localhost:8000/sitemap.xml" in body


def test_robots_is_plain_text(client: Client) -> None:
    response = client.get("/robots.txt")

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/plain")


# --- the noindex pages --------------------------------------------------------


@pytest.mark.parametrize("path", ["/obrane/", "/poshuk/", "/dyakuyemo/"])
def test_the_private_pages_carry_the_meta_tag(client: Client, path: str) -> None:
    body = client.get(path).content.decode()

    assert '<meta name="robots" content="noindex, follow">' in body


# --- sitemap ------------------------------------------------------------------


def test_the_sitemap_lists_the_public_pages(client: Client) -> None:
    OccasionFactory.create(slug="vesillya")
    StaticPageFactory.create(slug="pro-nas")
    work = WorkFactory.create()
    Post.objects.create(slug="yak-obraty", title_uk="Як обрати", status=Post.Status.PUBLISHED)

    found = _locations(client)

    assert any(url.endswith("/galereya/") for url in found)
    assert any(url.endswith("/galereya/vesillya/") for url in found)
    assert any(url.endswith("/pro-nas/") for url in found)
    assert any(url.endswith(work.get_absolute_url()) for url in found)
    assert any(url.endswith("/blog/yak-obraty/") for url in found)
    assert any(url.endswith("/kontakty/") for url in found)


def test_the_sitemap_carries_both_languages(client: Client) -> None:
    found = _locations(client)

    assert any(url.endswith("/galereya/") for url in found)
    assert any(url.endswith("/ru/galereya/") for url in found)


def test_the_sitemap_holds_no_drafts_and_no_archive(client: Client) -> None:
    draft = WorkFactory.create(title_uk="Чернетка", status=Work.Status.DRAFT)
    archived = WorkFactory.create(title_uk="Архів", status=Work.Status.ARCHIVED)
    Post.objects.create(slug="chernetka", title_uk="Чернетка", status=Post.Status.DRAFT)
    OccasionFactory.create(slug="prykhovanyi", is_active=False)
    StaticPageFactory.create(slug="nepublichna", is_published=False)

    found = _locations(client)

    assert not any(url.endswith(draft.get_absolute_url()) for url in found)
    assert not any(url.endswith(archived.get_absolute_url()) for url in found)
    assert not any("chernetka" in url for url in found)
    assert not any("prykhovanyi" in url for url in found)
    assert not any("nepublichna" in url for url in found)


def test_the_sitemap_keeps_the_noindex_pages_out(client: Client) -> None:
    found = _locations(client)

    for path in ("/obrane/", "/poshuk/", "/dyakuyemo/"):
        assert not any(url.endswith(path) for url in found)


def test_the_sitemap_carries_hreflang_alternates(client: Client) -> None:
    OccasionFactory.create(slug="vesillya")

    index = ElementTree.fromstring(client.get("/sitemap.xml").content)
    section = index.find("s:sitemap/s:loc", NS).text or ""  # type: ignore[union-attr]
    body = client.get(section[section.index("/sitemap-") :]).content

    alternates = ElementTree.fromstring(body).findall("s:url/x:link", NS)
    assert alternates, "each address should name its other language"
    assert {node.get("hreflang") for node in alternates} >= {"uk", "ru"}


# --- link previews ------------------------------------------------------------


def test_every_public_page_carries_og_and_twitter_tags(client: Client) -> None:
    work = WorkFactory.create()
    for path in ("/", "/galereya/", work.get_absolute_url(), "/kontakty/"):
        body = client.get(path).content.decode()

        assert '<meta property="og:type"' in body, path
        assert '<meta property="og:title"' in body, path
        assert '<meta property="og:url"' in body, path
        assert '<meta name="twitter:card" content="summary_large_image">' in body, path


def test_every_public_page_names_both_languages(client: Client) -> None:
    for path in ("/", "/galereya/", "/kontakty/", "/blog/"):
        body = client.get(path).content.decode()

        assert '<link rel="alternate" hreflang="uk"' in body, path
        assert '<link rel="alternate" hreflang="ru"' in body, path
        assert '<link rel="alternate" hreflang="x-default"' in body, path

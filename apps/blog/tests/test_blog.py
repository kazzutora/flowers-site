"""Sections 4.11, 8.3, 9 and 16: the blog."""

from typing import Any

import pytest
from django.test import Client
from django.utils import translation

from apps.blog.models import Post
from apps.blog.views import PAGE_SIZE
from apps.catalog.services import views_counter
from apps.catalog.tasks import flush_view_counters
from tests.factories import SiteSettingsFactory, WorkFactory

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def site() -> Any:
    return SiteSettingsFactory.create()


@pytest.fixture
def post() -> Post:
    return Post.objects.create(
        slug="yak-obraty-buket",
        title_uk="Як обрати букет",
        title_ru="Как выбрать букет",
        excerpt_uk="Коротка інструкція",
        body_uk="<p>Почніть із приводу</p>",
        status=Post.Status.PUBLISHED,
    )


@pytest.fixture
def counters() -> Any:
    try:
        client = views_counter.get_client()
        client.ping()
    except Exception:  # pragma: no cover - only on a machine without Redis
        pytest.skip("redis is not reachable")

    def clear() -> None:
        for pattern in views_counter.PATTERNS.values():
            for key in client.scan_iter(match=pattern, count=500):
                client.delete(key)

    clear()
    yield client
    clear()


# --- the pages ----------------------------------------------------------------


def test_the_list_opens(client: Client, post: Post) -> None:
    response = client.get("/blog/")

    assert response.status_code == 200
    assert "Як обрати букет" in response.content.decode()


def test_a_post_opens(client: Client, post: Post) -> None:
    response = client.get(post.get_absolute_url())

    assert response.status_code == 200
    assert "Почніть із приводу" in response.content.decode()


def test_a_post_opens_in_russian_and_falls_back(client: Client, post: Post) -> None:
    body = client.get("/ru/blog/yak-obraty-buket/").content.decode()

    assert "Как выбрать букет" in body
    # The Russian body is empty, so the Ukrainian one is shown instead.
    assert "Почніть із приводу" in body


def test_a_draft_is_a_404(client: Client, post: Post) -> None:
    post.status = Post.Status.DRAFT
    post.save()

    assert client.get(post.get_absolute_url()).status_code == 404


def test_an_unknown_slug_is_a_404(client: Client, post: Post) -> None:
    assert client.get("/blog/nemaye-takogo/").status_code == 404


def test_a_draft_stays_out_of_the_list(client: Client) -> None:
    Post.objects.create(slug="chernetka", title_uk="Чернетка", status=Post.Status.DRAFT)

    assert "Чернетка" not in client.get("/blog/").content.decode()


def test_the_list_is_paginated(client: Client) -> None:
    for index in range(PAGE_SIZE + 2):
        Post.objects.create(
            slug=f"post-{index}", title_uk=f"Пост {index}", status=Post.Status.PUBLISHED
        )

    first = client.get("/blog/")
    second = client.get("/blog/?page=2")

    assert len(first.context["posts"]) == PAGE_SIZE
    assert len(second.context["posts"]) == 2


def test_an_empty_blog_says_so(client: Client) -> None:
    assert client.get("/blog/").status_code == 200


# --- related works ------------------------------------------------------------


def test_related_works_are_clickable(client: Client, post: Post) -> None:
    work = WorkFactory.create(title_uk="Букет із троянд")
    post.related_works.set([work])

    body = client.get(post.get_absolute_url()).content.decode()

    assert f'href="{work.get_absolute_url()}"' in body
    assert "Букет із троянд" in body


# --- content ------------------------------------------------------------------


def test_the_body_is_sanitised_on_the_way_in(client: Client) -> None:
    post = Post.objects.create(
        slug="nebezpechnyi",
        title_uk="Небезпечний",
        body_uk="<p>ok</p><script>alert(1)</script>",
        status=Post.Status.PUBLISHED,
    )
    post.refresh_from_db()

    body = client.get(post.get_absolute_url()).content.decode()

    assert "<script" not in post.body_uk
    # The page carries its own script tags; what must not survive is the payload.
    assert "alert(1)" not in body
    assert "<p>ok</p>" in body


def test_a_cover_is_squeezed_once_and_gets_no_renditions() -> None:
    from django.core.files.uploadedfile import SimpleUploadedFile
    from PIL import Image

    from apps.catalog.models import WorkImageRendition
    from tests.factories import photo_bytes

    post = Post.objects.create(
        slug="z-obkladynkoyu",
        title_uk="З обкладинкою",
        cover=SimpleUploadedFile("cover.jpg", photo_bytes(3000, 2000), "image/jpeg"),
    )

    assert str(post.cover.name).endswith(".webp")
    with Image.open(post.cover) as stored:
        assert stored.format == "WEBP"
        assert max(stored.size) == 1600
    assert WorkImageRendition.objects.count() == 0


def test_publishing_stamps_published_at_once(post: Post) -> None:
    stamped = post.published_at

    post.title_uk = "Інша назва"
    post.save()

    assert post.published_at == stamped


# --- structured data ----------------------------------------------------------


def test_the_post_carries_article_markup(client: Client, post: Post) -> None:
    body = client.get(post.get_absolute_url()).content.decode()

    assert '"@type": "Article"' in body
    assert '"headline": "Як обрати букет"' in body
    assert "http://localhost:8000/blog/yak-obraty-buket/" in body


def test_the_home_page_shows_the_latest_posts(client: Client, post: Post) -> None:
    body = client.get("/").content.decode()

    assert "Як обрати букет" in body
    assert "Всі статті" in body


# --- view counters ------------------------------------------------------------


def test_a_visit_is_counted_in_redis(client: Client, post: Post, counters: Any) -> None:
    client.get(post.get_absolute_url())
    post.refresh_from_db()

    assert post.views_count == 0
    assert int(counters.get(f"views:post:{post.pk}")) == 1


def test_flushing_handles_works_and_posts_together(
    client: Client, post: Post, counters: Any
) -> None:
    from apps.catalog.models import Work

    work = WorkFactory.create()
    client.get(work.get_absolute_url())
    client.get(post.get_absolute_url())
    client.get(post.get_absolute_url())

    assert flush_view_counters(payload={}) == 2

    post.refresh_from_db()
    assert post.views_count == 2
    assert Work.objects.get(pk=work.pk).views_count == 1

    # Idempotent: the counters were taken with GETDEL, so nothing is left.
    assert flush_view_counters(payload={}) == 0
    post.refresh_from_db()
    assert post.views_count == 2


def test_an_unreachable_redis_does_not_take_the_post_down(
    client: Client, post: Post, monkeypatch: pytest.MonkeyPatch
) -> None:
    def explode() -> Any:
        raise ConnectionError("redis is down")

    monkeypatch.setattr(views_counter, "get_client", explode)

    assert client.get(post.get_absolute_url()).status_code == 200


# --- query budget -------------------------------------------------------------


def test_the_list_costs_a_fixed_number_of_queries(
    client: Client, django_assert_num_queries: Any
) -> None:
    from apps.core.models import SiteSettings

    for index in range(PAGE_SIZE):
        Post.objects.create(
            slug=f"post-{index}", title_uk=f"Пост {index}", status=Post.Status.PUBLISHED
        )
    SiteSettings.load()

    # The count and the page itself.
    with django_assert_num_queries(2):
        client.get("/blog/")


def test_the_language_switch_keeps_the_post(client: Client, post: Post) -> None:
    with translation.override("uk"):
        body = client.get(post.get_absolute_url()).content.decode()

    assert 'href="/ru/blog/yak-obraty-buket/"' in body

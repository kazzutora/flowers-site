"""Sections 8.3, 9, 10 and 16: the page a visitor calls from."""

from decimal import Decimal
from typing import Any

import pytest
from django.test import Client

from apps.catalog.models import Work
from apps.catalog.services import views_counter
from apps.catalog.services.similar import similar_works
from apps.catalog.tasks import flush_view_counters, generate_renditions
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


@pytest.fixture
def work() -> Work:
    SiteSettingsFactory.create()
    group = TagGroupFactory.create(slug="type", name_uk="Тип")
    tag = TagFactory.create(group=group, slug="buket", name_uk="Букет")
    occasion = OccasionFactory.create(slug="vesillya", name_uk="Весілля")
    item = WorkFactory.create(
        title_uk="Букет із троянд", occasions=[occasion], tags=[tag], status=Work.Status.PUBLISHED
    )
    WorkImageFactory.create(work=item)
    return item


@pytest.fixture
def counters() -> Any:
    """A live Redis, cleaned before and after. CI runs one; a laptop may not."""
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


# --- response codes -----------------------------------------------------------


def test_a_published_work_opens(client: Client, work: Work) -> None:
    response = client.get(work.get_absolute_url())

    assert response.status_code == 200
    assert "Букет із троянд" in response.content.decode()


def test_a_draft_is_a_404(client: Client, work: Work) -> None:
    work.status = Work.Status.DRAFT
    work.save()

    assert client.get(work.get_absolute_url()).status_code == 404


def test_an_archived_work_answers_410_with_its_own_template(client: Client, work: Work) -> None:
    work.status = Work.Status.ARCHIVED
    work.save()

    response = client.get(work.get_absolute_url())

    assert response.status_code == 410
    assert "410.html" in [template.name for template in response.templates]


def test_an_unknown_slug_is_a_404(client: Client, work: Work) -> None:
    assert client.get("/robota/999-nemaye/").status_code == 404


# --- the page itself ----------------------------------------------------------


def test_the_article_is_shown_with_the_sign_and_copied_without_it(
    client: Client, work: Work
) -> None:
    body = client.get(work.get_absolute_url()).content.decode()

    assert f"&#8470;{work.article}" in body
    assert f"copyNumber('{work.article}')" in body


def test_tags_link_back_into_the_gallery(client: Client, work: Work) -> None:
    body = client.get(work.get_absolute_url()).content.decode()

    assert 'href="/galereya/?type=buket"' in body


def test_the_seasonality_notice_is_there(client: Client, work: Work) -> None:
    body = client.get(work.get_absolute_url()).content.decode()

    assert "season" in body.lower() or "сезон" in body.lower()


def test_the_cost_never_reaches_the_page(client: Client, work: Work) -> None:
    work.cost = Decimal("777.00")
    work.price_from = Decimal("950.00")
    work.price_visible = True
    work.save()

    for prices_enabled in (False, True):
        settings = SiteSettings.load()
        settings.prices_enabled = prices_enabled
        settings.save()

        body = client.get(work.get_absolute_url()).content.decode()
        assert "777" not in body


def test_the_price_appears_only_when_both_switches_are_on(client: Client, work: Work) -> None:
    work.price_from = Decimal("950.00")
    work.price_visible = True
    work.save()
    settings = SiteSettings.load()

    settings.prices_enabled = False
    settings.save()
    assert "950" not in client.get(work.get_absolute_url()).content.decode()

    settings.prices_enabled = True
    settings.save()
    assert "950" in client.get(work.get_absolute_url()).content.decode()


# --- link previews and structured data ----------------------------------------


def test_the_link_preview_is_absolute_and_carries_the_article(client: Client, work: Work) -> None:
    generate_renditions(payload={"work_image_id": work.images.get().pk})

    body = client.get(work.get_absolute_url()).content.decode()

    assert f'<meta property="og:title" content="№{work.article}' in body
    assert 'property="og:image" content="http://localhost:8000/media/' in body
    assert 'content="1200"' in body


def test_structured_data_has_no_product_while_prices_are_off(client: Client, work: Work) -> None:
    generate_renditions(payload={"work_image_id": work.images.get().pk})

    body = client.get(work.get_absolute_url()).content.decode()

    assert '"@type": "ImageObject"' in body
    assert "BreadcrumbList" in body
    assert "Product" not in body


# --- similar works ------------------------------------------------------------


def test_similar_works_prefer_the_occasion_then_the_tags(work: Work) -> None:
    occasion = work.occasions.first()
    tag = work.tags.first()
    by_occasion = WorkFactory.create(title_uk="Той самий привід", occasions=[occasion])
    by_tag = WorkFactory.create(title_uk="Той самий тег", tags=[tag])
    WorkFactory.create(title_uk="Нічого спільного")

    found = list(similar_works(work))

    assert found[0] == by_occasion
    assert by_tag in found
    assert work not in found
    assert len(found) == 2


def test_similar_works_stop_at_eight(work: Work) -> None:
    tag = work.tags.first()
    for index in range(12):
        WorkFactory.create(title_uk=f"Схожа {index}", tags=[tag])

    assert len(list(similar_works(work))) == 8


# --- view counters ------------------------------------------------------------


def test_a_visit_is_counted_in_redis_and_not_in_the_database(
    client: Client, work: Work, counters: Any
) -> None:
    client.get(work.get_absolute_url())
    work.refresh_from_db()

    assert work.views_count == 0
    assert int(counters.get(f"views:work:{work.pk}")) == 1


def test_flushing_twice_does_not_double_the_counter(
    client: Client, work: Work, counters: Any
) -> None:
    client.get(work.get_absolute_url())
    client.get(work.get_absolute_url())

    assert flush_view_counters(payload={}) == 1
    work.refresh_from_db()
    assert work.views_count == 2

    assert flush_view_counters(payload={}) == 0
    work.refresh_from_db()
    assert work.views_count == 2


def test_flushing_refuses_an_unexpected_payload(counters: Any) -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        flush_view_counters(payload={"since": "yesterday"})


def test_an_unreachable_redis_does_not_take_the_page_down(
    client: Client, work: Work, monkeypatch: pytest.MonkeyPatch
) -> None:
    def explode() -> Any:
        raise ConnectionError("redis is down")

    monkeypatch.setattr(views_counter, "get_client", explode)

    assert client.get(work.get_absolute_url()).status_code == 200
    assert flush_view_counters(payload={}) == 0

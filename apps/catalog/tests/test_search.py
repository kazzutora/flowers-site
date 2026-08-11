"""Section 10, "search": the visitor read a number under a photo on Instagram."""

import pytest
from django.test import Client
from hypothesis import given
from hypothesis import strategies as st

from apps.catalog.filters import extract_article, parse_articles
from apps.catalog.models import Work
from tests.factories import SiteSettingsFactory, WorkFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def work() -> Work:
    SiteSettingsFactory.create()
    return WorkFactory.create(
        title_uk="Букет із троянд",
        title_ru="Букет из роз",
        composition_uk="троянди, евкаліпт",
        status=Work.Status.PUBLISHED,
    )


# --- pulling the number out ---------------------------------------------------


@pytest.mark.parametrize("raw", ["147", "№147", "# 147", "0147", "  147  ", "№ 147"])
def test_every_way_of_typing_a_number_gives_the_same_one(raw: str) -> None:
    assert extract_article(raw) == 147


@pytest.mark.parametrize("raw", ["", "букет", "147 троянди", "147 152", "-3", "0", "abc147"])
def test_anything_that_is_not_a_number_is_a_text_search(raw: str) -> None:
    assert extract_article(raw) is None


@given(st.integers(min_value=1, max_value=10**6), st.sampled_from(["", "#", "№", "# ", "№ "]))
def test_the_number_survives_any_prefix_and_any_padding(number: int, prefix: str) -> None:
    assert extract_article(f"  {prefix}{number:07d}  ") == number


@given(st.text(max_size=20))
def test_extracting_a_number_never_raises(raw: str) -> None:
    result = extract_article(raw)

    assert result is None or result > 0


# --- the favourites parameter -------------------------------------------------


@given(st.text(alphabet="0123456789,- abc", max_size=200))
def test_the_favourites_parameter_is_always_clean(raw: str) -> None:
    numbers = parse_articles(raw)

    assert len(numbers) <= 50
    assert len(numbers) == len(set(numbers))
    assert all(isinstance(number, int) and number > 0 for number in numbers)


def test_the_favourites_parameter_keeps_the_order_and_cuts_at_fifty() -> None:
    raw = ",".join(str(number) for number in range(1, 80))

    numbers = parse_articles(raw)

    assert numbers == list(range(1, 51))


# --- the page -----------------------------------------------------------------


@pytest.mark.parametrize("raw", ["147", "№147", "# 147", "0147"])
def test_a_known_number_redirects_to_the_work(client: Client, work: Work, raw: str) -> None:
    query = raw.replace("147", str(work.article))

    response = client.get("/poshuk/", {"q": query})

    assert response.status_code == 302
    assert response.headers["Location"] == work.get_absolute_url()


def test_an_unknown_number_shows_an_empty_state(client: Client, work: Work) -> None:
    response = client.get("/poshuk/", {"q": "999999"})

    assert response.status_code == 200
    assert response.context["found_count"] == 0


def test_a_text_query_searches_the_title_and_the_composition(client: Client, work: Work) -> None:
    assert client.get("/poshuk/", {"q": "троянд"}).context["found_count"] == 1
    assert client.get("/poshuk/", {"q": "роз"}).context["found_count"] == 1
    assert client.get("/poshuk/", {"q": "евкаліпт"}).context["found_count"] == 1


def test_a_work_matching_twice_is_listed_once(client: Client, work: Work) -> None:
    work.title_uk = "Троянди"
    work.composition_uk = "троянди, гіпсофіла"
    work.save()

    response = client.get("/poshuk/", {"q": "троянд"})

    assert [item.pk for item in response.context["works"]] == [work.pk]


def test_tags_do_not_take_part_in_the_text_search(client: Client, work: Work) -> None:
    from tests.factories import TagFactory, TagGroupFactory

    group = TagGroupFactory.create(slug="type")
    tag = TagFactory.create(group=group, slug="buket", name_uk="Кошик")
    work.tags.add(tag)

    assert client.get("/poshuk/", {"q": "Кошик"}).context["found_count"] == 0


def test_drafts_and_archives_are_not_findable(client: Client, work: Work) -> None:
    work.status = Work.Status.ARCHIVED
    work.save()

    assert client.get("/poshuk/", {"q": str(work.article)}).status_code == 200
    assert client.get("/poshuk/", {"q": "троянд"}).context["found_count"] == 0


def test_the_search_page_is_closed_to_crawlers(client: Client, work: Work) -> None:
    body = client.get("/poshuk/").content.decode()

    assert '<meta name="robots" content="noindex, follow">' in body


def test_the_mobile_menu_carries_the_search_box(client: Client, work: Work) -> None:
    body = client.get("/").content.decode()

    assert 'action="/poshuk/"' in body

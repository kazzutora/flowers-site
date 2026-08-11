"""Gallery query: parsing, normalisation and the queryset (section 9).

Parsing is pure and knows nothing about the database: it takes the request
parameters and a `FilterSpec` describing the groups. That keeps the contract
(silently dropped unknowns, stable canonical order) under property based tests.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from django.db.models import F, QuerySet

SORT_NEW = "new"
SORT_POPULAR = "popular"
SORTS: tuple[str, ...] = (SORT_NEW, SORT_POPULAR)
DEFAULT_SORT = SORT_NEW

# Two, three and four columns divide it evenly on phone, tablet and desktop.
PAGE_SIZE = 24

# Exact keys from section 9. The trailing `-id` is not decoration: without it
# equal view counts give Postgres a free hand and "show more" starts repeating
# and dropping cards.
ORDER_BY: dict[str, tuple[Any, ...]] = {
    SORT_NEW: ("-is_pinned", F("published_at").desc(nulls_last=True), "-id"),
    SORT_POPULAR: ("-is_pinned", "-views_count", "-id"),
}


@dataclass(frozen=True)
class GroupSpec:
    """One filter group: the query parameter name and the values it accepts."""

    slug: str
    tag_slugs: frozenset[str]


@dataclass(frozen=True)
class FilterSpec:
    """Every active group, already in `TagGroup.order`."""

    groups: tuple[GroupSpec, ...] = ()

    @classmethod
    def from_db(cls) -> "FilterSpec":
        from apps.catalog.models import Tag, TagGroup

        tags: dict[int, set[str]] = {}
        for group_id, slug in Tag.objects.filter(is_active=True).values_list("group_id", "slug"):
            tags.setdefault(group_id, set()).add(slug)

        return cls(
            groups=tuple(
                GroupSpec(slug=group.slug, tag_slugs=frozenset(tags.get(group.pk, set())))
                for group in TagGroup.objects.filter(is_active=True)
            )
        )


@dataclass(frozen=True)
class GalleryQuery:
    """A normalised query: groups in `TagGroup.order`, values alphabetical."""

    selected: tuple[tuple[str, tuple[str, ...]], ...] = ()
    sort: str = DEFAULT_SORT
    page: int = 1

    @property
    def pairs(self) -> tuple[tuple[str, str], ...]:
        """(group slug, tag slug) in canonical order."""
        return tuple((group, tag) for group, tags in self.selected for tag in tags)

    @property
    def tag_slugs(self) -> tuple[str, ...]:
        return tuple(tag for _group, tag in self.pairs)

    def to_params(self) -> list[tuple[str, str]]:
        """The canonical parameter list, `sort` and `page` included."""
        params = list(self.pairs)
        if self.sort != DEFAULT_SORT:
            params.append(("sort", self.sort))
        if self.page > 1:
            params.append(("page", str(self.page)))
        return params

    def query_string(self, *, page: int | None = None, with_sort: bool = True) -> str:
        """`?a=b&...`, or an empty string when there is nothing to carry."""
        params = list(self.pairs)
        if with_sort and self.sort != DEFAULT_SORT:
            params.append(("sort", self.sort))
        number = self.page if page is None else page
        if number > 1:
            params.append(("page", str(number)))
        return f"?{urlencode(params)}" if params else ""

    def without(self, group: str, tag: str) -> "GalleryQuery":
        """The same query minus one value. Removing a filter starts at page 1."""
        selected = tuple(
            (name, tuple(value for value in tags if not (name == group and value == tag)))
            for name, tags in self.selected
        )
        return GalleryQuery(
            selected=tuple((name, tags) for name, tags in selected if tags),
            sort=self.sort,
            page=1,
        )

    def with_sort(self, sort: str) -> "GalleryQuery":
        return GalleryQuery(selected=self.selected, sort=sort, page=1)

    def is_active(self, group: str, tag: str) -> bool:
        return (group, tag) in self.pairs


def _values(params: Mapping[str, Any], key: str) -> list[str]:
    """Read repeated values from a QueryDict or from a plain mapping."""
    getlist = getattr(params, "getlist", None)
    if callable(getlist):
        return [str(value) for value in getlist(key)]
    value = params.get(key)
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Sequence):
        return [str(item) for item in value]
    return [str(value)]


def parse_page(raw: str | None) -> int:
    try:
        number = int(str(raw))
    except (TypeError, ValueError):
        return 1
    return number if number >= 1 else 1


def _is_page(raw: str) -> bool:
    return raw.isdigit() and int(raw) >= 1


def parse(params: Mapping[str, Any], spec: FilterSpec) -> GalleryQuery:
    """Normalise the query. Unknown parameters and slugs are dropped silently."""
    selected: list[tuple[str, tuple[str, ...]]] = []
    for group in spec.groups:
        chosen = {value for value in _values(params, group.slug) if value in group.tag_slugs}
        if chosen:
            selected.append((group.slug, tuple(sorted(chosen))))

    # First usable value, not the last one: a repeated parameter must not make
    # the answer depend on the order the browser happened to send.
    sort = next((value for value in _values(params, "sort") if value in SORTS), DEFAULT_SORT)
    pages = [parse_page(value) for value in _values(params, "page") if _is_page(value)]

    return GalleryQuery(selected=tuple(selected), sort=sort, page=pages[0] if pages else 1)


def apply(query: GalleryQuery, occasion: Any = None) -> "QuerySet[Any]":
    """Published works matching the query: OR inside a group, AND between them."""
    from apps.catalog.models import Work

    works = Work.published.all()
    if occasion is not None:
        works = works.filter(occasions=occasion)
    for _group, tags in query.selected:
        works = works.filter(tags__slug__in=tags)
    # Every filter adds a join, so rows repeat without this.
    return works.order_by(*ORDER_BY[query.sort]).distinct()

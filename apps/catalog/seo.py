"""Indexing rules of the gallery (section 9 of tech.md).

The table is applied top down. The first matching row decides `index` versus
`noindex`; the canonical comes from the strongest row that matched, and the
strongest one is the row that collapses the most. So a popular sort with two
tags canonicalises to the plain section page rather than to another noindex
URL.
"""

from collections.abc import Sequence
from urllib.parse import urlencode

from django.urls import reverse

from apps.catalog.filters import SORT_POPULAR

INDEX = "index, follow"
NOINDEX = "noindex, follow"


def gallery_path(occasion: str | None) -> str:
    if occasion:
        return reverse("gallery_occasion", kwargs={"occasion_slug": occasion})
    return reverse("gallery")


def robots_directive(
    occasion: str | None,
    tags: Sequence[tuple[str, str]],
    sort: str,
    page: int,
) -> tuple[str, str]:
    """Return the robots directive and the canonical path.

    `tags` holds (group slug, tag slug) pairs already in canonical order.
    """
    pairs = list(tags)
    base = gallery_path(occasion)

    many_tags = len(pairs) >= 2
    popular = sort == SORT_POPULAR
    robots = NOINDEX if popular or many_tags else INDEX

    if many_tags:
        # A combination of filters is not a landing page: it points at the
        # section, without tags and without a page.
        return robots, base

    # The canonical never carries `sort`; it always carries the page.
    params: list[tuple[str, str]] = list(pairs)
    if page > 1:
        params.append(("page", str(page)))
    query = f"?{urlencode(params)}" if params else ""
    return robots, f"{base}{query}"

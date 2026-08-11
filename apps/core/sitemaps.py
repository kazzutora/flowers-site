"""Sitemap of section 16: both languages, no drafts, no archive.

Every class sets `i18n = True`, so each address appears once per language, and
`alternates = True`, so each entry carries the hreflang links Google reads.
"""

from datetime import datetime
from typing import Any

from django.contrib.sitemaps import Sitemap
from django.db.models import QuerySet
from django.urls import reverse

from apps.blog.models import Post
from apps.catalog.models import Occasion, Work
from apps.core.models import StaticPage


class BaseSitemap(Sitemap):
    i18n = True
    alternates = True
    protocol = "https"


class StaticViewSitemap(BaseSitemap):
    """The pages that are code, not rows.

    /obrane/, /poshuk/ and /dyakuyemo/ are missing on purpose: section 16 keeps
    them out of the index with a meta tag, and a page that is noindex has no
    business in a sitemap either.
    """

    changefreq = "weekly"
    priority = 0.8

    def items(self) -> list[str]:
        return ["home", "gallery", "contacts", "review_list", "post_list"]

    def location(self, item: str) -> str:
        return reverse(item)


class StaticPageSitemap(BaseSitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self) -> "QuerySet[StaticPage]":
        return StaticPage.objects.filter(is_published=True)

    def lastmod(self, item: StaticPage) -> datetime:
        return item.updated_at


class OccasionSitemap(BaseSitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self) -> "QuerySet[Occasion]":
        return Occasion.objects.filter(is_active=True)

    def lastmod(self, item: Occasion) -> datetime:
        return item.updated_at


class WorkSitemap(BaseSitemap):
    changefreq = "monthly"
    priority = 0.7
    limit = 2000

    def items(self) -> "QuerySet[Work]":
        # `published` already drops drafts, archives and anything scheduled.
        return Work.published.all()

    def lastmod(self, item: Work) -> datetime:
        return item.updated_at


class PostSitemap(BaseSitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self) -> "QuerySet[Post]":
        return Post.published.all()

    def lastmod(self, item: Post) -> datetime:
        return item.updated_at


SITEMAPS: dict[str, Any] = {
    "pages": StaticViewSitemap,
    "static": StaticPageSitemap,
    "occasions": OccasionSitemap,
    "works": WorkSitemap,
    "posts": PostSitemap,
}

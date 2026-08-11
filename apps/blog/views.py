"""The blog (sections 9, 10 and 16). No categories, no RSS in v1."""

from typing import Any
from urllib.parse import urljoin

from django.conf import settings
from django.core.paginator import Paginator
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.blog.models import Post
from apps.catalog.services import views_counter

PAGE_SIZE = 9


def post_list(request: HttpRequest) -> HttpResponse:
    posts = Post.published.all()
    page_obj = Paginator(posts, PAGE_SIZE).get_page(request.GET.get("page"))

    return render(
        request,
        "pages/post_list.html",
        {
            "page_obj": page_obj,
            "posts": page_obj.object_list,
            "base_url": f"{reverse('post_list')}?",
            "breadcrumbs": [
                {"label": _("Home"), "url": reverse("home")},
                {"label": _("Blog")},
            ],
        },
    )


def _article_jsonld(post: Post) -> dict[str, Any]:
    data: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": post.tr("title"),
        "mainEntityOfPage": urljoin(f"{settings.SITE_URL}/", post.get_absolute_url().lstrip("/")),
    }
    if post.published_at:
        data["datePublished"] = post.published_at.isoformat()
    if post.updated_at:
        data["dateModified"] = post.updated_at.isoformat()
    if post.cover:
        data["image"] = urljoin(f"{settings.SITE_URL}/", post.cover.url.lstrip("/"))
    if post.tr("excerpt"):
        data["description"] = post.tr("excerpt")
    return data


def post_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """A draft is a 404, exactly like an unpublished work."""
    post = (
        Post.objects.filter(slug=slug).prefetch_related("related_works__images__renditions").first()
    )
    if post is None or post.status != Post.Status.PUBLISHED:
        raise Http404
    if post.published_at is not None and post.published_at > timezone.now():
        raise Http404

    views_counter.record_post_view(post.pk)

    return render(
        request,
        "pages/post_detail.html",
        {
            "post": post,
            "related_works": list(post.related_works.all()),
            "article_jsonld": _article_jsonld(post),
            "breadcrumbs": [
                {"label": _("Home"), "url": reverse("home")},
                {"label": _("Blog"), "url": reverse("post_list")},
                {"label": post.tr("title")},
            ],
        },
    )

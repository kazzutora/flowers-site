from typing import Any

from django.apps import apps
from django.conf import settings as django_settings
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import NoReverseMatch, reverse
from django.utils.translation import gettext_lazy as _

from apps.catalog.models import Occasion, Work
from apps.core.models import HowToStep, SiteSettings, StaticPage

FRESH_WORKS = 12
FEATURED_REVIEWS = 3
LATEST_POSTS = 3


def _model_or_none(label: str) -> Any:
    """A model that may not have landed yet. The label is a variable on purpose:
    a literal would make the type checker insist the model exists today."""
    try:
        return apps.get_model(label)
    except LookupError:
        return None


def _featured_reviews() -> list[Any]:
    """Reviews land in stage 3. Until then the block simply has nothing to show."""
    review = _model_or_none("reviews.Review")
    if review is None:
        return []
    return list(review.objects.filter(status="published", is_featured=True)[:FEATURED_REVIEWS])


def _latest_posts() -> list[Any]:
    """The blog lands in stage 3, same story."""
    post = _model_or_none("blog.Post")
    if post is None:
        return []
    return list(post.objects.filter(status="published").order_by("-published_at")[:LATEST_POSTS])


def _optional_url(name: str) -> str:
    """A link to a page that may not have landed yet."""
    try:
        return reverse(name)
    except NoReverseMatch:
        return ""


def _local_business(site: SiteSettings) -> dict[str, Any]:
    """LocalBusiness for the home page and for the contacts page (section 16).

    AggregateRating is added in stage 3, once there are reviews to count.
    """
    data: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": str(site.tr("site_name") or _("Flower studio")),
        "url": django_settings.SITE_URL,
    }
    if site.phone_primary:
        data["telephone"] = str(site.phone_primary)
    if site.tr("address"):
        data["address"] = {"@type": "PostalAddress", "streetAddress": site.tr("address")}
    if site.tr("working_hours"):
        data["openingHours"] = site.tr("working_hours")
    if site.instagram_url:
        data["sameAs"] = [url for url in (site.instagram_url, site.facebook_url) if url]
    return data


def home(request: HttpRequest) -> HttpResponse:
    """Section 10. A block with nothing in it is not rendered at all."""
    site = SiteSettings.load()

    return render(
        request,
        "pages/home.html",
        {
            "occasions": Occasion.objects.filter(is_active=True, show_on_home=True),
            "works": Work.published.prefetch_related("images__renditions")[:FRESH_WORKS],
            "steps": HowToStep.objects.filter(is_active=True),
            "reviews": _featured_reviews(),
            "posts": _latest_posts(),
            "local_business": _local_business(site),
            "reviews_url": _optional_url("review_list"),
            "blog_url": _optional_url("post_list"),
        },
    )


def static_page(request: HttpRequest, slug: str) -> HttpResponse:
    page = get_object_or_404(StaticPage, slug=slug, is_published=True)
    breadcrumbs = [
        {"label": _("Home"), "url": reverse("home")},
        {"label": page.tr("title")},
    ]
    return render(request, "pages/static_page.html", {"page": page, "breadcrumbs": breadcrumbs})


def kitchen_sink(request: HttpRequest) -> HttpResponse:
    """Every UI primitive in every state. Development only, rendered on stubs."""
    if not django_settings.DEBUG:
        raise Http404

    from tests import stubs

    context: dict[str, Any] = stubs.kitchen_sink_context()
    return render(request, "pages/kitchen_sink.html", context)

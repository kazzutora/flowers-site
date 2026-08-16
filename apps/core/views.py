import logging
from typing import Any

from django.apps import apps
from django.conf import settings as django_settings
from django.core.cache import cache
from django.db import connection
from django.db.models import Avg, Count
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from apps.catalog.models import Occasion, Work
from apps.core.models import HowToStep, SiteSettings, StaticPage
from apps.core.services.images import compress_simple_image
from apps.leads.views import lead_form_context
from config.storages import public_storage

logger = logging.getLogger(__name__)

FRESH_WORKS = 12
# Section 12, `hero_showcase.html`: the fan holds three cards at most.
HERO_FAN_CARDS = 3
FEATURED_REVIEWS = 3
LATEST_POSTS = 3
# Section 16: an average below this many opinions is noise, not a rating.
MIN_RATED_REVIEWS = 5
# A picture inside a text is a picture, not an archive of one.
MAX_EDITOR_UPLOAD_BYTES = 25 * 1024 * 1024


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


def _aggregate_rating() -> dict[str, Any] | None:
    """Section 16: shown only from five rated reviews on.

    Below that the average says more about who happened to write than about the
    studio, and Google is not fond of it either.
    """
    review = _model_or_none("reviews.Review")
    if review is None:
        return None

    rated = review.objects.filter(status="published", rating__isnull=False)
    counted = rated.aggregate(total=Count("pk"), average=Avg("rating"))
    if (counted["total"] or 0) < MIN_RATED_REVIEWS:
        return None

    return {
        "@type": "AggregateRating",
        "ratingValue": round(float(counted["average"]), 1),
        "reviewCount": counted["total"],
        "bestRating": 5,
        "worstRating": 1,
    }


def _local_business(site: SiteSettings) -> dict[str, Any]:
    """LocalBusiness for the home page and for the contacts page (section 16)."""
    data: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": str(site.tr("site_name") or _("Flower studio")),
        "url": django_settings.SITE_URL,
    }
    rating = _aggregate_rating()
    if rating is not None:
        data["aggregateRating"] = rating
    if site.phone_primary:
        data["telephone"] = str(site.phone_primary)
    if site.tr("address"):
        data["address"] = {"@type": "PostalAddress", "streetAddress": site.tr("address")}
    if site.tr("working_hours"):
        data["openingHours"] = site.tr("working_hours")
    if site.instagram_url:
        data["sameAs"] = [url for url in (site.instagram_url, site.facebook_url) if url]
    return data


def _hero_images(site: SiteSettings, occasions: list[Occasion]) -> list[Any]:
    """The fan of section 10: the hero in front, occasion covers behind it.

    Built from the tiles the page already holds, so the fan costs no query of
    its own. Missing photographs simply shorten the fan.
    """
    candidates = [site.hero_image, *(occasion.cover for occasion in occasions)]
    return [image for image in candidates if image][:HERO_FAN_CARDS]


def home(request: HttpRequest) -> HttpResponse:
    """Section 10. A block with nothing in it is not rendered at all."""
    site = SiteSettings.load()
    occasions = list(Occasion.objects.filter(is_active=True, show_on_home=True))

    return render(
        request,
        "pages/home.html",
        {
            "occasions": occasions,
            "hero_images": _hero_images(site, occasions),
            "works": Work.published.prefetch_related("images__renditions")[:FRESH_WORKS],
            "steps": HowToStep.objects.filter(is_active=True),
            "reviews": _featured_reviews(),
            "posts": _latest_posts(),
            "local_business": _local_business(site),
            "reviews_url": _optional_url("review_list"),
            "blog_url": _optional_url("post_list"),
            # The "call me back" modal of section 10.
            **lead_form_context(request, "callback"),
        },
    )


def contacts(request: HttpRequest) -> HttpResponse:
    """`/kontakty/` (section 10). Everything on it comes from the admin."""
    site = SiteSettings.load()

    return render(
        request,
        "pages/contacts.html",
        {
            "local_business": _local_business(site),
            "breadcrumbs": [
                {"label": _("Home"), "url": reverse("home")},
                {"label": _("Contacts")},
            ],
            **lead_form_context(request, "full"),
        },
    )


DELIVERY_PAGE_SLUG = "dostavka-i-oplata"


def _delivery_columns(site: SiteSettings) -> list[dict[str, Any]]:
    """The band opening the delivery page (section 10).

    Assembled here rather than in the template: the primitive takes a plain
    list, and a column whose text the owner has not filled in is dropped
    instead of standing empty.
    """
    columns = [
        {"icon": "map-pin", "title": _("Shop"), "text": site.tr("address")},
        {"icon": "clock", "title": _("We work"), "text": site.tr("working_hours")},
        {"icon": "gift", "title": _("Pickup"), "text": site.tr("pickup_text")},
        {"icon": "truck", "title": _("Delivery"), "text": site.tr("delivery_text")},
    ]
    return [column for column in columns if column["text"]]


def static_page(request: HttpRequest, slug: str) -> HttpResponse:
    page = get_object_or_404(StaticPage, slug=slug, is_published=True)
    breadcrumbs = [
        {"label": _("Home"), "url": reverse("home")},
        {"label": page.tr("title")},
    ]
    columns = _delivery_columns(SiteSettings.load()) if slug == DELIVERY_PAGE_SLUG else []
    return render(
        request,
        "pages/static_page.html",
        {"page": page, "breadcrumbs": breadcrumbs, "info_columns": columns},
    )


@require_POST
def upload_image(request: HttpRequest) -> HttpResponse:
    """`/admin/upload-image/`: pictures dropped into the text editor.

    Staff only, and 403 rather than a redirect: the caller is TinyMCE, not a
    browser that can follow one. The file is squeezed once by
    `core/services/images.py` and gets no renditions (section 14.2).
    """
    user = request.user
    if not (user.is_authenticated and user.is_staff):
        return JsonResponse({"error": {"message": "forbidden"}}, status=403)

    upload = request.FILES.get("file")
    if upload is None:
        return JsonResponse({"error": {"message": "no file"}}, status=400)
    if (upload.size or 0) > MAX_EDITOR_UPLOAD_BYTES:
        return JsonResponse({"error": {"message": "too large"}}, status=400)

    compressed = compress_simple_image(upload, upload.name or "image")
    if compressed is None:
        return JsonResponse({"error": {"message": "not an image"}}, status=400)

    storage = public_storage()
    name = storage.save(f"content/{timezone.now():%Y/%m}/{compressed.name}", compressed)
    return JsonResponse({"location": storage.url(name)})


def healthz(request: HttpRequest) -> HttpResponse:
    """`/healthz/` (section 9). 200 while the dependencies answer, 503 otherwise.

    The check is deliberately cheap and honest: one round trip to Postgres and
    one to Redis. A load balancer needs to know whether this instance can serve
    a page, not how fast it is.
    """
    checks: dict[str, str] = {}

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks["database"] = "ok"
    except Exception as error:
        logger.error("healthz: the database is unreachable", exc_info=True)
        checks["database"] = f"error: {type(error).__name__}"

    try:
        cache.set("healthz", "ok", 10)
        checks["cache"] = "ok" if cache.get("healthz") == "ok" else "error: no round trip"
    except Exception as error:
        logger.error("healthz: the cache is unreachable", exc_info=True)
        checks["cache"] = f"error: {type(error).__name__}"

    healthy = all(value == "ok" for value in checks.values())
    return JsonResponse(
        {"status": "ok" if healthy else "error", **checks}, status=200 if healthy else 503
    )


def robots_txt(request: HttpRequest) -> HttpResponse:
    """Section 16: only /hx/ and /admin/ are closed here.

    /obrane/, /poshuk/ and /dyakuyemo/ are kept out of the index with a meta
    tag instead. Disallowing them here would stop the crawler from ever reading
    that tag.
    """
    lines = [
        "User-agent: *",
        "Disallow: /hx/",
        "Disallow: /admin/",
        # The same rules under the Russian prefix, as section 16 asks.
        "Disallow: /ru/hx/",
        "Disallow: /ru/admin/",
        "",
        f"Sitemap: {django_settings.SITE_URL}/sitemap.xml",
        "",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


def kitchen_sink(request: HttpRequest) -> HttpResponse:
    """Every UI primitive in every state. Development only, rendered on stubs."""
    if not django_settings.DEBUG:
        raise Http404

    from tests import stubs

    context: dict[str, Any] = stubs.kitchen_sink_context()
    return render(request, "pages/kitchen_sink.html", context)

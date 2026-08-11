"""Gallery views (sections 9 and 10).

The public page and the htmx fragment share one context builder, so the
fragment can never drift from the page it replaces.
"""

from typing import Any
from urllib.parse import urljoin

from django.conf import settings as django_settings
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.catalog import filters, seo
from apps.catalog.models import (
    Occasion,
    Tag,
    TagGroup,
    Work,
    WorkImage,
    WorkImageRendition,
)
from apps.catalog.services import views_counter
from apps.catalog.services.similar import similar_works
from apps.core.models import SiteSettings
from apps.leads.views import lead_form_context


def _filter_groups() -> list[TagGroup]:
    """Active groups with their active tags, ready for `ui/filter_group.html`."""
    return list(
        TagGroup.objects.filter(is_active=True).prefetch_related(
            Prefetch("tags", queryset=Tag.objects.filter(is_active=True))
        )
    )


def _gallery_context(
    request: HttpRequest, occasion: Occasion | None, *, fragment: bool
) -> dict[str, Any]:
    spec = filters.FilterSpec.from_db()
    query = filters.parse(request.GET, spec)

    works = filters.apply(query, occasion).prefetch_related("images__renditions")
    paginator = Paginator(works, filters.PAGE_SIZE)
    page_obj = paginator.get_page(query.page)

    base_path = seo.gallery_path(occasion.slug if occasion else None)
    robots, canonical = seo.robots_directive(
        occasion.slug if occasion else None, query.pairs, query.sort, page_obj.number
    )

    groups = _filter_groups()
    names = {tag.slug: tag for group in groups for tag in group.tags.all()}
    chips = [
        {
            "label": names[tag].tr("name") if tag in names else tag,
            "color_hex": names[tag].color_hex if tag in names else "",
            "remove_url": f"{base_path}{query.without(group, tag).query_string()}",
        }
        for group, tag in query.pairs
    ]

    next_url = (
        f"{base_path}{query.query_string(page=page_obj.next_page_number())}"
        if page_obj.has_next()
        else ""
    )
    # `ui/pagination.html` appends `page=N`, so the base has to end with a
    # separator already.
    carried = query.query_string(page=1)
    base_url = f"{base_path}{carried}&" if carried else f"{base_path}?"

    if occasion is not None:
        page_title = occasion.tr("seo_title") or occasion.tr("name")
        page_description = occasion.tr("seo_description")
        breadcrumbs = [
            {"label": _("Home"), "url": reverse("home")},
            {"label": _("Gallery"), "url": reverse("gallery")},
            {"label": occasion.tr("name")},
        ]
    else:
        page_title = _("Gallery")
        page_description = ""
        breadcrumbs = [{"label": _("Home"), "url": reverse("home")}, {"label": _("Gallery")}]

    active = len(query.pairs)
    filters_label = _("Filters · %(count)d") % {"count": active} if active else _("Filters")

    return {
        "occasion": occasion,
        "breadcrumbs": breadcrumbs,
        "filters_label": filters_label,
        "occasions": Occasion.objects.filter(is_active=True),
        "groups": groups,
        "query": query,
        "active_slugs": list(query.tag_slugs),
        "chips": chips,
        "page_obj": page_obj,
        "works": page_obj.object_list,
        "found_count": paginator.count,
        "base_path": base_path,
        "base_url": base_url,
        "public_url": f"{base_path}{query.query_string()}",
        "next_url": next_url,
        "sort_urls": {
            sort: f"{base_path}{query.with_sort(sort).query_string()}" for sort in filters.SORTS
        },
        "canonical_path": canonical,
        "robots": robots,
        "is_fragment": fragment,
        "page_title": page_title,
        "page_description": page_description,
    }


def gallery(request: HttpRequest, occasion_slug: str | None = None) -> HttpResponse:
    """`/galereya/` and `/galereya/<occasion>/`. An unknown occasion is a 404."""
    occasion = (
        get_object_or_404(Occasion, slug=occasion_slug, is_active=True) if occasion_slug else None
    )
    context = _gallery_context(request, occasion, fragment=bool(request.headers.get("HX-Request")))
    return render(request, "pages/gallery.html", context)


def hx_gallery(request: HttpRequest) -> HttpResponse:
    """The results fragment (section 9).

    The occasion travels as a parameter here because this endpoint is internal
    and noindex; the public gallery keeps it in the path, where it belongs.
    """
    slug = request.GET.get("occasion") or ""
    occasion = Occasion.objects.filter(slug=slug, is_active=True).first() if slug else None

    context = _gallery_context(request, occasion, fragment=True)
    response = render(request, "partials/gallery_fragment.html", context)
    # The address bar gets the public URL, never this endpoint.
    response.headers["HX-Push-Url"] = context["public_url"] or context["base_path"]
    return response


def work_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """`/robota/<slug>/`. Archived answers 410, a draft answers 404."""
    work = (
        Work.objects.filter(slug=slug)
        .prefetch_related("images__renditions", "occasions", "tags__group")
        .first()
    )
    if work is None or work.status == Work.Status.DRAFT:
        raise Http404
    if work.status == Work.Status.ARCHIVED:
        # 410 and not 404: the page may be indexed, and 410 clears it faster.
        return render(
            request,
            "410.html",
            {"similar": similar_works(work), "robots": "noindex, follow"},
            status=410,
        )
    if work.published_at is not None and work.published_at > timezone.now():
        raise Http404

    views_counter.record_work_view(work.pk)

    site = SiteSettings.load()
    images = list(work.images.all())
    main_image = work.main_image
    og_rendition = _og_rendition(main_image)
    breadcrumbs = [
        {"label": _("Home"), "url": reverse("home")},
        {"label": _("Gallery"), "url": reverse("gallery")},
        {"label": work.tr("title") or f"№{work.article}"},
    ]

    return render(
        request,
        "pages/work_detail.html",
        {
            "work": work,
            "images": images,
            "main_image": main_image,
            "og_rendition": og_rendition,
            "image_jsonld": _image_jsonld(work, og_rendition),
            "tags": list(work.tags.all()),
            "similar": similar_works(work),
            "breadcrumbs": breadcrumbs,
            "show_price": bool(
                site.prices_enabled and work.price_visible and work.price_from is not None
            ),
            "page_title": work.tr("seo_title") or f"№{work.article} {work.tr('title')}".strip(),
            "page_description": work.tr("seo_description") or work.tr("description"),
            # Everything `partials/lead_form.html` needs for the order modal.
            **lead_form_context(request, "full", work=work),
        },
    )


def search(request: HttpRequest) -> HttpResponse:
    """`/poshuk/` (section 10).

    A number is the fast path: someone read the article under a photo on
    Instagram. Everything else is a text search over the title and the
    composition, in both languages.
    """
    raw = (request.GET.get("q") or "").strip()
    works: Any = Work.published.none()

    if raw:
        article = filters.extract_article(raw)
        if article is not None:
            match = Work.published.filter(article=article).first()
            if match is not None:
                return redirect(match.get_absolute_url())

        works = (
            Work.published.filter(
                Q(title_uk__icontains=raw)
                | Q(title_ru__icontains=raw)
                | Q(composition_uk__icontains=raw)
                | Q(composition_ru__icontains=raw)
            )
            .prefetch_related("images__renditions")
            # A work matching on both the title and the composition is still
            # one work.
            .distinct()
        )

    return render(
        request,
        "pages/search.html",
        {
            "query_text": raw,
            "works": works,
            "found_count": len(works) if raw else 0,
            "breadcrumbs": [
                {"label": _("Home"), "url": reverse("home")},
                {"label": _("Search")},
            ],
        },
    )


def _works_by_article(raw: str) -> list[Work]:
    """Published works for a list of numbers, in the order they were given.

    Junk, duplicates, archived and unknown numbers fall out silently
    (section 10).
    """
    articles = filters.parse_articles(raw)
    if not articles:
        return []
    found = {
        work.article: work
        for work in Work.published.filter(article__in=articles).prefetch_related(
            "images__renditions"
        )
    }
    return [found[article] for article in articles if article in found]


def favorites(request: HttpRequest) -> HttpResponse:
    """`/obrane/`. With `?a=` it renders on the server, so the link travels."""
    raw = request.GET.get("a") or ""
    works = _works_by_article(raw)

    return render(
        request,
        "pages/favorites.html",
        {
            "works": works,
            "shared": bool(raw),
            "articles": ",".join(str(work.article) for work in works),
            "breadcrumbs": [
                {"label": _("Home"), "url": reverse("home")},
                {"label": _("Favourites")},
            ],
            **lead_form_context(request, "full"),
        },
    )


@require_POST
def hx_favorites(request: HttpRequest) -> HttpResponse:
    """The cards for the numbers the browser is holding (section 9)."""
    works = _works_by_article(request.POST.get("articles") or "")
    return render(request, "partials/favorites_grid.html", {"works": works, "shared": False})


def _image_jsonld(work: Work, rendition: WorkImageRendition | None) -> dict[str, Any] | None:
    """ImageObject only. `Product` needs an offer with a price (section 16)."""
    if rendition is None:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "ImageObject",
        "contentUrl": urljoin(f"{django_settings.SITE_URL}/", rendition.file.url.lstrip("/")),
        "name": f"№{work.article} {work.tr('title')}".strip(),
        "width": rendition.width,
        "height": rendition.height,
    }


def _og_rendition(image: WorkImage | None) -> WorkImageRendition | None:
    """The jpeg link preview: several messengers decode nothing else."""
    if image is None:
        return None
    for rendition in image.renditions.all():
        if (
            rendition.preset == WorkImageRendition.Preset.OG
            and rendition.image_format == WorkImageRendition.ImageFormat.JPEG
        ):
            return rendition
    return None

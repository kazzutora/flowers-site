from typing import Any

from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.core.models import StaticPage


def home(request: HttpRequest) -> HttpResponse:
    """Landing page. The remaining blocks of section 10 arrive with S1-6."""
    return render(request, "pages/home.html")


def static_page(request: HttpRequest, slug: str) -> HttpResponse:
    page = get_object_or_404(StaticPage, slug=slug, is_published=True)
    breadcrumbs = [
        {"label": _("Home"), "url": reverse("home")},
        {"label": page.tr("title")},
    ]
    return render(request, "pages/static_page.html", {"page": page, "breadcrumbs": breadcrumbs})


def kitchen_sink(request: HttpRequest) -> HttpResponse:
    """Every UI primitive in every state. Development only, rendered on stubs."""
    if not settings.DEBUG:
        raise Http404

    from tests import stubs

    context: dict[str, Any] = stubs.kitchen_sink_context()
    return render(request, "pages/kitchen_sink.html", context)

"""Reviews: the public list and the form that feeds it (sections 10 and 15).

The antispam layers are the ones from the enquiry form, with the review's own
limit keys: filling in a review must not use up someone's right to enquire.
"""

from typing import Any

from django.conf import settings
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.leads.services import antispam, ratelimit
from apps.reviews.forms import RATINGS, ReviewForm
from apps.reviews.models import Review

SCOPE = "review"
PAGE_SIZE = 20


def review_form_context(
    request: HttpRequest,
    *,
    form: ReviewForm | None = None,
    notice: str = "",
) -> dict[str, Any]:
    """Everything `partials/review_form.html` needs, wherever it is embedded."""
    return {
        "review_form": form,
        "review_form_token": antispam.timestamp_token(),
        "review_form_notice": notice,
        "rating_options": RATINGS,
        "turnstile_site_key": settings.ENV.turnstile_site_key or "",
    }


def review_list(request: HttpRequest) -> HttpResponse:
    """`/vidhuky/`. Only published reviews, newest first."""
    reviews = Review.published.select_related("work").prefetch_related("work__images__renditions")
    page_obj = Paginator(reviews, PAGE_SIZE).get_page(request.GET.get("page"))

    return render(
        request,
        "pages/review_list.html",
        {
            "page_obj": page_obj,
            "reviews": page_obj.object_list,
            "base_url": f"{reverse('review_list')}?",
            "breadcrumbs": [
                {"label": _("Home"), "url": reverse("home")},
                {"label": _("Reviews")},
            ],
            **review_form_context(request),
        },
    )


def _fragment(request: HttpRequest, form: ReviewForm | None, notice: str = "") -> HttpResponse:
    context = review_form_context(request, form=form, notice=notice)
    return render(request, "partials/review_form.html", context)


def _accepted(request: HttpRequest) -> HttpResponse:
    if request.headers.get("HX-Request"):
        response = HttpResponse(status=204)
        response.headers["HX-Redirect"] = reverse("thanks")
        return response
    return redirect(reverse("thanks"))


@require_POST
def hx_review(request: HttpRequest) -> HttpResponse:
    """Takes a review and parks it in `pending` until the owner says yes."""
    if antispam.honeypot_filled(request.POST) or antispam.filled_too_fast(request.POST):
        return _accepted(request)

    form = ReviewForm(request.POST, request.FILES)
    if not form.is_valid():
        return _fragment(request, form)

    if not antispam.turnstile_passed(request):
        return _fragment(
            request,
            form,
            _("The check did not pass. Please try again or give us a call."),
        )

    ip_hash = antispam.hash_ip(antispam.client_ip(request))
    allowed = ratelimit.within_limits(
        SCOPE,
        ip_hash,
        settings.ENV.review_rate_per_ip_hour,
        settings.ENV.review_rate_global_day,
    )

    review: Review = form.save(commit=False)
    review.source = Review.Source.SITE
    review.status = Review.Status.PENDING
    review.ip_hash = ip_hash
    review.user_agent = request.META.get("HTTP_USER_AGENT", "")
    if not allowed:
        # Kept and quietly rejected: the owner never sees it, and a real
        # person who wrote twice has not lost anything.
        review.status = Review.Status.REJECTED
    review.save()

    if not allowed:
        return _fragment(
            request,
            ReviewForm(),
            _("You have already left a review. Thank you!"),
        )

    from apps.reviews.tasks import notify_new_review

    review_id = review.pk
    transaction.on_commit(
        lambda: notify_new_review.apply_async(kwargs={"payload": {"review_id": review_id}})
    )
    return _accepted(request)

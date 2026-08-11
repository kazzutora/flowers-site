"""Taking an enquiry (sections 10 and 15).

The four antispam layers are applied in the order of section 15. The first two
answer exactly like a success and write nothing: a bot is never told it was
caught. A rate limit does the opposite - the row is written with the status
`spam`, because losing a real enquiry is worse than storing a bad one.
"""

from typing import Any

from django.conf import settings
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.catalog.filters import parse_articles
from apps.catalog.models import Work
from apps.leads.forms import BaseLeadForm, form_for
from apps.leads.models import Lead
from apps.leads.services import antispam, ratelimit

SCOPE = "lead"


def _thanks_url() -> str:
    return reverse("thanks")


def _accepted(request: HttpRequest) -> HttpResponse:
    """Section 10: htmx gets a redirect header, a plain form gets a 302."""
    if request.headers.get("HX-Request"):
        response = HttpResponse(status=204)
        response.headers["HX-Redirect"] = _thanks_url()
        return response
    return redirect(_thanks_url())


def _form_fragment(
    request: HttpRequest,
    form: BaseLeadForm,
    kind: str,
    *,
    notice: str = "",
    status: int = 200,
) -> HttpResponse:
    context = lead_form_context(request, kind, form=form, notice=notice)
    return render(request, "partials/lead_form.html", context, status=status)


def lead_form_context(
    request: HttpRequest,
    kind: str,
    *,
    form: BaseLeadForm | None = None,
    notice: str = "",
    work: Work | None = None,
) -> dict[str, Any]:
    """Everything `partials/lead_form.html` needs, wherever it is embedded."""
    return {
        "form": form,
        "form_kind": kind,
        "form_token": antispam.timestamp_token(),
        "form_notice": notice,
        "work": work,
        "turnstile_site_key": settings.ENV.turnstile_site_key or "",
        "contact_options": Lead.PreferredContact.choices,
        "source_url": request.POST.get("source_url") or request.get_full_path(),
    }


def _work_from(data: Any) -> tuple[Work | None, int | None]:
    raw = (data.get("work_article") or "").strip()
    if not raw.isdecimal():
        return None, None
    article = int(raw)
    return Work.objects.filter(article=article).first(), article


@require_POST
def hx_lead(request: HttpRequest) -> HttpResponse:
    kind = request.POST.get("form") or "full"
    form_class = form_for(kind)

    # Layers one and two: silence. The answer is the one a real visitor gets.
    if antispam.honeypot_filled(request.POST) or antispam.filled_too_fast(request.POST):
        return _accepted(request)

    form = form_class(request.POST)
    if not form.is_valid():
        return _form_fragment(request, form, kind)

    if not antispam.turnstile_passed(request):
        return _form_fragment(
            request,
            form,
            kind,
            notice=_("The check did not pass. Please try again or give us a call."),
        )

    ip_hash = antispam.hash_ip(antispam.client_ip(request))
    allowed = ratelimit.within_limits(
        SCOPE,
        ip_hash,
        settings.ENV.lead_rate_per_ip_hour,
        settings.ENV.lead_rate_global_day,
    )

    lead: Lead = form.save(commit=False)
    work, article = _work_from(request.POST)
    lead.work = work
    lead.work_article = article
    lead.favorites_articles = parse_articles(request.POST.get("favorites") or "")
    lead.source_url = (request.POST.get("source_url") or "")[:500]
    lead.ip_hash = ip_hash
    lead.user_agent = request.META.get("HTTP_USER_AGENT", "")
    if not allowed:
        lead.status = Lead.Status.SPAM
    lead.save()

    if not allowed:
        # Kept, not thrown away, and no notification is sent for it.
        return _form_fragment(
            request,
            form_class(),
            kind,
            notice=_("You have already sent an enquiry. Please give us a call."),
        )

    from apps.leads.tasks import notify_new_lead

    lead_id = lead.pk
    transaction.on_commit(
        lambda: notify_new_lead.apply_async(kwargs={"payload": {"lead_id": lead_id}})
    )
    return _accepted(request)


def thanks(request: HttpRequest) -> HttpResponse:
    """`/dyakuyemo/`. Exists always: it is the conversion mark (section 10)."""
    return render(request, "pages/thanks.html")

from typing import Any

from django.http import HttpRequest
from django.utils.functional import SimpleLazyObject

from apps.core.models import SiteSettings

CONSENT_COOKIE = "cookie_consent"
CONSENT_ACCEPTED = "accepted"


def _analytics_enabled(request: HttpRequest) -> bool:
    """Both switches, in the order of section 16.

    The choice is kept in localStorage under `cookie_consent:v1` and mirrored
    into a cookie, which is the only way the server can promise that nothing
    is loaded before the visitor said yes.
    """
    if request.COOKIES.get(CONSENT_COOKIE) != CONSENT_ACCEPTED:
        return False
    return bool(SiteSettings.load().analytics_ga_id)


def site_settings(request: HttpRequest) -> dict[str, Any]:
    """Expose the singleton to every template.

    Lazy: pages that never touch it (and error pages) pay nothing.
    """
    return {
        "site_settings": SimpleLazyObject(SiteSettings.load),
        "analytics_enabled": SimpleLazyObject(lambda: _analytics_enabled(request)),
    }

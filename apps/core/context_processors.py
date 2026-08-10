from typing import Any

from django.http import HttpRequest
from django.utils.functional import SimpleLazyObject

from apps.core.models import SiteSettings


def site_settings(request: HttpRequest) -> dict[str, Any]:
    """Expose the singleton to every template.

    Lazy: pages that never touch it (and error pages) pay nothing.
    """
    return {"site_settings": SimpleLazyObject(SiteSettings.load)}

import logging

from celery import shared_task
from django.utils import timezone

from apps.core.contracts import EmptyPayload

logger = logging.getLogger(__name__)


@shared_task(name="core.expire_banner")
def expire_banner(payload: dict) -> bool:
    """Untick the banner once its date has passed (section 8.5).

    The template already checks the date, so this changes nothing for a
    visitor. It exists so the owner opens the admin and sees the real state of
    the switch. Idempotent: a second run finds the box already unticked.
    """
    from apps.core.models import SiteSettings

    EmptyPayload.model_validate(payload)

    site = SiteSettings.load()
    if not site.banner_enabled or site.banner_until is None:
        return False
    if site.banner_until > timezone.now():
        return False

    site.banner_enabled = False
    site.save()
    logger.info("core.expire_banner: the banner was switched off")
    return True

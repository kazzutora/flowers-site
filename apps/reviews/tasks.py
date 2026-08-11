"""Telling the owner about a review (section 8.6).

The same three phases as the enquiry notification: claim, send outside every
lock, mark. A review waits in `pending`, so the message is a nudge to moderate,
not an order to fill.
"""

import logging
from typing import Any

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape
from django.utils.translation import gettext as _

from apps.reviews.contracts import ReviewNotificationPayload
from clients.dto import TelegramMessage
from clients.factory import get_telegram_client, telegram_chat_id

logger = logging.getLogger(__name__)

TEXT_LIMIT = 4096


def build_message(review: Any) -> str:
    lines = [
        f"<b>{escape(_('New review'))}</b>",
        escape(review.author_name),
    ]
    if review.rating:
        lines.append(f"{escape(_('Rating'))}: {review.rating}/5")
    if review.contact_phone:
        lines.append(f"<code>{escape(str(review.contact_phone))}</code>")
    text = review.text_uk or review.text_ru
    if text:
        lines.append(escape(text))

    admin_path = reverse("admin:reviews_review_change", args=[review.pk])
    lines.append(
        f'<a href="{settings.SITE_URL}{admin_path}">{escape(_("Moderate in the admin"))}</a>'
    )

    message = "\n".join(lines)
    return message if len(message) <= TEXT_LIMIT else f"{message[: TEXT_LIMIT - 1]}…"


@shared_task(name="reviews.notify_new_review", bind=True)
def notify_new_review(self: Any, payload: dict) -> str:
    from apps.reviews.models import Review

    data = ReviewNotificationPayload.model_validate(payload)
    is_retry = bool(getattr(self.request, "retries", 0))

    # Phase one: claim it inside a short transaction.
    with transaction.atomic():
        review = Review.objects.select_for_update().filter(pk=data.review_id).first()
        if review is None:
            logger.info("reviews.notify_new_review: review %s is gone", data.review_id)
            return "missing"
        if review.notified_at is not None:
            return "already sent"
        if review.status == Review.Status.REJECTED:
            return "rejected"
        if review.notify_attempts and not is_retry:
            return "already sent"
        Review.objects.filter(pk=review.pk).update(notify_attempts=review.notify_attempts + 1)

    # Phase two: the network, outside every lock.
    result = get_telegram_client().send_message(
        TelegramMessage(chat_id=telegram_chat_id(), text=build_message(review))
    )
    if not result.ok:
        logger.error("reviews.notify_new_review: telegram refused %s: %s", review.pk, result.error)
        return "refused"

    # Phase three: mark it, in its own transaction.
    Review.objects.filter(pk=review.pk).update(notified_at=timezone.now())
    return "sent"

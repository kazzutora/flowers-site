"""Telling the owner about an enquiry (section 8.1).

Three phases, and the network call sits between the two transactions. Holding
a ten second HTTP request inside a row lock is both a long lock and a way to
send the same message twice when the transaction rolls back.
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

from apps.leads.contracts import LeadNotificationPayload
from clients.dto import TelegramMessage
from clients.factory import get_telegram_client, telegram_chat_id

logger = logging.getLogger(__name__)

TEXT_LIMIT = 4096


def build_message(lead: Any) -> str:
    """The message the owner reads on a phone.

    The number goes on its own line inside `<code>`: Telegram does not make
    `tel:` links, and a tap on a code block copies it.
    """
    lines = [
        f"<b>{escape(_('New enquiry'))}</b>",
        escape(lead.name),
        f"<code>{escape(str(lead.phone))}</code>",
        f"{escape(_('Channel'))}: {escape(lead.get_preferred_contact_display())}",
    ]
    if lead.event_date:
        lines.append(f"{escape(_('Date'))}: {lead.event_date:%d.%m.%Y}")
    if lead.budget_text:
        lines.append(f"{escape(_('Budget'))}: {escape(lead.budget_text)}")
    if lead.work_article:
        lines.append(f"{escape(_('Work'))}: №{lead.work_article}")
    if lead.favorites_articles:
        numbers = ", ".join(f"№{article}" for article in lead.favorites_articles)
        lines.append(f"{escape(_('Favourites'))}: {numbers}")
    if lead.comment:
        lines.append(escape(lead.comment))

    admin_path = reverse("admin:leads_lead_change", args=[lead.pk])
    lines.append(f'<a href="{settings.SITE_URL}{admin_path}">{escape(_("Open in the admin"))}</a>')

    text = "\n".join(lines)
    return text if len(text) <= TEXT_LIMIT else f"{text[: TEXT_LIMIT - 1]}…"


@shared_task(name="leads.notify_new_lead", bind=True)
def notify_new_lead(self: Any, payload: dict) -> str:
    from apps.leads.models import Lead

    data = LeadNotificationPayload.model_validate(payload)
    # A retry of this very task is allowed to pick the enquiry up again; a
    # second, parallel task is not.
    is_retry = bool(getattr(self.request, "retries", 0))

    # Phase one: claim the enquiry inside a short transaction.
    with transaction.atomic():
        lead = Lead.objects.select_for_update().filter(pk=data.lead_id).first()
        if lead is None:
            logger.info("leads.notify_new_lead: enquiry %s is gone", data.lead_id)
            return "missing"
        if lead.notified_at is not None:
            return "already sent"
        if lead.status == Lead.Status.SPAM:
            return "spam"
        if lead.notify_attempts and not is_retry:
            # Someone else took it between the two transactions below. Sending
            # twice is worse than letting the retry chain finish the job.
            return "already sent"
        Lead.objects.filter(pk=lead.pk).update(notify_attempts=lead.notify_attempts + 1)

    # Phase two: the network, outside every lock.
    result = get_telegram_client().send_message(
        TelegramMessage(chat_id=telegram_chat_id(), text=build_message(lead))
    )
    if not result.ok:
        # Not transient: the message itself was refused. The enquiry stays put.
        logger.error("leads.notify_new_lead: telegram refused %s: %s", lead.pk, result.error)
        return "refused"

    # Phase three: mark it, in its own transaction.
    Lead.objects.filter(pk=lead.pk).update(notified_at=timezone.now())
    return "sent"

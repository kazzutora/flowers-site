"""Section 4.12. Enquiries are never deleted automatically."""

from typing import Any

from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

USER_AGENT_LIMIT = 300


class Lead(models.Model):
    """One enquiry. The raw IP is never stored, only its hash (section 15)."""

    class PreferredContact(models.TextChoices):
        PHONE = "phone", _("Phone call")
        VIBER = "viber", _("Viber")
        TELEGRAM = "telegram", _("Telegram")

    class Status(models.TextChoices):
        NEW = "new", _("New")
        IN_PROGRESS = "in_progress", _("In progress")
        DONE = "done", _("Done")
        SPAM = "spam", _("Spam")

    name = models.CharField(_("name"), max_length=100)
    phone = PhoneNumberField(_("phone"), region="UA")
    preferred_contact = models.CharField(
        _("preferred contact"),
        max_length=20,
        choices=PreferredContact.choices,
        default=PreferredContact.PHONE,
    )
    event_date = models.DateField(_("event date"), null=True, blank=True)
    budget_text = models.CharField(_("budget"), max_length=50, blank=True)
    comment = models.CharField(_("comment"), max_length=1000, blank=True)
    work = models.ForeignKey(
        "catalog.Work",
        verbose_name=_("work"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="leads",
    )
    # A snapshot: the work may be archived later, the number stays readable.
    work_article = models.PositiveIntegerField(_("work number"), null=True, blank=True)
    favorites_articles = models.JSONField(_("favourites"), default=list, blank=True)
    status = models.CharField(
        _("status"), max_length=20, choices=Status.choices, default=Status.NEW
    )
    source_url = models.URLField(_("came from"), max_length=500, blank=True)
    ip_hash = models.CharField(max_length=64, blank=True)
    user_agent = models.CharField(max_length=USER_AGENT_LIMIT, blank=True)
    consent = models.BooleanField(_("consent"), default=False)
    notified_at = models.DateTimeField(null=True, blank=True, editable=False)
    notify_attempts = models.PositiveSmallIntegerField(default=0, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "created_at"], name="lead_status_created_idx")]
        verbose_name = _("enquiry")
        verbose_name_plural = _("enquiries")

    def __str__(self) -> str:
        return f"{self.name} {self.phone}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        # Browsers send long strings and some of them are longer than the column.
        self.user_agent = (self.user_agent or "")[:USER_AGENT_LIMIT]
        super().save(*args, **kwargs)

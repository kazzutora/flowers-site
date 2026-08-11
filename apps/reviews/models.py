"""Section 4.10. Only published reviews ever leave the database."""

from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from apps.core.models import TranslatedMixin
from apps.core.services.images import compress_field
from config.storages import public_storage

USER_AGENT_LIMIT = 300


class PublishedReviewManager(models.Manager["Review"]):
    def get_queryset(self) -> models.QuerySet["Review"]:
        return super().get_queryset().filter(status=Review.Status.PUBLISHED)


class Review(TranslatedMixin, models.Model):
    """A review. From the site it arrives as `pending` and waits for the owner."""

    class Source(models.TextChoices):
        ADMIN = "admin", _("Added by the owner")
        SITE = "site", _("Left on the site")

    class Status(models.TextChoices):
        PENDING = "pending", _("Waiting for moderation")
        PUBLISHED = "published", _("Published")
        REJECTED = "rejected", _("Rejected")

    author_name = models.CharField(_("name"), max_length=100)
    text_uk = models.TextField(_("text, uk"), blank=True)
    text_ru = models.TextField(_("text, ru"), blank=True)
    rating = models.PositiveSmallIntegerField(_("rating"), null=True, blank=True)
    photo = models.ImageField(_("photo"), upload_to="reviews/", storage=public_storage, blank=True)
    work = models.ForeignKey(
        "catalog.Work",
        verbose_name=_("work"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviews",
    )
    source = models.CharField(
        _("source"), max_length=10, choices=Source.choices, default=Source.ADMIN
    )
    status = models.CharField(
        _("status"), max_length=20, choices=Status.choices, default=Status.PENDING
    )
    # For calling back about the review. Never rendered publicly.
    contact_phone = PhoneNumberField(_("phone for us"), region="UA", blank=True)
    is_featured = models.BooleanField(_("show on the home page"), default=False)
    consent = models.BooleanField(_("consent"), default=False)
    ip_hash = models.CharField(max_length=64, blank=True)
    user_agent = models.CharField(max_length=USER_AGENT_LIMIT, blank=True)
    notified_at = models.DateTimeField(null=True, blank=True, editable=False)
    notify_attempts = models.PositiveSmallIntegerField(default=0, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(_("published at"), null=True, blank=True)

    objects = models.Manager()
    published = PublishedReviewManager()

    class Meta:
        ordering = ["-published_at", "-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(rating__isnull=True) | Q(rating__gte=1, rating__lte=5),
                name="review_rating_range",
            )
        ]
        verbose_name = _("review")
        verbose_name_plural = _("reviews")

    def __str__(self) -> str:
        return f"{self.author_name} ({self.get_status_display()})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.user_agent = (self.user_agent or "")[:USER_AGENT_LIMIT]
        # Section 14.2: a review photo is squeezed once and gets no renditions.
        compress_field(self, "photo")
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        errors: dict[str, Any] = {}

        if not self.text_uk and not self.text_ru:
            errors["text_uk"] = _("Write the review in at least one language.")
        if self.rating is not None and not 1 <= self.rating <= 5:
            errors["rating"] = _("The rating goes from 1 to 5.")
        if self.source == self.Source.SITE and not self.consent:
            errors["consent"] = _("A review left on the site needs consent.")

        if errors:
            raise ValidationError(errors)

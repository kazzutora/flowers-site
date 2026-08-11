"""Section 4.11. The blog has no categories in v1."""

from typing import Any

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import TranslatedMixin
from apps.core.services.images import compress_field
from apps.core.services.sanitize import sanitize_html
from config.storages import public_storage


class PublishedPostManager(models.Manager["Post"]):
    def get_queryset(self) -> models.QuerySet["Post"]:
        return (
            super()
            .get_queryset()
            .filter(status=Post.Status.PUBLISHED, published_at__lte=timezone.now())
        )


class Post(TranslatedMixin, models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        PUBLISHED = "published", _("Published")

    slug = models.SlugField(_("slug"), max_length=200, unique=True)
    title_uk = models.CharField(_("title, uk"), max_length=200)
    title_ru = models.CharField(_("title, ru"), max_length=200, blank=True)
    excerpt_uk = models.CharField(_("excerpt, uk"), max_length=300, blank=True)
    excerpt_ru = models.CharField(_("excerpt, ru"), max_length=300, blank=True)
    body_uk = models.TextField(_("body, uk"), blank=True)
    body_ru = models.TextField(_("body, ru"), blank=True)
    cover = models.ImageField(_("cover"), upload_to="blog/", storage=public_storage, blank=True)
    related_works = models.ManyToManyField(
        "catalog.Work", verbose_name=_("related works"), related_name="posts", blank=True
    )
    status = models.CharField(
        _("status"), max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    published_at = models.DateTimeField(_("published at"), null=True, blank=True)
    views_count = models.PositiveIntegerField(_("views"), default=0)
    seo_title_uk = models.CharField(_("SEO title, uk"), max_length=200, blank=True)
    seo_title_ru = models.CharField(_("SEO title, ru"), max_length=200, blank=True)
    seo_description_uk = models.CharField(_("SEO description, uk"), max_length=300, blank=True)
    seo_description_ru = models.CharField(_("SEO description, ru"), max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    published = PublishedPostManager()

    class Meta:
        ordering = [models.F("published_at").desc(nulls_last=True), "-id"]
        indexes = [
            models.Index(fields=["status", "published_at"], name="post_status_published_idx")
        ]
        verbose_name = _("post")
        verbose_name_plural = _("posts")

    def __str__(self) -> str:
        return self.title_uk

    def save(self, *args: Any, **kwargs: Any) -> None:
        # Sanitised on write, like every other body the owner types (4.8).
        self.body_uk = sanitize_html(self.body_uk)
        self.body_ru = sanitize_html(self.body_ru)
        # Section 14.2: a cover is squeezed once and gets no renditions.
        compress_field(self, "cover")
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("post_detail", kwargs={"slug": self.slug})

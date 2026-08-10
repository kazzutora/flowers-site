import hashlib
import logging
from typing import Any

from django.core.cache import cache
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from apps.core.services.sanitize import sanitize_html

logger = logging.getLogger(__name__)


class TranslatedMixin:
    """Access to `<field>_uk` / `<field>_ru` pairs (section 11 of tech.md).

    Templates must go through the `tr` filter: reading `title_uk` directly would
    silently show Ukrainian text on the Russian version of the page.
    """

    def tr(self, field: str) -> str:
        lang = get_language() or "uk"
        return getattr(self, f"{field}_{lang}", "") or getattr(self, f"{field}_uk", "") or ""


class SiteSettings(TranslatedMixin, models.Model):
    """Singleton (pk=1) with everything the owner edits without a developer."""

    CACHE_KEY = "site_settings:v1"
    CACHE_TTL = 3600

    class WatermarkPosition(models.TextChoices):
        BOTTOM_RIGHT = "bottom_right", _("Bottom right")
        BOTTOM_LEFT = "bottom_left", _("Bottom left")
        CENTER = "center", _("Center")

    # contacts
    phone_primary = PhoneNumberField(_("main phone"), blank=True)
    phone_secondary = PhoneNumberField(_("second phone"), blank=True)
    email = models.EmailField(_("email"), blank=True)
    viber_url = models.URLField(_("Viber link"), blank=True)
    telegram_url = models.URLField(_("Telegram link"), blank=True)
    instagram_url = models.URLField(_("Instagram link"), blank=True)
    facebook_url = models.URLField(_("Facebook link"), blank=True)

    # address
    address_uk = models.CharField(_("address, uk"), max_length=300, blank=True)
    address_ru = models.CharField(_("address, ru"), max_length=300, blank=True)
    landmark_uk = models.CharField(_("landmark, uk"), max_length=300, blank=True)
    landmark_ru = models.CharField(_("landmark, ru"), max_length=300, blank=True)
    parking_uk = models.CharField(_("parking, uk"), max_length=300, blank=True)
    parking_ru = models.CharField(_("parking, ru"), max_length=300, blank=True)
    map_embed_url = models.URLField(_("map embed URL"), max_length=500, blank=True)
    map_directions_url = models.URLField(_("directions URL"), max_length=500, blank=True)

    # working hours
    working_hours_uk = models.TextField(_("working hours, uk"), blank=True)
    working_hours_ru = models.TextField(_("working hours, ru"), blank=True)

    # taking orders
    accepting_orders = models.BooleanField(_("accepting orders"), default=True)
    not_accepting_message_uk = models.CharField(
        _("not accepting message, uk"), max_length=300, blank=True
    )
    not_accepting_message_ru = models.CharField(
        _("not accepting message, ru"), max_length=300, blank=True
    )

    # banner
    banner_enabled = models.BooleanField(_("banner enabled"), default=False)
    banner_text_uk = models.CharField(_("banner text, uk"), max_length=300, blank=True)
    banner_text_ru = models.CharField(_("banner text, ru"), max_length=300, blank=True)
    banner_url = models.URLField(_("banner link"), blank=True)
    banner_until = models.DateTimeField(_("banner until"), null=True, blank=True)

    # prices
    prices_enabled = models.BooleanField(_("prices enabled"), default=False)

    # watermark
    watermark_image = models.ImageField(_("watermark"), upload_to="site/", blank=True)
    watermark_opacity = models.FloatField(
        _("watermark opacity"),
        default=0.35,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    watermark_position = models.CharField(
        _("watermark position"),
        max_length=20,
        choices=WatermarkPosition.choices,
        default=WatermarkPosition.BOTTOM_RIGHT,
    )
    watermark_scale = models.FloatField(
        _("watermark scale"),
        default=0.18,
        validators=[MinValueValidator(0.01), MaxValueValidator(1.0)],
    )

    # seo and analytics
    og_default_image = models.ImageField(_("default OG image"), upload_to="site/", blank=True)
    analytics_ga_id = models.CharField(_("GA4 measurement id"), max_length=50, blank=True)
    site_name_uk = models.CharField(_("site name, uk"), max_length=100, blank=True)
    site_name_ru = models.CharField(_("site name, ru"), max_length=100, blank=True)

    # home page
    hero_title_uk = models.CharField(_("hero title, uk"), max_length=200, blank=True)
    hero_title_ru = models.CharField(_("hero title, ru"), max_length=200, blank=True)
    hero_subtitle_uk = models.CharField(_("hero subtitle, uk"), max_length=300, blank=True)
    hero_subtitle_ru = models.CharField(_("hero subtitle, ru"), max_length=300, blank=True)
    hero_image = models.ImageField(_("hero image"), upload_to="site/", blank=True)

    class Meta:
        verbose_name = _("site settings")
        verbose_name_plural = _("site settings")

    def __str__(self) -> str:
        return str(_("Site settings"))

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.pk = 1
        # `objects.create()` asks for an insert; for a singleton that has to be
        # an update instead of an integrity error.
        kwargs.pop("force_insert", None)
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("SiteSettings is a singleton and must not be deleted")

    @classmethod
    def load(cls) -> "SiteSettings":
        """Read the singleton. An unreachable cache degrades to a direct read."""
        try:
            cached = cache.get(cls.CACHE_KEY)
        # Broad on purpose: no cache failure may reach the visitor.
        except Exception:
            logger.warning("site settings cache unavailable on read", exc_info=True)
            cached = None
        if cached is not None:
            return cached

        obj, _created = cls.objects.get_or_create(pk=1)
        try:
            cache.set(cls.CACHE_KEY, obj, cls.CACHE_TTL)
        except Exception:
            logger.warning("site settings cache unavailable on write", exc_info=True)
        return obj

    @property
    def banner_is_active(self) -> bool:
        if not self.banner_enabled:
            return False
        return self.banner_until is None or self.banner_until > timezone.now()

    @property
    def banner_dismiss_hash(self) -> str:
        """Identity of the current banner: a new text or date brings it back."""
        until = self.banner_until.isoformat() if self.banner_until else ""
        return hashlib.sha256(f"{self.banner_text_uk}|{until}".encode()).hexdigest()[:16]


@receiver(post_save, sender=SiteSettings)
def invalidate_site_settings_cache(sender: type[SiteSettings], **kwargs: Any) -> None:
    try:
        cache.delete(SiteSettings.CACHE_KEY)
    except Exception:
        logger.warning("site settings cache unavailable on invalidation", exc_info=True)


class StaticPage(TranslatedMixin, models.Model):
    """Text page edited in the admin: about, delivery, faq, privacy policy."""

    slug = models.SlugField(_("slug"), max_length=60, unique=True)
    title_uk = models.CharField(_("title, uk"), max_length=200)
    title_ru = models.CharField(_("title, ru"), max_length=200, blank=True)
    body_uk = models.TextField(_("body, uk"), blank=True)
    body_ru = models.TextField(_("body, ru"), blank=True)
    seo_title_uk = models.CharField(_("SEO title, uk"), max_length=200, blank=True)
    seo_title_ru = models.CharField(_("SEO title, ru"), max_length=200, blank=True)
    seo_description_uk = models.CharField(_("SEO description, uk"), max_length=300, blank=True)
    seo_description_ru = models.CharField(_("SEO description, ru"), max_length=300, blank=True)
    is_published = models.BooleanField(_("published"), default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["slug"]
        verbose_name = _("static page")
        verbose_name_plural = _("static pages")

    def __str__(self) -> str:
        return self.title_uk or self.slug

    def save(self, *args: Any, **kwargs: Any) -> None:
        # Sanitising on write, not on render: the body is later marked safe by
        # the `tr_html` filter.
        self.body_uk = sanitize_html(self.body_uk)
        self.body_ru = sanitize_html(self.body_ru)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("static_page", kwargs={"slug": self.slug})


class HowToStep(TranslatedMixin, models.Model):
    """A step of the "how to order" block on the home page."""

    order = models.PositiveSmallIntegerField(_("order"), default=0)
    title_uk = models.CharField(_("title, uk"), max_length=200)
    title_ru = models.CharField(_("title, ru"), max_length=200, blank=True)
    text_uk = models.TextField(_("text, uk"), blank=True)
    text_ru = models.TextField(_("text, ru"), blank=True)
    icon = models.CharField(_("icon"), max_length=50, blank=True)
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = _("how to order step")
        verbose_name_plural = _("how to order steps")

    def __str__(self) -> str:
        return self.title_uk

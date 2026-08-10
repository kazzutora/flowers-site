from typing import Any

from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from apps.core.models import HowToStep, SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(ModelAdmin):
    fieldsets = (
        (_("Contacts"), {"fields": (
            "phone_primary",
            "phone_secondary",
            "email",
            "viber_url",
            "telegram_url",
            "instagram_url",
            "facebook_url",
        )}),
        (_("Address"), {"fields": (
            "address_uk",
            "address_ru",
            "landmark_uk",
            "landmark_ru",
            "parking_uk",
            "parking_ru",
            "map_embed_url",
            "map_directions_url",
        )}),
        (_("Working hours"), {"fields": ("working_hours_uk", "working_hours_ru")}),
        (_("Taking orders"), {"fields": (
            "accepting_orders",
            "not_accepting_message_uk",
            "not_accepting_message_ru",
        )}),
        (_("Banner"), {"fields": (
            "banner_enabled",
            "banner_text_uk",
            "banner_text_ru",
            "banner_url",
            "banner_until",
        )}),
        (_("Prices"), {"fields": ("prices_enabled",)}),
        (_("Watermark"), {"fields": (
            "watermark_image",
            "watermark_opacity",
            "watermark_position",
            "watermark_scale",
        )}),
        (_("SEO and analytics"), {"fields": (
            "og_default_image",
            "analytics_ga_id",
            "site_name_uk",
            "site_name_ru",
        )}),
        (_("Home page"), {"fields": (
            "hero_title_uk",
            "hero_title_ru",
            "hero_subtitle_uk",
            "hero_subtitle_ru",
            "hero_image",
        )}),
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def changelist_view(
        self, request: HttpRequest, extra_context: dict[str, Any] | None = None
    ) -> HttpResponse:
        # A single row has no list: go straight to the form.
        settings = SiteSettings.load()
        return redirect(reverse("admin:core_sitesettings_change", args=[settings.pk]))


@admin.register(HowToStep)
class HowToStepAdmin(ModelAdmin):
    list_display = ("title_uk", "order", "is_active")
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)
    fieldsets = (
        (None, {"fields": ("order", "icon", "is_active")}),
        (_("Content"), {"fields": ("title_uk", "title_ru", "text_uk", "text_ru")}),
    )

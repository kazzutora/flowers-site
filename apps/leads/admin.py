from typing import Any

from django.contrib import admin
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from apps.leads.models import Lead


@admin.register(Lead)
class LeadAdmin(ModelAdmin):
    list_display = ("created_at", "name", "phone", "status", "work_article", "notified_at")
    list_filter = ("status", "preferred_contact", "created_at")
    search_fields = ("name", "phone", "comment")
    date_hierarchy = "created_at"
    readonly_fields = (
        "created_at",
        "ip_hash",
        "user_agent",
        "source_url",
        "notified_at",
        "notify_attempts",
        "favorites_articles",
        "work_article",
    )
    fieldsets = (
        (None, {"fields": ("status", "created_at")}),
        (
            _("Enquiry"),
            {
                "fields": (
                    "name",
                    "phone",
                    "preferred_contact",
                    "event_date",
                    "budget_text",
                    "comment",
                )
            },
        ),
        (_("Works"), {"fields": ("work", "work_article", "favorites_articles")}),
        (
            _("Technical"),
            {
                "classes": ("collapse",),
                "fields": (
                    "consent",
                    "source_url",
                    "ip_hash",
                    "user_agent",
                    "notified_at",
                    "notify_attempts",
                ),
            },
        ),
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        # Enquiries arrive from the site, never from here.
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

from typing import Any

from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from unfold.admin import ModelAdmin

from apps.reviews.models import Review


@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    list_display = ("author_name", "rating", "status", "source", "is_featured", "created_at")
    list_filter = ("status", "source", "is_featured", "rating")
    search_fields = ("author_name", "text_uk", "text_ru")
    list_editable = ("is_featured",)
    date_hierarchy = "created_at"
    actions = ["publish", "reject", "feature"]
    readonly_fields = ("created_at", "ip_hash", "user_agent", "notified_at", "notify_attempts")
    fieldsets = (
        (None, {"fields": ("status", "source", "is_featured", "created_at", "published_at")}),
        (
            _("Review"),
            {"fields": ("author_name", "rating", "text_uk", "text_ru", "photo", "work")},
        ),
        (
            _("Technical"),
            {
                "classes": ("collapse",),
                # The phone is for calling the author back; it never reaches a page.
                "fields": (
                    "contact_phone",
                    "consent",
                    "ip_hash",
                    "user_agent",
                    "notified_at",
                    "notify_attempts",
                ),
            },
        ),
    )

    def get_changeform_initial_data(self, request: HttpRequest) -> dict[str, Any]:
        # Section 4.10: what the owner types in here is published straight away.
        return {"source": Review.Source.ADMIN, "status": Review.Status.PUBLISHED, "consent": True}

    @admin.action(description=_("Publish the selected reviews"))
    def publish(self, request: HttpRequest, queryset: QuerySet[Review]) -> None:
        published = 0
        for review in queryset:
            review.status = Review.Status.PUBLISHED
            review.save()
            published += 1
        self.message_user(
            request,
            ngettext("%(count)d review published.", "%(count)d reviews published.", published)
            % {"count": published},
            level=messages.SUCCESS if published else messages.WARNING,
        )

    @admin.action(description=_("Reject the selected reviews"))
    def reject(self, request: HttpRequest, queryset: QuerySet[Review]) -> None:
        updated = queryset.update(status=Review.Status.REJECTED)
        self.message_user(
            request,
            ngettext("%(count)d review rejected.", "%(count)d reviews rejected.", updated)
            % {"count": updated},
        )

    @admin.action(description=_("Show the selected reviews on the home page"))
    def feature(self, request: HttpRequest, queryset: QuerySet[Review]) -> None:
        updated = queryset.update(is_featured=True)
        self.message_user(
            request,
            ngettext(
                "%(count)d review moved to the home page.",
                "%(count)d reviews moved to the home page.",
                updated,
            )
            % {"count": updated},
        )

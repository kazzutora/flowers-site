from django.contrib import admin
from django.db import models
from django.utils.translation import gettext_lazy as _
from tinymce.widgets import TinyMCE
from unfold.admin import ModelAdmin

from apps.blog.models import Post


@admin.register(Post)
class PostAdmin(ModelAdmin):
    class Media:
        # Defines window.uploadEditorImage, which the TinyMCE config names.
        js = ("js/tinymce-upload.js",)

    list_display = ("title_uk", "slug", "status", "published_at", "views_count")
    list_filter = ("status",)
    search_fields = ("slug", "title_uk", "title_ru", "body_uk", "body_ru")
    prepopulated_fields = {"slug": ("title_uk",)}
    readonly_fields = ("views_count", "created_at", "updated_at")
    filter_horizontal = ("related_works",)
    formfield_overrides = {models.TextField: {"widget": TinyMCE()}}
    fieldsets = (
        (None, {"fields": ("slug", "status", "published_at", "cover", "views_count")}),
        (
            _("Content"),
            {
                "fields": (
                    "title_uk",
                    "title_ru",
                    "excerpt_uk",
                    "excerpt_ru",
                    "body_uk",
                    "body_ru",
                )
            },
        ),
        (_("Related works"), {"fields": ("related_works",)}),
        (
            _("SEO"),
            {
                "classes": ("collapse",),
                "fields": (
                    "seo_title_uk",
                    "seo_title_ru",
                    "seo_description_uk",
                    "seo_description_ru",
                ),
            },
        ),
    )

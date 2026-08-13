"""Catalog admin: adding a work with several photos has to fit in a minute.

Section 4.4 puts the "a published work needs a photo" rule in the inline
formset and in `save_related`, never in `Work.clean()`: inlines are saved after
the parent, so `clean()` would always see zero photos.
"""

import re
from typing import Any

from adminsortable2.admin import (
    CustomInlineFormSet,
    SortableAdminBase,
    SortableAdminMixin,
    SortableInlineAdminMixin,
)
from django import forms
from django.contrib import admin, messages
from django.db import models
from django.db.models import QuerySet
from django.forms.models import BaseInlineFormSet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action as unfold_action

from apps.catalog.models import (
    Occasion,
    Tag,
    TagGroup,
    Work,
    WorkImage,
    WorkImageRendition,
)
from apps.catalog.tasks import regenerate_all_renditions


def _thumbnail(image: WorkImage | None) -> str:
    """The webp thumbnail, or nothing while the renditions are still queued."""
    if image is None:
        return ""
    for rendition in image.renditions.all():
        if (
            rendition.preset == WorkImageRendition.Preset.THUMB
            and rendition.image_format == WorkImageRendition.ImageFormat.WEBP
        ):
            return str(rendition.file.url)
    return ""


class WorkImageInlineFormSet(CustomInlineFormSet):
    """Refuses to publish a work that would end up without a single photo.

    Built on the sortable formset: dragging photos into order and validating
    the set are the same form submission.
    """

    def clean(self) -> None:
        super().clean()
        # `self.instance` is the work carrying the status just submitted, not
        # the one stored in the database.
        if getattr(self.instance, "status", None) != Work.Status.PUBLISHED:
            return

        remaining = 0
        for form in self.forms:
            cleaned = getattr(form, "cleaned_data", None)
            if not cleaned or cleaned.get("DELETE"):
                continue
            if cleaned.get("image") or (form.instance.pk and form.instance.image):
                remaining += 1

        if remaining == 0:
            raise forms.ValidationError(
                _("A published work needs at least one photo. Add a photo or save it as a draft.")
            )

    def save_new(self, form: Any, commit: bool = True) -> WorkImage:
        # Skips the sortable mixin, which numbers new rows from one. Section 4.5
        # gives `order` a default of 0 and the model lines new photos up behind
        # the existing ones itself.
        return BaseInlineFormSet.save_new(self, form, commit=commit)


class PrivateImageInput(forms.ClearableFileInput):
    """A file input that never asks the storage for a URL.

    Originals live in `private_storage`, which raises on `url()` on purpose:
    nginx does not serve those files and a public looking address would be a
    lie. The stock widget links to the current file, so every change page of a
    work that had a photo answered with ValueError. The photo is already on
    screen in the `preview` column, through its public rendition.
    """

    def is_initial(self, value: Any) -> bool:
        return False


class WorkImageInline(SortableInlineAdminMixin, TabularInline):
    model = WorkImage
    formset = WorkImageInlineFormSet
    extra = 1
    fields = ("image", "preview", "alt_uk", "alt_ru", "is_main")
    readonly_fields = ("preview",)
    formfield_overrides = {models.ImageField: {"widget": PrivateImageInput}}

    @admin.display(description=_("preview"))
    def preview(self, obj: WorkImage) -> str:
        url = _thumbnail(obj)
        if not url:
            return "—"
        return format_html('<img src="{}" alt="" style="height:72px;border-radius:4px">', url)


@admin.register(Work)
class WorkAdmin(SortableAdminBase, ModelAdmin):
    list_display = ("thumbnail", "article", "title_uk", "status", "occasion_list", "views_count")
    list_display_links = ("thumbnail", "article", "title_uk")
    list_filter = ("status", "is_pinned", "occasions", "tags")
    search_fields = ("title_uk", "title_ru", "composition_uk", "composition_ru")
    readonly_fields = ("article", "slug", "views_count", "created_at", "updated_at")
    inlines = [WorkImageInline]
    actions = ["publish", "archive", "pin", "regenerate_photos"]
    # Changelist button, for the moment after the watermark changed.
    actions_list = ["regenerate_every_photo"]
    # Checkboxes rather than a horizontal filter: the owner fills this in on a
    # phone, and the sets are small.
    formfield_overrides = {models.ManyToManyField: {"widget": forms.CheckboxSelectMultiple}}
    list_per_page = 30

    fieldsets = (
        (
            _("Content"),
            {
                "fields": (
                    "article",
                    "slug",
                    "title_uk",
                    "title_ru",
                    "description_uk",
                    "description_ru",
                    "composition_uk",
                    "composition_ru",
                    "size_text_uk",
                    "size_text_ru",
                )
            },
        ),
        (_("Occasions and tags"), {"fields": ("occasions", "tags")}),
        (
            _("Prices"),
            {
                "fields": (
                    "price_from",
                    "price_to",
                    "price_visible",
                    "price_note_uk",
                    "price_note_ru",
                )
            },
        ),
        (
            _("Cost"),
            {
                "classes": ("collapse",),
                "description": _("Internal. It is never shown on the site."),
                "fields": ("cost",),
            },
        ),
        (
            _("Publication"),
            {"fields": ("status", "is_pinned", "order", "published_at", "views_count")},
        ),
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

    def get_queryset(self, request: HttpRequest) -> QuerySet[Work]:
        return super().get_queryset(request).prefetch_related("occasions", "images__renditions")

    def get_search_results(
        self, request: HttpRequest, queryset: QuerySet[Work], search_term: str
    ) -> tuple[QuerySet[Work], bool]:
        """Text search over the titles, plus the article typed in any shape."""
        results, may_have_duplicates = super().get_search_results(request, queryset, search_term)
        digits = re.sub(r"\D", "", search_term)
        if digits:
            results = results | queryset.filter(article=int(digits))
        return results, may_have_duplicates

    @admin.display(description=_("photo"))
    def thumbnail(self, obj: Work) -> str:
        url = _thumbnail(obj.main_image)
        if not url:
            return "—"
        return format_html('<img src="{}" alt="" style="height:56px;border-radius:4px">', url)

    @admin.display(description=_("occasions"))
    def occasion_list(self, obj: Work) -> str:
        return ", ".join(occasion.name_uk for occasion in obj.occasions.all()) or "—"

    def save_related(self, request: HttpRequest, form: Any, formsets: Any, change: bool) -> None:
        super().save_related(request, form, formsets, change)

        work = form.instance
        if work.status == Work.Status.PUBLISHED and not work.images.exists():
            # Backstop for the paths that carry no inline formset at all.
            Work.objects.filter(pk=work.pk).update(status=Work.Status.DRAFT, published_at=None)
            self.message_user(
                request,
                _("A work without photos cannot be published, so it was saved as a draft."),
                level=messages.WARNING,
            )

    @admin.action(description=_("Publish the selected works"))
    def publish(self, request: HttpRequest, queryset: QuerySet[Work]) -> None:
        published, skipped = 0, 0
        for work in queryset:
            if not work.images.exists():
                skipped += 1
                continue
            work.status = Work.Status.PUBLISHED
            work.save()
            published += 1

        self.message_user(
            request,
            ngettext("%(count)d work published.", "%(count)d works published.", published)
            % {"count": published},
            level=messages.SUCCESS if published else messages.WARNING,
        )
        if skipped:
            self.message_user(
                request,
                ngettext(
                    "%(count)d work has no photo and stayed a draft.",
                    "%(count)d works have no photo and stayed drafts.",
                    skipped,
                )
                % {"count": skipped},
                level=messages.WARNING,
            )

    @admin.action(description=_("Move the selected works to the archive"))
    def archive(self, request: HttpRequest, queryset: QuerySet[Work]) -> None:
        updated = queryset.update(status=Work.Status.ARCHIVED)
        self.message_user(
            request,
            ngettext("%(count)d work archived.", "%(count)d works archived.", updated)
            % {"count": updated},
        )

    @admin.action(description=_("Pin the selected works"))
    def pin(self, request: HttpRequest, queryset: QuerySet[Work]) -> None:
        updated = queryset.update(is_pinned=True)
        self.message_user(
            request,
            ngettext("%(count)d work pinned.", "%(count)d works pinned.", updated)
            % {"count": updated},
        )

    @admin.action(description=_("Rebuild the photos of the selected works"))
    def regenerate_photos(self, request: HttpRequest, queryset: QuerySet[Work]) -> None:
        for work_id in queryset.values_list("pk", flat=True):
            regenerate_all_renditions.apply_async(
                kwargs={"payload": {"force": True, "work_id": work_id}}, queue="media"
            )
        self.message_user(request, _("The photos are being rebuilt in the background."))

    @unfold_action(description=_("Rebuild every photo"), url_path="regenerate-renditions")
    def regenerate_every_photo(self, request: HttpRequest) -> HttpResponse:
        """Used after the watermark changed: file names carry the version, so
        the new images reach visitors through the CDN."""
        regenerate_all_renditions.apply_async(kwargs={"payload": {"force": True}}, queue="media")
        messages.info(request, _("Every photo is being rebuilt in the background."))
        return redirect(reverse("admin:catalog_work_changelist"))


@admin.register(Occasion)
class OccasionAdmin(SortableAdminMixin, ModelAdmin):
    list_display = ("name_uk", "slug", "is_active", "show_on_home")
    list_filter = ("is_active", "show_on_home")
    search_fields = ("slug", "name_uk", "name_ru")
    prepopulated_fields = {"slug": ("name_uk",)}
    fieldsets = (
        (None, {"fields": ("slug", "is_active", "show_on_home", "cover")}),
        (
            _("Content"),
            {"fields": ("name_uk", "name_ru", "description_uk", "description_ru")},
        ),
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


class TagInline(SortableInlineAdminMixin, TabularInline):
    model = Tag
    extra = 1
    fields = ("name_uk", "name_ru", "slug", "color_hex", "is_active")
    prepopulated_fields = {"slug": ("name_uk",)}


@admin.register(TagGroup)
class TagGroupAdmin(SortableAdminMixin, ModelAdmin):
    list_display = ("name_uk", "slug", "filter_kind", "is_active")
    list_filter = ("filter_kind", "is_active")
    search_fields = ("slug", "name_uk", "name_ru")
    inlines = [TagInline]


@admin.register(Tag)
class TagAdmin(SortableAdminMixin, ModelAdmin):
    list_display = ("name_uk", "slug", "group", "color_hex", "is_active")
    list_filter = ("group", "is_active")
    search_fields = ("slug", "name_uk", "name_ru")
    prepopulated_fields = {"slug": ("name_uk",)}

from __future__ import annotations

from django.contrib import admin
from django.http import HttpRequest
from unfold.admin import ModelAdmin, TabularInline

from apps.stores.models import Store, StorePhoto


class StorePhotoInline(TabularInline):
    model = StorePhoto
    extra = 1
    fields = ("image", "sort_order")


@admin.register(Store)
class StoreAdmin(ModelAdmin):
    list_display = ("name", "slug", "phone", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name", "address", "phone")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [StorePhotoInline]

    def has_delete_permission(self, request: HttpRequest, obj: Store | None = None) -> bool:
        return request.user.is_superuser

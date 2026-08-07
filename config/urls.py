from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path

urlpatterns: list[URLResolver | URLPattern] = [
    path("manage/", admin.site.urls),
    path("healthz/", include("health_check.urls")),
    path("api/v1/stores/", include("apps.stores.api_urls")),
    path("", include("apps.pages.urls")),
    path("stores/", include("apps.stores.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

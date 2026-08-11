from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path

from apps.core import views as core_views

urlpatterns: list[URLPattern | URLResolver] = [
    path("admin/", admin.site.urls),
    path("tinymce/", include("tinymce.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
]

localized = [
    path("", core_views.home, name="home"),
    # Registered always, answers only while DEBUG is on: the view checks.
    path("kitchen-sink/", core_views.kitchen_sink, name="kitchen_sink"),
    # Stays last: it matches any single segment, so every new URL must be
    # declared above it.
    path("<slug:slug>/", core_views.static_page, name="static_page"),
]

urlpatterns += i18n_patterns(*localized, prefix_default_language=False)

if settings.DEBUG:
    # Public media only. The private storage has no URL mapping anywhere.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

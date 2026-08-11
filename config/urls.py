from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path

from apps.catalog import views as catalog_views
from apps.core import views as core_views
from apps.leads import views as lead_views

urlpatterns: list[URLPattern | URLResolver] = [
    # Ahead of the admin site: it owns the prefix, not this address.
    path("admin/upload-image/", core_views.upload_image, name="upload_image"),
    path("admin/", admin.site.urls),
    path("tinymce/", include("tinymce.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
]

localized = [
    path("", core_views.home, name="home"),
    path("galereya/", catalog_views.gallery, name="gallery"),
    path("galereya/<slug:occasion_slug>/", catalog_views.gallery, name="gallery_occasion"),
    path("robota/<slug:slug>/", catalog_views.work_detail, name="work_detail"),
    path("poshuk/", catalog_views.search, name="search"),
    path("obrane/", catalog_views.favorites, name="favorites"),
    path("kontakty/", core_views.contacts, name="contacts"),
    path("dyakuyemo/", lead_views.thanks, name="thanks"),
    # Fragments. Closed to crawlers by robots.txt, noindex in the markup.
    path("hx/gallery/", catalog_views.hx_gallery, name="hx_gallery"),
    path("hx/lead/", lead_views.hx_lead, name="hx_lead"),
    path("hx/favorites/", catalog_views.hx_favorites, name="hx_favorites"),
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

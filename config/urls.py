from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps import views as sitemap_views
from django.urls import URLPattern, URLResolver, include, path

from apps.blog import views as blog_views
from apps.catalog import views as catalog_views
from apps.core import views as core_views
from apps.core.sitemaps import SITEMAPS
from apps.leads import views as lead_views
from apps.reviews import views as review_views

urlpatterns: list[URLPattern | URLResolver] = [
    # Ahead of the admin site: it owns the prefix, not this address.
    path("admin/upload-image/", core_views.upload_image, name="upload_image"),
    path("admin/", admin.site.urls),
    path("tinymce/", include("tinymce.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    # Outside i18n_patterns: a crawler looks for these at the root, and the
    # sitemap itself carries an entry per language.
    path(
        "sitemap.xml",
        sitemap_views.index,
        {"sitemaps": SITEMAPS, "sitemap_url_name": "sitemap_section"},
        name="sitemap",
    ),
    path(
        "sitemap-<section>.xml",
        sitemap_views.sitemap,
        {"sitemaps": SITEMAPS},
        name="sitemap_section",
    ),
    path("robots.txt", core_views.robots_txt, name="robots_txt"),
]

localized = [
    path("", core_views.home, name="home"),
    path("galereya/", catalog_views.gallery, name="gallery"),
    path("galereya/<slug:occasion_slug>/", catalog_views.gallery, name="gallery_occasion"),
    path("robota/<slug:slug>/", catalog_views.work_detail, name="work_detail"),
    path("poshuk/", catalog_views.search, name="search"),
    path("obrane/", catalog_views.favorites, name="favorites"),
    path("kontakty/", core_views.contacts, name="contacts"),
    path("vidhuky/", review_views.review_list, name="review_list"),
    path("blog/", blog_views.post_list, name="post_list"),
    path("blog/<slug:slug>/", blog_views.post_detail, name="post_detail"),
    path("dyakuyemo/", lead_views.thanks, name="thanks"),
    # Fragments. Closed to crawlers by robots.txt, noindex in the markup.
    path("hx/gallery/", catalog_views.hx_gallery, name="hx_gallery"),
    path("hx/lead/", lead_views.hx_lead, name="hx_lead"),
    path("hx/favorites/", catalog_views.hx_favorites, name="hx_favorites"),
    path("hx/review/", review_views.hx_review, name="hx_review"),
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

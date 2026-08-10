from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("tinymce/", include("tinymce.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
]

urlpatterns += i18n_patterns(prefix_default_language=False)

if settings.DEBUG:
    # Public media only. The private storage has no URL mapping anywhere.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

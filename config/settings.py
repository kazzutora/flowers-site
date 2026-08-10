"""Django settings, assembled from the validated environment schema."""

from pathlib import Path
from urllib.parse import unquote, urlsplit

from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _
from pydantic import ValidationError

from config.settings_schema import Settings

BASE_DIR = Path(__file__).resolve().parent.parent


def _explain(exc: ValidationError) -> str:
    problems = "\n".join(
        "  {}: {}".format(".".join(str(part) for part in error["loc"]).upper(), error["msg"])
        for error in exc.errors()
    )
    return f"Invalid environment configuration:\n{problems}\n\nCompare your .env with .env.example."


try:
    ENV = Settings()
except ValidationError as exc:  # start-up must fail loudly, not at request time
    raise ImproperlyConfigured(_explain(exc)) from exc


# --- core ---------------------------------------------------------------------

SECRET_KEY = ENV.secret_key.get_secret_value()
DEBUG = ENV.debug
ALLOWED_HOSTS = ENV.allowed_hosts
SITE_URL = str(ENV.site_url).rstrip("/")
CSRF_TRUSTED_ORIGINS = [SITE_URL]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

INSTALLED_APPS = [
    # unfold must precede django.contrib.admin: it overrides admin templates
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "adminsortable2",
    "phonenumber_field",
    "tinymce",
    "apps.core",
    "apps.catalog",
    "apps.leads",
    "apps.reviews",
    "apps.blog",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# --- database, cache ----------------------------------------------------------

_db = urlsplit(str(ENV.database_url))
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(_db.path.lstrip("/")),
        "USER": unquote(_db.username or ""),
        "PASSWORD": unquote(_db.password or ""),
        "HOST": _db.hostname or "",
        "PORT": str(_db.port or ""),
        "CONN_MAX_AGE": 60,
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": str(ENV.redis_url),
        # Short timeouts: an unreachable Redis degrades to a direct read, it
        # must not hold a request open.
        "OPTIONS": {"socket_connect_timeout": 1, "socket_timeout": 1},
    }
}


# --- i18n ---------------------------------------------------------------------

LANGUAGE_CODE = "uk"
LANGUAGES = [("uk", _("Ukrainian")), ("ru", _("Russian"))]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = ENV.time_zone
USE_TZ = ENV.use_tz
USE_I18N = True


# --- static and media ---------------------------------------------------------

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media" / "public"
MEDIA_PRIVATE_ROOT = BASE_DIR / "media" / "private"

if ENV.media_backend == "s3":
    _s3_options = {
        "bucket_name": ENV.s3_bucket,
        "endpoint_url": ENV.s3_endpoint_url,
        "access_key": ENV.s3_access_key.get_secret_value() if ENV.s3_access_key else None,
        "secret_key": ENV.s3_secret_key.get_secret_value() if ENV.s3_secret_key else None,
    }
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {**_s3_options, "location": "public", "default_acl": "public-read"},
        },
        "private": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {**_s3_options, "location": "private", "default_acl": "private"},
        },
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
            "OPTIONS": {"location": MEDIA_ROOT, "base_url": MEDIA_URL},
        },
        # Never served over HTTP: nginx does not map it and urls.py does not
        # expose it, not even under DEBUG.
        "private": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
            "OPTIONS": {"location": MEDIA_PRIVATE_ROOT},
        },
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }


# --- security -----------------------------------------------------------------

X_FRAME_OPTIONS = "DENY"

if not DEBUG:
    SECURE_HSTS_SECONDS = 31_536_000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --- third party --------------------------------------------------------------

PHONENUMBER_DEFAULT_REGION = "UA"
PHONENUMBER_DEFAULT_FORMAT = "E164"

UNFOLD = {
    "SITE_TITLE": _("Flower studio"),
    "SITE_HEADER": _("Flower studio"),
    "SHOW_HISTORY": True,
}

TINYMCE_DEFAULT_CONFIG = {
    "menubar": False,
    "plugins": "lists link table code",
    "toolbar": (
        "undo redo | blocks | bold italic underline | bullist numlist | "
        "link table | removeformat | code"
    ),
    "block_formats": "Paragraph=p; Heading 2=h2; Heading 3=h3; Heading 4=h4",
    "width": "100%",
    "height": 480,
    "convert_urls": False,
    "browser_spellcheck": True,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "{levelname} {name} {message}", "style": "{"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "simple"}},
    "loggers": {"django": {"handlers": ["console"], "level": "INFO", "propagate": False}},
    "root": {"handlers": ["console"], "level": "INFO"},
}

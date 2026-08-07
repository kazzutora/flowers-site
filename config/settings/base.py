"""Shared settings. Never imported directly — always via local/prod/test."""

from pathlib import Path

from config.settings.env import settings

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = settings.secret_key
DEBUG = settings.debug
ALLOWED_HOSTS = settings.allowed_hosts
CSRF_TRUSTED_ORIGINS = settings.csrf_trusted_origins
SITE_URL = settings.site_url

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django_celery_beat",
    "health_check",
    "health_check.db",
    "health_check.cache",
    "health_check.contrib.celery",
    "apps.common",
    "apps.pages",
    "apps.stores",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.pages.context_processors.header_data",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": settings.postgres_db,
        "USER": settings.postgres_user,
        "PASSWORD": settings.postgres_password,
        "HOST": settings.postgres_host,
        "PORT": settings.postgres_port,
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": settings.redis_cache_url,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    },
    "sessions": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": settings.redis_sessions_url,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    },
}
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "sessions"

# --- Celery (tech.md §7) -------------------------------------------------
CELERY_BROKER_URL = settings.redis_celery_url
CELERY_RESULT_BACKEND = settings.redis_celery_url
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_TIMEZONE = settings.time_zone
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# --- External providers, read by apps/*/clients/factory.py ---------------
PAYMENT_PROVIDER = settings.payment_provider
SMS_PROVIDER = settings.sms_provider
MESSENGER_PROVIDER = settings.messenger_provider
STREAM_PROVIDER = settings.stream_provider

# --- Email -----------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = settings.email_host
EMAIL_PORT = settings.email_port
EMAIL_USE_TLS = settings.email_use_tls
DEFAULT_FROM_EMAIL = settings.default_from_email

# --- i18n / tz — one language live in v1, infra ready for a second (tech.md §1)
LANGUAGE_CODE = settings.language_code
TIME_ZONE = settings.time_zone
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "mediafiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# django.contrib.staticfiles + WhiteNoise serve uploaded media type sniffing
# safely; catalog storage never executes anything (tech.md §10.3).
SECURE_CONTENT_TYPE_NOSNIFF = True

DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

# --- Admin lives off the beaten path (tech.md §10.5) ----------------------
UNFOLD = {
    "SITE_TITLE": "Квіти — адмін",
    "SITE_HEADER": "Квіти",
}

HEALTH_CHECK = {
    "DISABLE_ERROR_MESSAGES": False,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

SENTRY_DSN = settings.sentry_dsn

if settings.sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration

    from apps.common.observability import scrub_sensitive_event

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        send_default_pii=False,
        before_send=scrub_sensitive_event,
    )

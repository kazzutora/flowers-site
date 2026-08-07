from config.settings.base import *  # noqa: F403
from config.settings.base import BASE_DIR

DEBUG = False

# Task bodies run synchronously so idempotency-key assertions don't need a
# live worker process; the Redis SETNX guard behaves identically either way.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
MEDIA_ROOT = BASE_DIR / "test_media"

# Plain (non-manifest) static storage: tests render templates with
# {% static %} but shouldn't need a `collectstatic` manifest as a
# prerequisite for running the suite.
STORAGES["staticfiles"]["BACKEND"] = (  # noqa: F405
    "django.contrib.staticfiles.storage.StaticFilesStorage"
)

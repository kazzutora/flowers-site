"""tech.md §10.1 — copied verbatim, not open to per-deploy tuning."""

from config.settings.base import *  # noqa: F403
from config.settings.env import settings

DEBUG = False

SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# --- Media moves to S3-compatible storage in prod (tech.md §2) -----------
STORAGES["default"]["BACKEND"] = "storages.backends.s3boto3.S3Boto3Storage"  # noqa: F405
AWS_STORAGE_BUCKET_NAME = settings.aws_storage_bucket_name
AWS_S3_ENDPOINT_URL = settings.aws_s3_endpoint_url
AWS_ACCESS_KEY_ID = settings.aws_access_key_id
AWS_SECRET_ACCESS_KEY = settings.aws_secret_access_key
AWS_S3_REGION_NAME = settings.aws_s3_region_name
AWS_DEFAULT_ACL = None
AWS_S3_FILE_OVERWRITE = False

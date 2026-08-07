"""Typed environment access — tech.md §6.1.

The only module in the project allowed to read process environment
variables. Every other module (``base.py``, ``local.py``, ``prod.py``,
``test.py``, service code, tasks) reads configuration through the
``settings`` singleton defined here, never through ``os.getenv``.

The two exceptions are ``manage.py``, ``config/wsgi.py`` and
``config/celery.py`` setting ``DJANGO_SETTINGS_MODULE`` via
``os.environ.setdefault`` — that variable selects *which* settings module
to import and must be readable before this module (or Django) exists, so
it cannot be routed through ``Settings`` without a chicken-and-egg problem.

``Settings()`` is instantiated at import time. A missing required variable
raises ``pydantic.ValidationError`` immediately on import — i.e. at process
startup — instead of surfacing as an obscure ``KeyError``/``AttributeError``
deep in a request an hour into production.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
    )

    # --- Core Django -------------------------------------------------
    secret_key: str
    debug: bool = False
    # NoDecode: pydantic-settings otherwise tries to JSON-decode list-typed
    # fields before validators run, which rejects a plain CSV env value.
    allowed_hosts: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1"]
    )
    csrf_trusted_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)
    site_url: str = "http://localhost:8000"

    # --- Database ------------------------------------------------------
    postgres_db: str = "flowers"
    postgres_user: str = "flowers"
    postgres_password: str
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    # --- Redis: db0 cache, db1 sessions, db2 celery broker/result (tech.md §7)
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_cache_db: int = 0
    redis_sessions_db: int = 1
    redis_celery_db: int = 2

    # --- Email (mailhog locally) ---------------------------------------
    email_host: str = "mailhog"
    email_port: int = 1025
    email_use_tls: bool = False
    default_from_email: str = "noreply@flowers.local"

    # --- External service providers, selected by factory (tech.md §9.1) -
    payment_provider: Literal["fake", "liqpay", "mono", "wayforpay"] = "fake"
    sms_provider: str = "fake"
    messenger_provider: str = "fake"
    stream_provider: Literal["fake", "mediamtx", "youtube", "external"] = "fake"

    # --- Observability ---------------------------------------------------
    sentry_dsn: str | None = None
    sentry_environment: str = "local"
    sentry_traces_sample_rate: float = 0.0

    # --- Object storage, prod only (S3-compatible, tech.md §2) ----------
    aws_storage_bucket_name: str | None = None
    aws_s3_endpoint_url: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_s3_region_name: str | None = None

    # --- Fixed by product decision, not meant to vary per environment ---
    time_zone: str = "Europe/Kyiv"
    language_code: str = "uk"

    @field_validator("allowed_hosts", "csrf_trusted_origins", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def redis_cache_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_cache_db}"

    @property
    def redis_sessions_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_sessions_db}"

    @property
    def redis_celery_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_celery_db}"


settings = Settings()

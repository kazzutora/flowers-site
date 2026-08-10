"""The only place in the project that reads environment variables.

`os.environ` and `os.getenv` are banned everywhere else: a single typed schema
makes a missing or malformed variable fail on start-up instead of at request
time.
"""

import json
from typing import Annotated, Any, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AnyHttpUrl, PostgresDsn, RedisDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # core
    secret_key: SecretStr
    debug: bool = False
    # NoDecode keeps pydantic-settings from JSON-parsing the raw value, so the
    # validator below sees "a.com, b.com" instead of a source error.
    allowed_hosts: Annotated[list[str], NoDecode] = ["localhost"]
    site_url: AnyHttpUrl
    time_zone: str = "Europe/Kyiv"
    use_tz: bool = True

    # db / redis / celery
    database_url: PostgresDsn
    redis_url: RedisDsn
    celery_broker_url: RedisDsn
    celery_result_backend: RedisDsn

    # telegram
    telegram_bot_token: SecretStr | None = None
    telegram_chat_id: str | None = None
    telegram_enabled: bool = False  # False -> fake client

    # turnstile
    turnstile_site_key: str | None = None
    turnstile_secret_key: SecretStr | None = None
    turnstile_enabled: bool = False  # False -> verifier accepts everything

    # antispam
    lead_rate_per_ip_hour: int = 5
    lead_rate_global_day: int = 20
    review_rate_per_ip_hour: int = 2
    review_rate_global_day: int = 20
    form_min_fill_seconds: int = 3
    ip_hash_salt: SecretStr

    # media
    media_backend: Literal["local", "s3"] = "local"
    s3_bucket: str | None = None
    s3_endpoint_url: str | None = None
    s3_access_key: SecretStr | None = None
    s3_secret_key: SecretStr | None = None

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def split_hosts(cls, v: Any) -> Any:
        # A JSON list is what pydantic-settings expects for list[str]; a comma
        # separated string is what people actually write in .env files.
        if isinstance(v, str):
            text = v.strip()
            if text.startswith("["):
                try:
                    return json.loads(text)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        "expected a JSON list or a comma separated string"
                    ) from exc
            return [host.strip() for host in text.split(",") if host.strip()]
        return v

    @field_validator("time_zone")
    @classmethod
    def known_time_zone(cls, v: str) -> str:
        try:
            ZoneInfo(v)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"unknown time zone: {v!r}") from exc
        return v

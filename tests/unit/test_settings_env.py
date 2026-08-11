"""S0.2 acceptance — config/settings/env.py.

"Удаление обязательной переменной валит старт приложения с внятным
сообщением, а не падает через час в рантайме": a missing required variable
must raise at construction (which happens at import time, since the module
instantiates ``Settings()`` at module scope), and declared defaults must
carry the types the rest of the settings modules assume.

Every test builds ``Settings`` explicitly rather than importing the module
singleton, so the developer's own ``.env`` and shell never decide the
outcome.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from config.settings.env import Settings

REQUIRED_KEYS = ("SECRET_KEY", "POSTGRES_PASSWORD")
MINIMAL_ENV = {"SECRET_KEY": "test-secret-key", "POSTGRES_PASSWORD": "test-password"}


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """Strip every settings variable from the ambient environment."""
    for field_name in Settings.model_fields:
        monkeypatch.delenv(field_name.upper(), raising=False)
    return monkeypatch


def _build(**overrides: str) -> Settings:
    # _env_file=None: read the passed values only, never the repo's .env.
    return Settings(_env_file=None, **{**MINIMAL_ENV, **overrides})  # type: ignore[arg-type]


@pytest.mark.parametrize("missing", REQUIRED_KEYS)
def test_missing_required_variable_raises_validation_error(
    clean_env: pytest.MonkeyPatch, missing: str
) -> None:
    present = {key: value for key, value in MINIMAL_ENV.items() if key != missing}

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None, **present)  # type: ignore[arg-type]

    # "Внятное сообщение": the report has to name the variable that is missing.
    message = str(exc_info.value)
    assert missing.lower() in message
    assert "required" in message.lower()


def test_defaults_are_correctly_typed(clean_env: pytest.MonkeyPatch) -> None:
    settings = _build()

    assert settings.debug is False
    assert settings.postgres_port == 5432
    assert isinstance(settings.postgres_port, int)
    # tech.md §7: db0 cache, db1 sessions, db2 celery broker/result.
    assert (settings.redis_cache_db, settings.redis_sessions_db, settings.redis_celery_db) == (
        0,
        1,
        2,
    )
    assert settings.time_zone == "Europe/Kyiv"
    assert settings.language_code == "uk"
    # Every provider defaults to its fake, so the app boots with no real secret.
    assert settings.payment_provider == "fake"
    assert settings.stream_provider == "fake"
    assert settings.sentry_dsn is None
    assert settings.allowed_hosts == ["localhost", "127.0.0.1"]


def test_redis_urls_select_the_documented_databases(clean_env: pytest.MonkeyPatch) -> None:
    settings = _build(REDIS_HOST="redis", REDIS_PORT="6379")

    assert settings.redis_cache_url == "redis://redis:6379/0"
    assert settings.redis_sessions_url == "redis://redis:6379/1"
    assert settings.redis_celery_url == "redis://redis:6379/2"


def test_csv_list_variables_are_split(clean_env: pytest.MonkeyPatch) -> None:
    settings = _build(
        ALLOWED_HOSTS="example.com, www.example.com ,",
        CSRF_TRUSTED_ORIGINS="https://example.com",
    )

    assert settings.allowed_hosts == ["example.com", "www.example.com"]
    assert settings.csrf_trusted_origins == ["https://example.com"]


def test_unknown_variable_is_rejected(clean_env: pytest.MonkeyPatch) -> None:
    """extra="forbid" is the typo guard — SECRET_KEYY must not pass silently."""
    with pytest.raises(ValidationError):
        _build(SECRET_KEYY="typo")


def test_compose_only_keys_in_env_file_do_not_break_startup(
    clean_env: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """docker compose and Django read the same ``.env``.

    deploy.yml rewrites ``IMAGE`` in the server's .env on every release and
    deploy/README.md has the operator add ``SITE_DOMAIN``. Under
    extra="forbid" an undeclared key there stops the container at startup,
    so these have to stay declared fields.
    """
    env_file = tmp_path / ".env"
    env_file.write_text(
        "SECRET_KEY=test-secret-key\n"
        "POSTGRES_PASSWORD=test-password\n"
        "SITE_DOMAIN=test.example\n"
        "IMAGE=ghcr.io/kazzutora/flowers-site:abc123\n"
        "POSTGRES_HOST_PORT=5433\n"
        "REDIS_HOST_PORT=6380\n",
        encoding="utf-8",
    )

    settings = Settings(_env_file=env_file)  # type: ignore[call-arg]

    assert settings.site_domain == "test.example"
    assert settings.image == "ghcr.io/kazzutora/flowers-site:abc123"
    assert settings.postgres_host_port == 5433
    assert settings.redis_host_port == 6380

"""Section 6 of tech.md: the environment schema is the only source of config."""

import importlib.util
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from config.settings_schema import Settings

ROOT = Path(__file__).resolve().parent.parent

MINIMAL: dict[str, Any] = {
    "secret_key": "x",
    "site_url": "http://localhost:8000",
    "database_url": "postgresql://u:p@db:5432/flowers",
    "redis_url": "redis://redis:6379/0",
    "celery_broker_url": "redis://redis:6379/1",
    "celery_result_backend": "redis://redis:6379/2",
    "ip_hash_salt": "salt",
}

HOSTS = st.lists(st.from_regex(r"[a-z0-9][a-z0-9.-]{0,20}", fullmatch=True), max_size=6)


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Hide the ambient environment so the schema is tested, not the container."""
    for name in Settings.model_fields:
        monkeypatch.delenv(name.upper(), raising=False)
        monkeypatch.delenv(name, raising=False)


def build(**overrides: Any) -> Settings:
    return Settings(_env_file=None, **{**MINIMAL, **overrides})  # type: ignore[arg-type]


def test_incomplete_environment_is_rejected(clean_env: None) -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)  # type: ignore[call-arg]

    missing = {error["loc"][0] for error in exc_info.value.errors()}
    assert missing == {
        "secret_key",
        "site_url",
        "database_url",
        "redis_url",
        "celery_broker_url",
        "celery_result_backend",
        "ip_hash_salt",
    }


def test_defaults_follow_the_contract(clean_env: None) -> None:
    settings = build()

    assert settings.time_zone == "Europe/Kyiv"
    assert settings.use_tz is True
    assert settings.debug is False
    assert settings.allowed_hosts == ["localhost"]
    assert settings.telegram_enabled is False
    assert settings.turnstile_enabled is False
    assert settings.media_backend == "local"
    assert settings.lead_rate_per_ip_hour == 5
    assert settings.lead_rate_global_day == 20
    assert settings.review_rate_per_ip_hour == 2
    assert settings.review_rate_global_day == 20
    assert settings.form_min_fill_seconds == 3


def test_allowed_hosts_read_from_a_comma_separated_variable(
    clean_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    for key, value in MINIMAL.items():
        monkeypatch.setenv(key.upper(), str(value))
    monkeypatch.setenv("ALLOWED_HOSTS", "a.com, b.com")

    assert Settings(_env_file=None).allowed_hosts == ["a.com", "b.com"]  # type: ignore[call-arg]


def test_allowed_hosts_read_from_a_json_variable(
    clean_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    for key, value in MINIMAL.items():
        monkeypatch.setenv(key.upper(), str(value))
    monkeypatch.setenv("ALLOWED_HOSTS", '["a.com", "b.com"]')

    assert Settings(_env_file=None).allowed_hosts == ["a.com", "b.com"]  # type: ignore[call-arg]


@given(hosts=HOSTS, padding=st.integers(min_value=0, max_value=4))
def test_allowed_hosts_ignore_whitespace_and_empty_elements(hosts: list[str], padding: int) -> None:
    spaces = " " * padding
    raw = ",".join(f"{spaces}{host}{spaces}" for host in hosts) + "," * padding

    assert build(allowed_hosts=raw).allowed_hosts == hosts


def test_unknown_time_zone_is_rejected(clean_env: None) -> None:
    with pytest.raises(ValidationError):
        build(time_zone="Mars/Olympus")


def test_secrets_are_not_printable(clean_env: None) -> None:
    settings = build(secret_key="super-secret")

    assert "super-secret" not in repr(settings)
    assert settings.secret_key.get_secret_value() == "super-secret"


def _load_settings_with(monkeypatch: pytest.MonkeyPatch, **env: str) -> Any:
    """Execute config/settings.py in a private module, leaving the live one alone."""
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    spec = importlib.util.spec_from_file_location("settings_probe", ROOT / "config" / "settings.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_production_settings_are_hardened(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _load_settings_with(monkeypatch, DEBUG="False")

    assert settings.SECURE_HSTS_SECONDS == 31_536_000
    assert settings.SESSION_COOKIE_SECURE is True
    assert settings.CSRF_COOKIE_SECURE is True
    assert settings.SECURE_SSL_REDIRECT is True
    assert settings.X_FRAME_OPTIONS == "DENY"
    assert settings.TIME_ZONE == "Europe/Kyiv"
    assert settings.USE_TZ is True


def test_broken_environment_stops_the_process(monkeypatch: pytest.MonkeyPatch) -> None:
    from django.core.exceptions import ImproperlyConfigured

    with pytest.raises(ImproperlyConfigured) as exc_info:
        _load_settings_with(monkeypatch, DATABASE_URL="not-a-dsn")

    assert "DATABASE_URL" in str(exc_info.value)

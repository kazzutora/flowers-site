"""Section 7: the fakes are the default and they validate like the real thing."""

from typing import Any

import pytest
from pydantic import ValidationError

from apps.core.exceptions import TransientError
from clients.base import ClientError
from clients.dto import TelegramMessage
from clients.factory import get_telegram_client, get_turnstile_verifier
from clients.fakes import FakeTelegramClient, FakeTurnstileVerifier
from clients.telegram import RealTelegramClient
from clients.turnstile import RealTurnstileVerifier


@pytest.fixture
def telegram() -> FakeTelegramClient:
    client = FakeTelegramClient()
    client.reset()
    return client


def test_disabled_telegram_gives_the_fake(settings: Any, monkeypatch: Any) -> None:
    monkeypatch.setattr(settings.ENV, "telegram_enabled", False)

    assert isinstance(get_telegram_client(), FakeTelegramClient)


def test_enabled_telegram_gives_the_real_client(settings: Any, monkeypatch: Any) -> None:
    from pydantic import SecretStr

    monkeypatch.setattr(settings.ENV, "telegram_enabled", True)
    monkeypatch.setattr(settings.ENV, "telegram_bot_token", SecretStr("123:abc"))

    assert isinstance(get_telegram_client(), RealTelegramClient)


def test_disabled_turnstile_accepts_everything(settings: Any) -> None:
    verifier = get_turnstile_verifier()

    assert isinstance(verifier, FakeTurnstileVerifier)
    assert verifier.verify("anything", None).success is True


def test_enabled_turnstile_gives_the_real_verifier(settings: Any, monkeypatch: Any) -> None:
    from pydantic import SecretStr

    monkeypatch.setattr(settings.ENV, "turnstile_enabled", True)
    monkeypatch.setattr(settings.ENV, "turnstile_secret_key", SecretStr("secret"))

    assert isinstance(get_turnstile_verifier(), RealTurnstileVerifier)


def test_fake_records_what_it_was_given(telegram: FakeTelegramClient) -> None:
    result = telegram.send_message(TelegramMessage(chat_id="1", text="Нова заявка"))

    assert result.ok is True
    assert [message.text for message in telegram.sent] == ["Нова заявка"]


def test_message_longer_than_the_limit_never_reaches_the_network(
    telegram: FakeTelegramClient,
) -> None:
    with pytest.raises(ValidationError):
        telegram.send_message({"chat_id": "1", "text": "x" * 4097})  # type: ignore[arg-type]

    assert telegram.sent == []


def test_junk_input_blows_up_in_the_fake(telegram: FakeTelegramClient) -> None:
    with pytest.raises(ValidationError):
        telegram.send_message({"text": "no chat id"})  # type: ignore[arg-type]


def test_server_error_is_transient(telegram: FakeTelegramClient) -> None:
    telegram.fail_with(500)

    with pytest.raises(TransientError):
        telegram.send_message(TelegramMessage(chat_id="1", text="hi"))

    assert telegram.sent == []


def test_client_error_is_permanent(telegram: FakeTelegramClient) -> None:
    telegram.fail_with(400)

    with pytest.raises(ClientError):
        telegram.send_message(TelegramMessage(chat_id="1", text="hi"))


def test_timeout_is_transient(telegram: FakeTelegramClient) -> None:
    telegram.timeout()

    with pytest.raises(TransientError):
        telegram.send_message(TelegramMessage(chat_id="1", text="hi"))


def test_failing_turnstile_reports_error_codes() -> None:
    verifier = FakeTurnstileVerifier(success=False)

    result = verifier.verify("token", "127.0.0.1")

    assert result.success is False
    assert result.error_codes == ["invalid-input-response"]


def test_real_client_waits_ten_seconds_at_most() -> None:
    from clients import telegram as telegram_module
    from clients import turnstile as turnstile_module

    assert telegram_module.TIMEOUT_SECONDS == 10
    assert turnstile_module.TIMEOUT_SECONDS == 10

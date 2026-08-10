"""Which implementation the application talks to, decided by the config flags."""

from django.conf import settings

from clients.base import TelegramClient, TurnstileVerifier
from clients.fakes import FakeTelegramClient, FakeTurnstileVerifier
from clients.telegram import RealTelegramClient
from clients.turnstile import RealTurnstileVerifier

# Module level so a test can read what the application sent.
fake_telegram_client = FakeTelegramClient()
fake_turnstile_verifier = FakeTurnstileVerifier()


def get_telegram_client() -> TelegramClient:
    env = settings.ENV
    if not env.telegram_enabled or env.telegram_bot_token is None:
        return fake_telegram_client
    return RealTelegramClient(token=env.telegram_bot_token.get_secret_value())


def get_turnstile_verifier() -> TurnstileVerifier:
    env = settings.ENV
    if not env.turnstile_enabled or env.turnstile_secret_key is None:
        return fake_turnstile_verifier
    return RealTurnstileVerifier(secret_key=env.turnstile_secret_key.get_secret_value())


def telegram_chat_id() -> str:
    return settings.ENV.telegram_chat_id or "fake-chat"

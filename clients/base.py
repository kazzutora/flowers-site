from typing import Protocol

from clients.dto import TelegramMessage, TelegramSendResult, TurnstileResult


class ClientError(Exception):
    """Permanent failure of an external service: retrying cannot help."""


class TelegramClient(Protocol):
    def send_message(self, payload: TelegramMessage) -> TelegramSendResult: ...


class TurnstileVerifier(Protocol):
    def verify(self, token: str, remote_ip: str | None) -> TurnstileResult: ...

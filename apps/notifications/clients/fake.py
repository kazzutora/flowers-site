"""FakeSmsClient / FakeMessengerClient — tech.md §9.1, S0.7."""

from __future__ import annotations

from apps.notifications.clients.base import MessengerClient, SmsClient
from apps.notifications.clients.dto import SmsResult, SmsStatus
from apps.notifications.clients.errors import MessengerClientError, SmsClientError


class FakeSmsClient(SmsClient):
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.sent: list[tuple[str, str]] = []

    def send(self, phone: str, text: str) -> SmsResult:
        if self.fail:
            raise SmsClientError("fake SMS client: send failed")
        self.sent.append((phone, text))
        return SmsResult(message_id=f"fake-sms-{len(self.sent)}", status=SmsStatus.SENT)


class FakeMessengerClient(MessengerClient):
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.sent: list[tuple[str, str]] = []

    def send_message(self, chat_id: str, text: str) -> None:
        if self.fail:
            raise MessengerClientError("fake messenger client: send_message failed")
        self.sent.append((chat_id, text))

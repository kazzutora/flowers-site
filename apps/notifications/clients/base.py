"""tech.md §9.1 — frozen ABC signatures."""

from __future__ import annotations

from abc import ABC, abstractmethod

from apps.notifications.clients.dto import SmsResult


class SmsClient(ABC):
    @abstractmethod
    def send(self, phone: str, text: str) -> SmsResult: ...


class MessengerClient(ABC):
    @abstractmethod
    def send_message(self, chat_id: str, text: str) -> None: ...

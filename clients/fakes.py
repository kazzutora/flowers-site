"""In-process doubles used whenever the real integration is disabled.

The fakes validate their input with the same pydantic models as the real
clients, so code that sends junk fails here too, without a token and without a
network call.
"""

from apps.core.exceptions import TransientError
from clients.base import ClientError
from clients.dto import TelegramMessage, TelegramSendResult, TurnstileResult


class FakeTelegramClient:
    def __init__(self) -> None:
        self.sent: list[TelegramMessage] = []
        self._fail_status: int | None = None
        self._timeout = False

    def fail_with(self, status: int) -> None:
        self._fail_status = status
        self._timeout = False

    def timeout(self) -> None:
        self._timeout = True
        self._fail_status = None

    def reset(self) -> None:
        self.sent.clear()
        self._fail_status = None
        self._timeout = False

    def send_message(self, payload: TelegramMessage) -> TelegramSendResult:
        message = TelegramMessage.model_validate(payload)

        if self._timeout:
            raise TransientError("telegram timed out")
        if self._fail_status is not None:
            if self._fail_status >= 500:
                raise TransientError(f"telegram responded {self._fail_status}")
            raise ClientError(f"telegram rejected the message: {self._fail_status}")

        self.sent.append(message)
        return TelegramSendResult(ok=True, message_id=len(self.sent))


class FakeTurnstileVerifier:
    """Accepts every token unless told otherwise: local work needs no keys."""

    def __init__(self, success: bool = True) -> None:
        self.success = success
        self.tokens: list[str] = []

    def reset(self) -> None:
        self.success = True
        self.tokens.clear()

    def verify(self, token: str, remote_ip: str | None) -> TurnstileResult:
        self.tokens.append(token)
        if self.success:
            return TurnstileResult(success=True)
        return TurnstileResult(success=False, error_codes=["invalid-input-response"])

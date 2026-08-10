"""Telegram Bot API client.

urllib from the standard library, not an HTTP package: two POST requests do not
justify a dependency that is not in the stack table of tech.md.
"""

import json
import logging
import urllib.error
import urllib.request
from typing import Any

from apps.core.exceptions import TransientError
from clients.base import ClientError
from clients.dto import TelegramMessage, TelegramSendResult

logger = logging.getLogger(__name__)

API_URL = "https://api.telegram.org/bot{token}/sendMessage"
TIMEOUT_SECONDS = 10


class RealTelegramClient:
    def __init__(self, token: str) -> None:
        self._token = token

    def send_message(self, payload: TelegramMessage) -> TelegramSendResult:
        message = TelegramMessage.model_validate(payload)
        body = json.dumps(message.model_dump()).encode("utf-8")
        request = urllib.request.Request(
            API_URL.format(token=self._token),
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                answer: dict[str, Any] = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            # 5xx is worth another attempt, 4xx means the request itself is wrong.
            if exc.code >= 500:
                raise TransientError(f"telegram responded {exc.code}") from exc
            raise ClientError(f"telegram rejected the message: {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise TransientError(f"telegram is unreachable: {exc}") from exc

        result = answer.get("result") or {}
        return TelegramSendResult(ok=bool(answer.get("ok")), message_id=result.get("message_id"))

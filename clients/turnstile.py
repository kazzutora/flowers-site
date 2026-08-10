"""Cloudflare Turnstile verification."""

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from apps.core.exceptions import TransientError
from clients.base import ClientError
from clients.dto import TurnstileResult

VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
TIMEOUT_SECONDS = 10


class RealTurnstileVerifier:
    def __init__(self, secret_key: str) -> None:
        self._secret_key = secret_key

    def verify(self, token: str, remote_ip: str | None) -> TurnstileResult:
        form = {"secret": self._secret_key, "response": token}
        if remote_ip:
            form["remoteip"] = remote_ip
        request = urllib.request.Request(
            VERIFY_URL,
            data=urllib.parse.urlencode(form).encode("utf-8"),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                answer: dict[str, Any] = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code >= 500:
                raise TransientError(f"turnstile responded {exc.code}") from exc
            raise ClientError(f"turnstile rejected the request: {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise TransientError(f"turnstile is unreachable: {exc}") from exc

        return TurnstileResult(
            success=bool(answer.get("success")),
            error_codes=list(answer.get("error-codes") or []),
        )

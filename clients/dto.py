from typing import Literal

from pydantic import BaseModel, Field


class TelegramMessage(BaseModel):
    chat_id: str
    text: str = Field(max_length=4096)
    parse_mode: Literal["HTML"] = "HTML"
    disable_web_page_preview: bool = True


class TelegramSendResult(BaseModel):
    ok: bool
    message_id: int | None = None
    error: str | None = None


class TurnstileResult(BaseModel):
    success: bool
    error_codes: list[str] = []

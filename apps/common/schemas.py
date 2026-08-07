"""Pydantic contracts shared across apps — tech.md §5 & §6."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict


class ApiModel(BaseModel):
    """Base for every request/response/task-payload schema in the project."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ErrorCode(str, Enum):
    """Closed set — tech.md §5. Adding a value is a core change, not a fix."""

    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    RATE_LIMITED = "rate_limited"
    PAYMENT_FAILED = "payment_failed"
    INTERNAL_ERROR = "internal_error"


class ErrorBody(ApiModel):
    code: ErrorCode
    message: str
    fields: dict[str, str] | None = None


class ErrorResponse(ApiModel):
    error: ErrorBody


class PingPayload(ApiModel):
    """Payload for the ``common.ping`` task (tech.md §7)."""

    nonce: str

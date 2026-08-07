"""tech.md §5: single JSON error shape, built only through error_response."""

from __future__ import annotations

from django.http import JsonResponse

from apps.common.schemas import ErrorBody, ErrorCode, ErrorResponse

_STATUS_BY_CODE: dict[ErrorCode, int] = {
    ErrorCode.VALIDATION_ERROR: 422,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.CONFLICT: 409,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.PAYMENT_FAILED: 402,
    ErrorCode.INTERNAL_ERROR: 500,
}


def error_response(
    code: ErrorCode,
    message: str,
    fields: dict[str, str] | None = None,
) -> JsonResponse:
    body = ErrorResponse(error=ErrorBody(code=code, message=message, fields=fields))
    return JsonResponse(
        body.model_dump(mode="json", exclude_none=True),
        status=_STATUS_BY_CODE[code],
    )

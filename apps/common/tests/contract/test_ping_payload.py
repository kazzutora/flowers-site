import pytest
from pydantic import ValidationError

from apps.common.schemas import PingPayload


def test_requires_nonce() -> None:
    with pytest.raises(ValidationError):
        PingPayload.model_validate({})


def test_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        PingPayload.model_validate({"nonce": "abc", "extra": "nope"})


def test_accepts_valid_payload() -> None:
    payload = PingPayload.model_validate({"nonce": "abc123"})
    assert payload.nonce == "abc123"

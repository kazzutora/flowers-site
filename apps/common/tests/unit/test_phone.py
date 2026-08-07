import pytest

from apps.common.phone import InvalidPhoneNumberError, normalize_phone


@pytest.mark.parametrize(
    "raw",
    ["0671234567", "+38 067 123 45 67", "38(067)1234567", "+380671234567"],
)
def test_normalizes_to_e164(raw: str) -> None:
    assert normalize_phone(raw) == "+380671234567"


def test_idempotent() -> None:
    once = normalize_phone("0671234567")
    assert normalize_phone(once) == once


def test_rejects_garbage() -> None:
    with pytest.raises(InvalidPhoneNumberError):
        normalize_phone("not a phone")


def test_rejects_wrong_length() -> None:
    with pytest.raises(InvalidPhoneNumberError):
        normalize_phone("12345")

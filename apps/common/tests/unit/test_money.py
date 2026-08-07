from decimal import Decimal

import pytest

from apps.common.money import Money


def test_add_same_currency() -> None:
    assert Money("10.50") + Money("5.25") == Money("15.75")


def test_sub_same_currency() -> None:
    assert Money("10.50") - Money("5.25") == Money("5.25")


def test_rejects_float_input() -> None:
    with pytest.raises(TypeError):
        Money(10.5)  # type: ignore[arg-type]


def test_rejects_currency_mismatch() -> None:
    with pytest.raises(ValueError, match="currency mismatch"):
        Money("10.00", "UAH") + Money("10.00", "USD")


def test_quantizes_to_two_decimal_places() -> None:
    assert Money(Decimal("10.005")).amount == Decimal("10.01")


def test_multiply_by_quantity() -> None:
    assert Money("15.00") * 3 == Money("45.00")


def test_rejects_non_int_multiplier() -> None:
    with pytest.raises(TypeError):
        Money("15.00") * 1.5  # type: ignore[operator]


def test_ordering() -> None:
    assert Money("5.00") < Money("10.00")
    assert Money("10.00") <= Money("10.00")
    assert Money("10.00") >= Money("5.00")


def test_zero() -> None:
    assert Money.zero() == Money("0.00")

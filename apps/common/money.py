"""tech.md §4: money is always Decimal, arithmetic only through this type."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

_CENTS = Decimal("0.01")


class Money:
    __slots__ = ("amount", "currency")

    def __init__(self, amount: Decimal | int | str, currency: str = "UAH") -> None:
        if isinstance(amount, float):
            raise TypeError("Money does not accept float; pass Decimal, int, or str")
        self.amount: Decimal = Decimal(amount).quantize(_CENTS, rounding=ROUND_HALF_UP)
        self.currency = currency

    def _check_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise ValueError(f"currency mismatch: {self.currency} vs {other.currency}")

    def __add__(self, other: Money) -> Money:
        self._check_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._check_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, quantity: int) -> Money:
        if not isinstance(quantity, int):
            raise TypeError("Money can only be multiplied by an int quantity")
        return Money(self.amount * quantity, self.currency)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Money)
            and self.amount == other.amount
            and self.currency == other.currency
        )

    def __lt__(self, other: Money) -> bool:
        self._check_currency(other)
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        return self == other or self < other

    def __gt__(self, other: Money) -> bool:
        self._check_currency(other)
        return self.amount > other.amount

    def __ge__(self, other: Money) -> bool:
        return self == other or self > other

    def __hash__(self) -> int:
        return hash((self.amount, self.currency))

    def __repr__(self) -> str:
        return f"Money({self.amount!s}, {self.currency!r})"

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"

    @classmethod
    def zero(cls, currency: str = "UAH") -> Money:
        return cls(Decimal("0.00"), currency)

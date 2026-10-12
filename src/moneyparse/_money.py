"""A frozen money value: an exact Decimal amount plus an optional ISO 4217 code."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation

from ._currencies import get_currency
from ._errors import CurrencyMismatchError, MinorUnitError, MoneyError

Scalar = int | Decimal


def _to_decimal(value: object) -> Decimal:
    if isinstance(value, (bool, float)) or not isinstance(value, (int, str, Decimal)):
        raise TypeError(f"amount must be int, str or Decimal, not {type(value).__name__}")
    try:
        number = Decimal(value)
    except InvalidOperation:
        raise MoneyError(f"not a decimal amount: {value!r}") from None
    if not number.is_finite():
        raise MoneyError(f"amount must be finite, got {value!r}")
    return number


@dataclass(frozen=True, slots=True)
class Money:
    """An exact amount of one currency. Immutable and hashable.

    ``amount`` accepts ``int``, ``str`` or ``Decimal`` and is stored as a Decimal;
    ``float`` is refused because it cannot hold cents exactly. ``currency`` is an
    ISO 4217 code (normalised to upper case) or ``None`` for a bare amount.

    Arithmetic keeps exactness and refuses to mix currencies:

    >>> Money("10.50", "EUR") + Money("0.25", "EUR")
    Money(amount=Decimal('10.75'), currency='EUR')
    >>> Money("10.50", "EUR") * 3
    Money(amount=Decimal('31.50'), currency='EUR')

    Adding ``Money("1", "USD")`` to ``Money("1", "EUR")`` raises
    :class:`CurrencyMismatchError`; so does ordering them. Equality is by value,
    so ``Money("1.0", "EUR") == Money("1.00", "EUR")``.
    """

    amount: Decimal
    currency: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "amount", _to_decimal(self.amount))
        if self.currency is not None:
            if not isinstance(self.currency, str) or self.currency.isdigit():
                raise MoneyError(f"currency must be an alphabetic ISO code: {self.currency!r}")
            object.__setattr__(self, "currency", get_currency(self.currency).code)

    def _same(self, other: object, op: str) -> Money:
        if not isinstance(other, Money):
            raise TypeError(f"cannot {op} Money and {type(other).__name__}")
        if other.currency != self.currency:
            raise CurrencyMismatchError(
                f"cannot {op} {self.currency} and {other.currency}: convert first"
            )
        return other

    def __add__(self, other: Money) -> Money:
        return Money(self.amount + self._same(other, "add").amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        return Money(self.amount - self._same(other, "subtract").amount, self.currency)

    def __mul__(self, factor: Scalar) -> Money:
        if isinstance(factor, bool) or not isinstance(factor, (int, Decimal)):
            raise TypeError(f"Money can only be multiplied by int or Decimal, not {factor!r}")
        return Money(self.amount * factor, self.currency)

    __rmul__ = __mul__

    def __neg__(self) -> Money:
        return Money(-self.amount, self.currency)

    def __pos__(self) -> Money:
        return self

    def __abs__(self) -> Money:
        return Money(abs(self.amount), self.currency)

    def __bool__(self) -> bool:
        return bool(self.amount)

    def __lt__(self, other: Money) -> bool:
        return self.amount < self._same(other, "compare").amount

    def __le__(self, other: Money) -> bool:
        return self.amount <= self._same(other, "compare").amount

    def __gt__(self, other: Money) -> bool:
        return self.amount > self._same(other, "compare").amount

    def __ge__(self, other: Money) -> bool:
        return self.amount >= self._same(other, "compare").amount

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}" if self.currency else str(self.amount)

    @property
    def minor_units(self) -> int | None:
        """Decimal places of the currency's minor unit, or None (no currency, or N.A.)."""
        return get_currency(self.currency).minor_units if self.currency else None

    def _exponent(self) -> Decimal:
        if self.minor_units is None:
            raise MinorUnitError(f"{self.currency or 'a bare amount'} has no minor unit")
        return Decimal(1).scaleb(-self.minor_units)

    def quantize(self, rounding: str = ROUND_HALF_EVEN) -> Money:
        """Round to the currency's minor units (banker's rounding by default).

        >>> Money("2.675", "USD").quantize()
        Money(amount=Decimal('2.68'), currency='USD')
        """
        return Money(self.amount.quantize(self._exponent(), rounding=rounding), self.currency)

    def to_minor(self) -> int:
        """Return the amount in minor units (cents) exactly, e.g. 1234 for 12.34 USD.

        Raises :class:`MinorUnitError` if the amount has finer precision.
        """
        exact = self.amount.quantize(self._exponent())
        if exact != self.amount:
            raise MinorUnitError(f"{self} is not a whole number of minor units")
        return int(exact.scaleb(self.minor_units or 0))

    @classmethod
    def from_minor(cls, units: int, currency: str) -> Money:
        """Build from an integer count of minor units: ``from_minor(1234, "USD")``."""
        if isinstance(units, bool) or not isinstance(units, int):
            raise TypeError("units must be an int")
        digits = get_currency(currency).minor_units
        if digits is None:
            raise MinorUnitError(f"{currency} has no minor unit")
        return cls(Decimal(units).scaleb(-digits), currency)

    def allocate(self, ratios: Sequence[int]) -> tuple[Money, ...]:
        """Split into parts proportional to ``ratios`` without losing a minor unit.

        Leftover minor units go one by one to the first parts, so the parts always
        add up to the (quantized) original:

        >>> [str(m) for m in Money("100.00", "EUR").allocate([1, 1, 1])]
        ['33.34 EUR', '33.33 EUR', '33.33 EUR']
        """
        if not ratios or any(isinstance(r, bool) or not isinstance(r, int) for r in ratios):
            raise TypeError("ratios must be a non-empty sequence of ints")
        if any(r < 0 for r in ratios) or sum(ratios) == 0:
            raise ValueError("ratios must be non-negative and not all zero")
        total = self.quantize().to_minor()
        sign = -1 if total < 0 else 1
        shares = [abs(total) * r // sum(ratios) for r in ratios]
        receivers = [index for index, ratio in enumerate(ratios) if ratio]
        for index in receivers[: abs(total) - sum(shares)]:
            shares[index] += 1
        return tuple(type(self).from_minor(sign * s, self.currency or "") for s in shares)

    def format(self, locale: str = "en-US", **options: object) -> str:
        """Format for a CLDR locale; same options as :func:`format_money`."""
        from ._format import format_money

        return format_money(self, locale=locale, **options)  # type: ignore[arg-type]

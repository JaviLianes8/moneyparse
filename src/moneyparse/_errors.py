"""Typed errors raised by moneyparse.

Every error is a :class:`ValueError` through :class:`MoneyError`, so a single
``except ValueError`` still catches everything. Errors raised while reading text are
also :class:`MoneyParseError`, the name the first release exported.
"""

from __future__ import annotations


class MoneyError(ValueError):
    """Base class of every error raised by moneyparse."""


class MoneyParseError(MoneyError):
    """Raised when a string is not a valid money value or is ambiguous."""


class AmbiguousSeparatorError(MoneyParseError):
    """The decimal and grouping separators cannot be told apart.

    ``"1,234"`` and ``"1.234"`` mean one thousand two hundred thirty-four in one
    convention and one point two three four in the other. Pass ``locale`` or
    ``decimal`` (or ``decimal_comma`` on :func:`parse_money`) to decide.
    """


class AmbiguousCurrencyError(MoneyParseError):
    """A currency symbol maps to several currencies and no hint chose one.

    ``candidates`` lists the ISO 4217 codes the symbol can stand for.
    """

    def __init__(self, symbol: str, candidates: tuple[str, ...]) -> None:
        self.symbol = symbol
        self.candidates = candidates
        shown = ", ".join(candidates)
        super().__init__(
            f"currency symbol {symbol!r} is ambiguous ({shown}): pass currency= or locale="
        )


class CurrencyConflictError(MoneyParseError):
    """The text names a currency that contradicts the ``currency`` hint."""


class MinorUnitError(MoneyParseError):
    """An amount has more fractional digits than its currency's minor units allow."""


class UnknownCurrencyError(MoneyError):
    """A currency code is not in the embedded ISO 4217 table."""


class UnknownLocaleError(MoneyError):
    """A locale tag has no embedded CLDR number data."""


class CurrencyMismatchError(MoneyError):
    """Arithmetic or comparison between amounts in different currencies."""

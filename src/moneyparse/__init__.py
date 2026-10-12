"""Parse human money strings into exact Decimal amounts with their currency.

Main entry points:

- :func:`parse` reads one money string into a :class:`Money`.
- :func:`find_money` finds every amount in free text, with spans.
- :func:`format_money` writes an amount back the way a CLDR locale does.
- :func:`parse_money` is the first release's tuple-returning parser, unchanged.

Currency data is ISO 4217 (embedded, see :data:`ISO4217_PUBLISHED`); locale data
is Unicode CLDR 48. There are no dependencies and floats are never used.
"""

from __future__ import annotations

from ._currencies import Currency, currencies, get_currency
from ._engine import parse
from ._errors import (
    AmbiguousCurrencyError,
    AmbiguousSeparatorError,
    CurrencyConflictError,
    CurrencyMismatchError,
    MinorUnitError,
    MoneyError,
    MoneyParseError,
    UnknownCurrencyError,
    UnknownLocaleError,
)
from ._find import MoneyMatch, find_money
from ._format import format_money
from ._iso4217_data import ISO4217_PUBLISHED
from ._locales import Locale, get_locale, locales
from ._money import Money
from ._parse import parse_money

__version__ = "0.2.0"

__all__ = [
    "ISO4217_PUBLISHED",
    "AmbiguousCurrencyError",
    "AmbiguousSeparatorError",
    "Currency",
    "CurrencyConflictError",
    "CurrencyMismatchError",
    "Locale",
    "MinorUnitError",
    "Money",
    "MoneyError",
    "MoneyMatch",
    "MoneyParseError",
    "UnknownCurrencyError",
    "UnknownLocaleError",
    "currencies",
    "find_money",
    "format_money",
    "get_currency",
    "get_locale",
    "locales",
    "parse",
    "parse_money",
]

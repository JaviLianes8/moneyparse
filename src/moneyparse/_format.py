"""Format an amount back into a locale's currency string, following CLDR patterns."""

from __future__ import annotations

import re
import unicodedata
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Literal

from ._currencies import get_currency
from ._locales import Locale, get_locale
from ._money import Money, _to_decimal
from ._symbols import is_ambiguous

Style = Literal["symbol", "code", "plain"]
_CORE = re.compile(r"[#0,.]+")
_NBSP = "\xa0"
_SIGN = "\xa4"  # the CLDR currency placeholder
_TRIM = " \xa0\N{LEFT-TO-RIGHT MARK}\N{RIGHT-TO-LEFT MARK}"
# CLDR ``en`` standard symbols; used when the locale has no symbol of its own.
_EN_SYMBOLS = {
    "AUD": "A$", "BRL": "R$", "CAD": "CA$", "CNY": "CN¥", "EUR": "€", "GBP": "£",
    "HKD": "HK$", "ILS": "₪", "INR": "₹", "JPY": "¥", "KRW": "₩", "MXN": "MX$",
    "NZD": "NZ$", "PHP": "₱", "TWD": "NT$", "USD": "$", "VND": "₫", "XAF": "FCFA",
    "XCD": "EC$", "XCG": "Cg.", "XOF": "F\u202fCFA", "XPF": "CFPF",
}  # fmt: skip


def format_money(
    value: Money | Decimal | int | str,
    currency: str | None = None,
    *,
    locale: str = "en-US",
    style: Style = "symbol",
    accounting: bool = False,
    digits: int | None = None,
    rounding: str = ROUND_HALF_EVEN,
) -> str:
    """Format an amount the way a CLDR locale writes money.

    >>> format_money(Money("1234.5", "EUR"), locale="de-DE")
    '1.234,50\\xa0€'
    >>> format_money(Decimal("-1234"), "USD", accounting=True)
    '($1,234.00)'
    >>> format_money(Decimal("12345678.9"), "INR", locale="en-IN")
    '₹1,23,45,678.90'

    Args:
        value: A :class:`Money`, or an int, str or Decimal amount (never float).
        currency: ISO code; taken from ``value`` when it is a :class:`Money`.
        locale: CLDR locale tag; selects separators, grouping, minus sign and the
            standard or accounting pattern.
        style: ``"symbol"`` (the locale's own symbol, else an unambiguous CLDR
            symbol, else the code), ``"code"`` (``USD``) or ``"plain"`` (no currency).
        accounting: Use the accounting pattern (parentheses for negatives where the
            locale has them).
        digits: Fraction digits; default is the currency's ISO 4217 minor units, or
            the amount's own digits when there is no currency or it has none.
        rounding: A :mod:`decimal` rounding mode; default is banker's rounding.

    The output parses back to the same amount with
    ``parse(text, locale=locale, currency=code)``.
    """
    if isinstance(value, Money):
        if currency is not None and value.currency is not None and currency != value.currency:
            raise ValueError(f"value is in {value.currency}, not {currency}")
        amount, code = value.amount, value.currency or currency
    else:
        amount, code = _to_decimal(value), currency
    code = get_currency(code).code if code is not None else None
    loc = get_locale(locale)
    places = digits if digits is not None else _default_places(amount, code)
    if places < 0:
        raise ValueError("digits must be zero or positive")
    amount = amount.quantize(Decimal(1).scaleb(-places), rounding=rounding)
    pattern = loc.accounting if accounting else loc.standard
    positive, _, negative = pattern.partition(";")
    chosen = (negative or "-" + positive) if amount < 0 else positive
    prefix, core, suffix = _split(chosen)
    number = _digits(abs(amount), places, core, loc)
    marker = None if style == "plain" or code is None else _marker(code, style, loc)
    return _assemble(prefix, number, suffix, marker, loc.minus)


def _default_places(amount: Decimal, code: str | None) -> int:
    units = get_currency(code).minor_units if code else None
    if units is not None:
        return units
    exponent = amount.as_tuple().exponent
    return -exponent if isinstance(exponent, int) and exponent < 0 else 0


def _split(pattern: str) -> tuple[str, str, str]:
    found = _CORE.search(pattern)
    if found is None:  # pragma: no cover - every CLDR currency pattern has a core
        raise ValueError(f"bad pattern {pattern!r}")
    return pattern[: found.start()], found.group(), pattern[found.end() :]


def _digits(amount: Decimal, places: int, core: str, loc: Locale) -> str:
    text = f"{amount:.{places}f}"
    integer, _, fraction = text.partition(".")
    pieces = core.split(".")[0].split(",")
    primary = len(pieces[-1]) if len(pieces) > 1 else 0
    secondary = len(pieces[-2]) if len(pieces) > 2 else primary
    if primary and len(integer) >= primary + loc.min_grouping:
        groups = [integer[-primary:]]
        rest = integer[:-primary]
        while rest:
            groups.insert(0, rest[-secondary:])
            rest = rest[:-secondary]
        integer = loc.group.join(groups)
    return f"{integer}{loc.decimal}{fraction}" if fraction else integer


def _marker(code: str, style: Style, loc: Locale) -> str:
    if style == "code":
        return code
    local = loc.symbol_for(code)
    if local is not None:
        return local
    symbol = _EN_SYMBOLS.get(code)
    return symbol if symbol is not None and not is_ambiguous(symbol) else code


def _spaced(edge: str) -> bool:
    """CLDR currencySpacing: a non-symbol edge next to a digit gets a no-break space."""
    return not unicodedata.category(edge).startswith(("S", "Z"))


def _assemble(prefix: str, number: str, suffix: str, marker: str | None, minus: str) -> str:
    prefix, suffix = prefix.replace("-", minus), suffix.replace("-", minus)
    if marker is None:
        prefix = prefix.replace(_SIGN, "").strip(_TRIM)
        return prefix + number + suffix.replace(_SIGN, "").strip(_TRIM)
    if prefix.endswith(_SIGN) and _spaced(marker[-1]):
        prefix += _NBSP
    if suffix.startswith(_SIGN) and _spaced(marker[0]):
        suffix = _NBSP + suffix
    return prefix.replace(_SIGN, marker) + number + suffix.replace(_SIGN, marker)

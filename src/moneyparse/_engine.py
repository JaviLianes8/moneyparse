"""The full money parser: currency resolution, separators, sign, magnitude, minor units."""

from __future__ import annotations

from decimal import Decimal

from ._currencies import get_currency
from ._errors import (
    AmbiguousSeparatorError,
    CurrencyConflictError,
    MinorUnitError,
    MoneyParseError,
)
from ._exact import exact, fits, quantize
from ._locales import Locale, get_locale
from ._money import Money
from ._number import parse_number
from ._symbols import resolve_symbol
from ._tokens import clean, peel


def parse(
    text: str,
    *,
    currency: str | None = None,
    locale: str | None = None,
    decimal: str | None = None,
    group: str | None = None,
    magnitude: bool = False,
    strict_minor: bool = False,
    require_currency: bool = False,
) -> Money:
    """Parse a money string into a :class:`Money` with an exact Decimal amount.

    >>> parse("1.234,56 €")
    Money(amount=Decimal('1234.56'), currency='EUR')
    >>> parse("$1,234.56", locale="en-US")
    Money(amount=Decimal('1234.56'), currency='USD')
    >>> parse("(1,234.00)", currency="USD", decimal=".")
    Money(amount=Decimal('-1234.00'), currency='USD')

    Args:
        text: The string, for example ``"€1.234,56"``, ``"1 234,56 kr"``,
            ``"USD (42.00)"``, ``"CHF-1'234.50"`` or ``"99.95-"``.
        currency: ISO 4217 code that resolves an ambiguous symbol (``$``, ``¥``,
            ``kr``, ``Rs``) and is used when the text has no currency. If the text
            names a different currency, :class:`CurrencyConflictError` is raised.
        locale: CLDR locale tag (``"de-DE"``, ``"fr-FR"``, ``"en-IN"``). Fixes the
            decimal and grouping separators and gives local symbols their local
            meaning (``$`` is CAD in ``en-CA``, ``kr`` is SEK in ``sv-SE``).
        decimal: Explicit decimal separator; overrides the locale.
        group: Explicit grouping separator (default: the other of ``.`` and ``,``).
            Alone it may only be ``.`` or ``,``; spaces and apostrophes always group.
        magnitude: Accept a scale suffix: ``k`` / ``thousand``, ``m`` / ``M`` /
            ``mn`` / ``million``, ``b`` / ``bn`` / ``billion``, ``t`` / ``tn`` /
            ``trillion`` (``"$1.2k"`` is 1200).
        strict_minor: Reject amounts the currency cannot hold in its minor units
            (``"¥1.5"`` for JPY, ``"$0.001"`` for USD) with :class:`MinorUnitError`.
            It also settles ``"$1,234"`` as 1234 USD, since 1.234 USD is invalid.
        require_currency: Raise :class:`MoneyParseError` when no currency results.

    Without ``locale`` or ``decimal`` the separator convention is detected, and a
    string such as ``"1,234"`` raises :class:`AmbiguousSeparatorError`. With a
    locale, its CLDR currency separators are accepted too (``1.234,56`` in de-AT).

    Raises:
        MoneyParseError: Or one of its subclasses, for text that is not money.
        UnknownCurrencyError: ``currency`` is not an ISO 4217 code.
        UnknownLocaleError: ``locale`` has no embedded CLDR data.
    """
    if not isinstance(text, str):
        raise TypeError(f"parse() expects a string, got {type(text).__name__}")
    hint = get_currency(currency).code if currency is not None else None
    loc = get_locale(locale) if locale is not None else None
    dec, grp = _separators(decimal, group, loc)
    cleaned = clean(text)
    if not cleaned:
        raise MoneyParseError("empty money string")
    peeled = peel(cleaned, magnitude=magnitude)
    local = {clean(sym): code for sym, code in loc.symbols} if loc else None
    code = _resolve(peeled.codes, peeled.symbols, hint, local, loc.currency if loc else None)
    indian = loc.indian_grouping if loc and decimal is None else False
    pairs = [(dec, grp)]
    if loc is not None and decimal is None and group is None:
        pairs.append((loc.currency_decimal, loc.currency_group))  # CLDR currencyGroup
    # A magnitude rescales the digits, so they cannot settle a separator by minor units.
    settle = code if strict_minor and not peeled.exponent else None
    amount = _first_reading(peeled.number, pairs, indian, settle)
    if peeled.exponent:
        amount = _scale(amount, peeled.exponent)
    if peeled.negative:
        amount = amount.copy_negate()
    if require_currency and code is None:
        raise MoneyParseError(f"no currency in {text!r}")
    if strict_minor and code is not None:
        _check_minor(amount, code, text)
    return Money(amount, code)


def _separators(
    decimal: str | None, group: str | None, loc: Locale | None
) -> tuple[str | None, str | None]:
    for name, value in (("decimal", decimal), ("group", group)):
        if value is not None and (len(value) != 1 or value.isdigit() or value in "+-()"):
            raise ValueError(f"{name} must be one non-digit character, got {value!r}")
    if decimal is not None and decimal == group:
        raise ValueError("decimal and group separators must differ")
    if decimal is None and group is not None:
        if group not in ".,":
            raise ValueError("pass decimal= together with a group separator other than . or ,")
        decimal = "," if group == "." else "."
    if decimal is not None:
        return decimal, group
    if loc is not None:
        return loc.decimal, loc.group
    return None, None


def _first_reading(
    number: str, pairs: list[tuple[str | None, str | None]], indian: bool, code: str | None
) -> Decimal:
    """Try each (decimal, group) pair in order; the last failure propagates."""
    unique = list(dict.fromkeys(pairs))
    for dec, grp in unique[:-1]:
        try:
            return _number(number, dec, grp, indian, code)
        except MoneyParseError:
            continue
    dec, grp = unique[-1]
    return _number(number, dec, grp, indian, code)


def _number(
    number: str, dec: str | None, grp: str | None, indian: bool, strict_code: str | None
) -> Decimal:
    """Parse the digits. Under ``strict_minor`` the currency can settle ``1,234``.

    When reading the mark as a decimal point would break the currency's minor units
    (``1.234`` USD has a tenth of a cent) the grouping reading is the only valid
    one. ``10.500`` USD stays ambiguous: 10.50 is a valid amount too.
    """
    try:
        return parse_number(number, decimal=dec, group=grp, indian=indian)
    except AmbiguousSeparatorError as error:
        units = get_currency(strict_code).minor_units if strict_code else None
        if units is None:
            raise
        as_decimal = parse_number(number, decimal=error.separator, indian=indian)
        if fits(as_decimal, units):
            raise
        decimal = "." if error.separator == "," else ","
        return parse_number(number, decimal=decimal, group=error.separator, indian=indian)


def _resolve(
    codes: tuple[str, ...],
    symbols: tuple[str, ...],
    hint: str | None,
    local: dict[str, str] | None,
    home: str | None,
) -> str | None:
    if len(set(codes)) > 1:
        raise CurrencyConflictError(f"the text names several currencies: {sorted(set(codes))}")
    if len(codes) > 1 or len(symbols) > 1:
        raise MoneyParseError("a currency is named twice")
    code = codes[0] if codes else None
    if code is not None and hint is not None and code != hint:
        raise CurrencyConflictError(f"the text says {code} but currency={hint!r}")
    chosen = code or hint
    for symbol in symbols:
        resolved = resolve_symbol(symbol, chosen, local, home)
        chosen = chosen or resolved
    return chosen


def _scale(amount: Decimal, exponent: int) -> Decimal:
    scaled = exact(lambda: amount.scaleb(exponent))
    return quantize(scaled, 0) if fits(scaled, 0) else scaled


def _check_minor(amount: Decimal, code: str, text: str) -> None:
    units = get_currency(code).minor_units
    if units is None:
        return
    if not fits(amount, units):
        raise MinorUnitError(f"{text!r} has more precision than {code} allows ({units} digits)")

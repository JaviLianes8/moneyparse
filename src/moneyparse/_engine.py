"""The full money parser: currency resolution, separators, sign, magnitude, minor units."""

from __future__ import annotations

from decimal import Decimal

from ._currencies import get_currency
from ._errors import CurrencyConflictError, MinorUnitError, MoneyParseError
from ._locales import Locale, get_locale
from ._money import Money
from ._number import FILLERS, parse_number
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
            Spaces and apostrophes always group.
        magnitude: Accept a scale suffix: ``k`` / ``thousand``, ``m`` / ``M`` /
            ``mn`` / ``million``, ``b`` / ``bn`` / ``billion``, ``t`` / ``tn`` /
            ``trillion`` (``"$1.2k"`` is 1200).
        strict_minor: Reject amounts the currency cannot hold in its minor units
            (``"¥1.5"`` for JPY, ``"$0.001"`` for USD) with :class:`MinorUnitError`.
        require_currency: Raise :class:`MoneyParseError` when no currency results.

    Without ``locale`` or ``decimal`` the separator convention is detected, and a
    string such as ``"1,234"`` raises :class:`AmbiguousSeparatorError`.

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
    code = _resolve(peeled.codes, peeled.symbols, hint, local)
    indian = loc.indian_grouping if loc and decimal is None else False
    amount = parse_number(peeled.number, decimal=dec, group=grp, indian=indian)
    if peeled.exponent:
        amount = _scale(amount, peeled.exponent)
    if peeled.negative:
        amount = -amount
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
        if group not in ".," and group not in FILLERS:
            raise ValueError("pass decimal= together with an unusual group separator")
        decimal = "," if group == "." else "."
    if decimal is not None:
        return decimal, group
    if loc is not None:
        return loc.decimal, loc.group
    return None, None


def _resolve(
    codes: tuple[str, ...],
    symbols: tuple[str, ...],
    hint: str | None,
    local: dict[str, str] | None,
) -> str | None:
    named = set(codes)
    if len(named) > 1:
        raise CurrencyConflictError(f"the text names several currencies: {sorted(named)}")
    code = codes[0] if codes else None
    if code is not None and hint is not None and code != hint:
        raise CurrencyConflictError(f"the text says {code} but currency={hint!r}")
    chosen = code or hint
    for symbol in symbols:
        resolved = resolve_symbol(symbol, chosen, local)
        chosen = chosen or resolved
    return chosen


def _scale(amount: Decimal, exponent: int) -> Decimal:
    scaled = amount.scaleb(exponent)
    return scaled.quantize(Decimal(1)) if scaled == scaled.to_integral_value() else scaled


def _check_minor(amount: Decimal, code: str, text: str) -> None:
    units = get_currency(code).minor_units
    if units is None:
        return
    if amount != amount.quantize(Decimal(1).scaleb(-units)):
        raise MinorUnitError(f"{text!r} has more precision than {code} allows ({units} digits)")

"""ISO 4217 currency records built from the embedded table."""

from __future__ import annotations

from dataclasses import dataclass

from ._errors import UnknownCurrencyError
from ._iso4217_data import TABLE


@dataclass(frozen=True, slots=True)
class Currency:
    """One ISO 4217 currency.

    Attributes:
        code: Alphabetic code, for example ``"EUR"``.
        numeric: Three-digit numeric code as a string, keeping leading zeros
            (``"008"`` for ``ALL``).
        minor_units: Number of decimal places of the minor unit (``2`` for USD,
            ``0`` for JPY, ``3`` for KWD, ``4`` for CLF), or ``None`` where ISO 4217
            says "N.A." (precious metals, funds such as XDR, the testing code XTS).
        name: Official currency name from the list.
    """

    code: str
    numeric: str
    minor_units: int | None
    name: str


def _load() -> dict[str, Currency]:
    table: dict[str, Currency] = {}
    for row in TABLE.splitlines():
        code, numeric, minor, name = row.split("|")
        units = None if minor == "-" else int(minor)
        table[code] = Currency(code, numeric, units, name)
    return table


_BY_CODE = _load()
_BY_NUMERIC = {currency.numeric: currency for currency in _BY_CODE.values()}


def get_currency(code: str | int) -> Currency:
    """Look up a currency by alphabetic or numeric ISO 4217 code.

    Alphabetic codes are case-insensitive. Numeric codes may be an ``int`` (``8``)
    or a string with or without leading zeros (``"008"``, ``"8"``).

    >>> get_currency("jpy").minor_units
    0
    >>> get_currency(978).code
    'EUR'

    Raises:
        UnknownCurrencyError: The code is not in the embedded table.
    """
    if isinstance(code, bool) or not isinstance(code, (int, str)):
        raise UnknownCurrencyError(f"unknown ISO 4217 currency: {code!r}")
    if isinstance(code, int):
        found = _BY_NUMERIC.get(f"{code:03d}") if 0 <= code <= 999 else None
    else:
        key = code.strip()
        if key.isdigit() and len(key) <= 3:
            found = _BY_NUMERIC.get(key.zfill(3))
        else:
            found = _BY_CODE.get(key.upper())
    if found is None:
        raise UnknownCurrencyError(f"unknown ISO 4217 currency: {code!r}")
    return found


def is_currency_code(code: str) -> bool:
    """Return True when ``code`` is an active alphabetic ISO 4217 code (exact case)."""
    return code in _BY_CODE


def currencies() -> tuple[Currency, ...]:
    """Return every currency of the embedded ISO 4217 table, sorted by code."""
    return tuple(_BY_CODE[code] for code in sorted(_BY_CODE))

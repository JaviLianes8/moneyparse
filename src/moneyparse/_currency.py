"""Detect and strip currency symbols and ISO 4217 codes from a money string."""

from __future__ import annotations

import re

_SYMBOL_TO_CODE: dict[str, str] = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY",
    "₹": "INR",
    "₩": "KRW",
    "₽": "RUB",
    "₺": "TRY",
    "₴": "UAH",
    "¢": "USD",
}

_CODES: frozenset[str] = frozenset(
    {
        "USD",
        "EUR",
        "GBP",
        "JPY",
        "CHF",
        "CAD",
        "AUD",
        "NZD",
        "CNY",
        "HKD",
        "SGD",
        "SEK",
        "NOK",
        "DKK",
        "PLN",
        "CZK",
        "HUF",
        "RUB",
        "INR",
        "BRL",
        "MXN",
        "ZAR",
        "KRW",
        "TRY",
        "UAH",
        "AED",
        "SAR",
        "ILS",
        "THB",
        "IDR",
        "MYR",
        "PHP",
    }
)

_PREFIX = re.compile(r"^([A-Za-z]{3})(?![A-Za-z])")
_SUFFIX = re.compile(r"(?<![A-Za-z])([A-Za-z]{3})$")


def extract_currency(text: str) -> tuple[str | None, str]:
    """Return the ISO code found in ``text`` (or None) and the remaining text."""
    stripped = text.strip()
    prefix = _PREFIX.match(stripped)
    if prefix and prefix.group(1).upper() in _CODES:
        return prefix.group(1).upper(), stripped[prefix.end() :]
    suffix = _SUFFIX.search(stripped)
    if suffix and suffix.group(1).upper() in _CODES:
        return suffix.group(1).upper(), stripped[: suffix.start()]
    for symbol, code in _SYMBOL_TO_CODE.items():
        if symbol in stripped:
            return code, stripped.replace(symbol, "", 1)
    return None, stripped

"""Oracle round-trips against Babel, an independent CLDR implementation.

Babel is not a dependency. When it is installed, every embedded locale formats a
grid of amounts and currencies with Babel (standard and accounting patterns) and
moneyparse must read each string back to the exact Decimal. Without Babel the
module is skipped and the CLDR fixtures in ``cldr_fixtures.py`` carry the contract.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from moneyparse import get_currency, get_locale, locales, parse

numbers = pytest.importorskip("babel.numbers")

CODES = ("USD", "EUR", "JPY", "KWD", "CHF", "GBP", "INR")
AMOUNTS = ("0", "3", "-3", "1234.5", "-1234.5", "1234567.891", "-98765432.1")


def _quantized(raw: str, code: str) -> Decimal:
    units = get_currency(code).minor_units or 0
    return Decimal(raw).quantize(Decimal(1).scaleb(-units))


@pytest.mark.parametrize("locale", locales())
@pytest.mark.parametrize("format_type", ["standard", "accounting"])
def test_babel_output_parses_back(locale: str, format_type: str) -> None:
    babel_locale = locale.replace("-", "_")
    for code in (*CODES, get_locale(locale).currency):
        for raw in AMOUNTS:
            text = numbers.format_currency(
                Decimal(raw), code, locale=babel_locale, format_type=format_type
            )
            money = parse(text, locale=locale, currency=code)
            assert money.amount == _quantized(raw, code), (locale, code, raw, text)
            assert money.currency == code


@pytest.mark.parametrize("locale", locales())
def test_babel_decimal_output_parses_back(locale: str) -> None:
    babel_locale = locale.replace("-", "_")
    for raw in AMOUNTS:
        text = numbers.format_decimal(Decimal(raw), locale=babel_locale)
        assert parse(text, locale=locale).amount == Decimal(raw), (locale, raw, text)

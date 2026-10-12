"""Contract: the complete promise, checked against CLDR 48 and ISO 4217 fixtures.

1. ``format_money`` writes exactly what CLDR specifies for each locale.
2. ``parse`` reads every such string back to the exact Decimal and currency.
3. Every embedded locale round-trips every sampled currency, sign, style and
   pattern, with ISO 4217 minor units deciding the fraction digits.
4. Strings typed by people in those conventions parse to the value they mean.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from cldr_fixtures import FORMATTED, TYPED

from moneyparse import Money, format_money, get_currency, get_locale, locales, parse

SAMPLE_CODES = ("USD", "EUR", "GBP", "JPY", "KWD", "BHD", "CLF", "INR", "CHF", "XAU")
AMOUNTS = ("0", "7", "-7", "1234.5", "-1234.5678", "999999.995", "12345678.9", "0.004")


@pytest.mark.parametrize(("locale", "amount", "code", "accounting", "expected"), FORMATTED)
def test_format_matches_cldr(
    locale: str, amount: Decimal, code: str, accounting: bool, expected: str
) -> None:
    assert format_money(amount, code, locale=locale, accounting=accounting) == expected


@pytest.mark.parametrize(("locale", "amount", "code", "accounting", "expected"), FORMATTED)
def test_cldr_strings_parse_back(
    locale: str, amount: Decimal, code: str, accounting: bool, expected: str
) -> None:
    money = parse(expected, locale=locale, currency=code)
    places = get_currency(code).minor_units or 0
    assert money == Money(amount.quantize(Decimal(1).scaleb(-places)), code)


@pytest.mark.parametrize(("locale", "hint", "text", "amount", "code"), TYPED)
def test_typed_strings_mean_what_people_mean(
    locale: str | None, hint: str | None, text: str, amount: Decimal, code: str | None
) -> None:
    money = parse(text, locale=locale, currency=hint)
    assert money.amount == amount
    assert str(money.amount) == str(amount)
    assert money.currency == code


def _expected(amount: Decimal, code: str) -> Decimal:
    units = get_currency(code).minor_units
    if units is None:
        return amount
    return amount.quantize(Decimal(1).scaleb(-units))


@pytest.mark.parametrize("locale", locales())
@pytest.mark.parametrize("style", ["symbol", "code"])
@pytest.mark.parametrize("accounting", [False, True])
def test_every_locale_round_trips(locale: str, style: str, accounting: bool) -> None:
    home = get_locale(locale).currency
    for code in (*SAMPLE_CODES, home):
        for raw in AMOUNTS:
            amount = Decimal(raw)
            text = format_money(
                amount,
                code,
                locale=locale,
                style=style,  # type: ignore[arg-type]
                accounting=accounting,
            )
            money = parse(text, locale=locale, currency=code)
            assert money == Money(_expected(amount, code), code), (locale, code, raw, text)


@pytest.mark.parametrize("locale", locales())
def test_home_currency_needs_no_hint_in_its_locale(locale: str) -> None:
    home = get_locale(locale).currency
    text = format_money(Decimal("-98765.43"), home, locale=locale)
    assert parse(text, locale=locale) == Money(_expected(Decimal("-98765.43"), home), home)


@pytest.mark.parametrize("locale", locales())
def test_plain_style_round_trips_without_currency(locale: str) -> None:
    text = format_money(Decimal("-1234567.25"), locale=locale, style="plain")
    assert parse(text, locale=locale) == Money(Decimal("-1234567.25"))


def test_money_method_matches_function() -> None:
    money = Money("1234.56", "EUR")
    assert money.format("de-DE") == format_money(money, locale="de-DE")

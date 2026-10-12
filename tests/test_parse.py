"""parse(): separators, ambiguity policy, signs, magnitude, minor units, errors."""

from __future__ import annotations

from decimal import Decimal

import pytest

from moneyparse import (
    AmbiguousCurrencyError,
    AmbiguousSeparatorError,
    CurrencyConflictError,
    MinorUnitError,
    Money,
    MoneyError,
    MoneyParseError,
    UnknownCurrencyError,
    UnknownLocaleError,
    parse,
)


@pytest.mark.parametrize("text", ["1,234", "1.234", "12,345", "999.999", "$1,234"])
def test_lone_three_digit_group_is_ambiguous(text: str) -> None:
    with pytest.raises(AmbiguousSeparatorError) as caught:
        parse(text.lstrip("$"))
    assert caught.value.separator in ",."


@pytest.mark.parametrize(
    ("text", "kwargs", "expected"),
    [
        ("1,234", {"decimal": ","}, "1.234"),
        ("1,234", {"decimal": "."}, "1234"),
        ("1.234", {"locale": "de-DE"}, "1234"),
        ("1.234", {"locale": "en-US"}, "1.234"),
        ("1,234", {"group": ","}, "1234"),
        ("0,123", {}, "0.123"),
        (",50", {}, "0.50"),
        ("1234,567", {}, "1234.567"),
        ("1 234,567", {}, "1234.567"),
        ("1'234.500", {}, "1234.500"),
    ],
)
def test_ambiguity_resolution(text: str, kwargs: dict[str, str], expected: str) -> None:
    assert str(parse(text, **kwargs).amount) == expected  # type: ignore[arg-type]


@pytest.mark.parametrize(("text", "code"), [("$1,234", "USD"), ("1.234 €", "EUR")])
def test_strict_minor_units_settle_the_separator(text: str, code: str) -> None:
    assert parse(text, currency=code, strict_minor=True) == Money("1234", code)
    with pytest.raises(AmbiguousSeparatorError):
        parse(text, currency=code)  # $3.459 is a real fuel price: no guessing


@pytest.mark.parametrize("text", ["1,234 KWD", "10.500 USD", "1,234 XAU"])
def test_strict_minor_keeps_genuine_ambiguity(text: str) -> None:
    with pytest.raises(AmbiguousSeparatorError):
        parse(text, strict_minor=True)


@pytest.mark.parametrize("symbol", ["$", "¥", "kr", "Rs", "C$"])
def test_ambiguous_symbols_need_a_hint(symbol: str) -> None:
    with pytest.raises(AmbiguousCurrencyError) as caught:
        parse(f"{symbol}5")
    assert len(caught.value.candidates) > 1


@pytest.mark.parametrize(
    ("text", "kwargs", "code"),
    [
        ("$5", {"currency": "CAD"}, "CAD"),
        ("$5", {"locale": "en-AU"}, "AUD"),
        ("$5", {"locale": "es-MX"}, "MXN"),
        ("$5", {"locale": "de-DE"}, "USD"),
        ("5 kr", {"locale": "nb-NO"}, "NOK"),
        ("£5", {}, "GBP"),
        ("£5", {"currency": "GIP"}, "GIP"),
        ("₩5", {}, "KRW"),
        ("CA$5", {}, "CAD"),
        ("5 usd", {}, "USD"),
        ("$5 USD", {}, "USD"),
    ],
)
def test_currency_resolution(text: str, kwargs: dict[str, str], code: str) -> None:
    assert parse(text, **kwargs).currency == code  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("text", "kwargs"),
    [("€5", {"currency": "USD"}), ("5 EUR", {"currency": "USD"}), ("USD 5 EUR", {})],
)
def test_conflicting_currencies_raise(text: str, kwargs: dict[str, str]) -> None:
    with pytest.raises(CurrencyConflictError):
        parse(text, **kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "text",
    ["-5 EUR", "\N{MINUS SIGN}5 EUR", "(5) EUR", "EUR (5)", "5- EUR", "EUR 5-", "€-5", "-€5"],
)
def test_every_negative_form(text: str) -> None:
    assert parse(text) == Money("-5", "EUR")


@pytest.mark.parametrize("text", ["--5", "-(5)", "(5)-", "(-5)"])
def test_double_signs_are_rejected(text: str) -> None:
    with pytest.raises(MoneyParseError):
        parse(text)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("$1.2k", "1200"),
        ("1.5 M USD", "1500000"),
        ("USD 2bn", "2000000000"),
        ("€3 million", "3000000"),
        ("0.25tn EUR", "250000000000"),
        ("1.2345k EUR", "1234.5"),
    ],
)
def test_magnitude_suffixes(text: str, expected: str) -> None:
    money = parse(text, magnitude=True, currency=None if "$" not in text else "USD")
    assert str(money.amount) == expected


def test_magnitude_is_opt_in() -> None:
    with pytest.raises(MoneyParseError):
        parse("1.2k USD")


@pytest.mark.parametrize(("text", "code"), [("¥1.5", "JPY"), ("$0.001", "USD")])
def test_strict_minor_rejects_extra_precision(text: str, code: str) -> None:
    assert parse(text, currency=code).currency == code
    with pytest.raises(MinorUnitError):
        parse(text, currency=code, strict_minor=True)


def test_strict_minor_accepts_trailing_zeros_and_metals() -> None:
    assert parse("10.500 USD", strict_minor=True, decimal=".").amount == Decimal("10.500")
    assert parse("1.23456 XAU", strict_minor=True).amount == Decimal("1.23456")
    assert parse("1.2345 CLF", strict_minor=True).amount == Decimal("1.2345")


def test_hint_fills_a_missing_currency_and_require_currency() -> None:
    assert parse("12.50", currency="eur") == Money("12.50", "EUR")
    with pytest.raises(MoneyParseError):
        parse("12.50", require_currency=True)


@pytest.mark.parametrize(
    "text", ["", "   ", "abc", "EUR", "1.2.3,4,5", "1,23,456.78", "12 34,5", "1,234.5.6"]
)
def test_not_money(text: str) -> None:
    with pytest.raises(MoneyParseError):
        parse(text)


def test_bad_arguments() -> None:
    with pytest.raises(UnknownCurrencyError):
        parse("5", currency="ZZZ")
    with pytest.raises(UnknownLocaleError):
        parse("5", locale="xx-YY")
    with pytest.raises(ValueError):
        parse("5", decimal=",", group=",")
    with pytest.raises(ValueError):
        parse("5", decimal="ab")
    with pytest.raises(TypeError):
        parse(5)  # type: ignore[arg-type]


def test_error_hierarchy() -> None:
    for error in (AmbiguousSeparatorError, AmbiguousCurrencyError, MinorUnitError):
        assert issubclass(error, MoneyParseError)
    assert issubclass(MoneyParseError, MoneyError)
    assert issubclass(MoneyError, ValueError)


def test_locale_rejects_the_other_convention() -> None:
    with pytest.raises(MoneyParseError):
        parse("1,234.56", locale="de-DE")
    assert parse("1.234,56", locale="de-DE").amount == Decimal("1234.56")

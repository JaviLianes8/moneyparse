"""Regressions for edge cases found in review: ranges, huge amounts, magnitudes."""

from __future__ import annotations

from decimal import Decimal

import pytest

from moneyparse import (
    AmbiguousSeparatorError,
    Money,
    MoneyError,
    MoneyParseError,
    UnknownCurrencyError,
    find_money,
    format_money,
    get_currency,
    parse,
    parse_money,
)
from moneyparse._cli import main


@pytest.mark.parametrize(
    ("text", "kwargs", "expected"),
    [
        ("costs 5-10 EUR each", {}, [("10 EUR", "10")]),
        ("costs 5 USD-10 USD", {}, [("5 USD", "5"), ("10 USD", "10")]),
        ("range $5-$10", {"currency": "USD"}, [("$5", "5"), ("$10", "10")]),
        ("x-5 EUR", {}, [("5 EUR", "5")]),
        ("balance: 5 EUR- 3 EUR", {}, [("5 EUR", "5"), ("3 EUR", "3")]),
        ("EUR5 and 5EUR", {}, [("EUR5", "5"), ("5EUR", "5")]),
    ],
)
def test_hyphens_and_ranges_are_not_minus_signs(
    text: str, kwargs: dict[str, str], expected: list[tuple[str, str]]
) -> None:
    found = find_money(text, **kwargs)  # type: ignore[arg-type]
    assert [(m.text, str(m.money.amount)) for m in found] == expected


def test_phone_numbers_and_dates_stay_positive() -> None:
    found = find_money("phone 555-1234 or 2024-01-01", require_currency=False)
    assert all(m.money.amount >= 0 for m in found)


def test_real_signs_still_work_in_text() -> None:
    found = find_money("€-5 and -€5 and 5 EUR- due, € -3")
    assert [str(m.money.amount) for m in found] == ["-5", "-5", "-5", "-3"]


def test_magnitude_does_not_settle_separators_by_minor_units() -> None:
    with pytest.raises(AmbiguousSeparatorError):
        parse("$1.234k", currency="USD", magnitude=True, strict_minor=True)
    assert parse("$1.234k", currency="USD", magnitude=True, decimal=".").amount == 1234


@pytest.mark.parametrize("digits", [30, 60])
def test_long_amounts_stay_exact(digits: int) -> None:
    nines = "9" * digits
    assert str(parse(f"-{nines} USD").amount) == f"-{nines}"
    assert str(parse(f"${nines}", currency="USD", strict_minor=True).amount) == nines
    money = Money(nines, "USD")
    assert str((money * 3).amount) == str(int(nines) * 3)
    assert str((money + Money("0.01", "USD")).amount) == f"{nines}.01"
    assert str(money.quantize().amount) == f"{nines}.00"
    assert money.to_minor() == int(nines) * 100
    assert format_money(money).startswith("$999,999")
    assert str(parse(f"{nines}k EUR", magnitude=True).amount) == f"{nines}000"


def test_cli_reports_huge_amounts_without_traceback(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["format", "1e40", "--currency", "USD"]) == 0
    assert capsys.readouterr().out.startswith("$10,000,000,000")


def test_sum_starts_from_zero() -> None:
    assert sum([Money("1.10", "EUR"), Money("2.20", "EUR")]) == Money("3.30", "EUR")
    with pytest.raises(TypeError):
        _ = 1 + Money("1", "EUR")  # type: ignore[operator]


def test_currency_named_twice_is_rejected() -> None:
    for text in ("€€5", "USD USD 5"):
        with pytest.raises(MoneyParseError):
            parse(text)
    with pytest.raises(MoneyParseError):
        parse("$5$", currency="USD")


def test_group_alone_must_be_dot_or_comma() -> None:
    with pytest.raises(ValueError):
        parse("1 234,56", group=" ")
    assert parse("1 234,56", decimal=",", group=" ").amount == Decimal("1234.56")


def test_format_accepts_a_lower_case_matching_code() -> None:
    assert format_money(Money(1, "USD"), "usd") == "$1.00"
    with pytest.raises(ValueError):
        format_money(Money(1, "USD"), "eur")


def test_get_currency_rejects_other_types() -> None:
    with pytest.raises(UnknownCurrencyError):
        get_currency(1.0)  # type: ignore[arg-type]


def test_error_hints_match_the_function() -> None:
    with pytest.raises(AmbiguousSeparatorError) as modern:
        parse("1,234")
    assert "decimal_comma" not in str(modern.value)
    with pytest.raises(AmbiguousSeparatorError) as legacy:
        parse_money("1,234")
    assert "decimal_comma" in str(legacy.value)
    assert legacy.value.separator == ","


def test_multi_digit_head_with_leading_zero_stays_ambiguous() -> None:
    with pytest.raises(AmbiguousSeparatorError):
        parse("06,679")
    with pytest.raises(MoneyError):
        parse_money("084,357")

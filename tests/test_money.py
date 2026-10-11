from decimal import Decimal

import pytest

from moneyparse import MoneyParseError, parse_money


def test_us_format_with_thousands_and_decimal() -> None:
    assert parse_money("1,234.56") == (Decimal("1234.56"), None)


def test_eu_format_with_thousands_and_decimal() -> None:
    assert parse_money("1.234,56") == (Decimal("1234.56"), None)


def test_leading_symbol_maps_to_iso_code() -> None:
    assert parse_money("$10") == (Decimal("10"), "USD")


def test_euro_symbol_with_eu_format() -> None:
    assert parse_money("€1.234,56") == (Decimal("1234.56"), "EUR")


def test_trailing_iso_code() -> None:
    assert parse_money("10 USD") == (Decimal("10"), "USD")


def test_leading_iso_code() -> None:
    assert parse_money("USD 10") == (Decimal("10"), "USD")


def test_parenthesised_negative() -> None:
    assert parse_money("($1,234.56)") == (Decimal("-1234.56"), "USD")


def test_trailing_minus_negative() -> None:
    assert parse_money("1234.56-") == (Decimal("-1234.56"), None)


def test_leading_minus_negative() -> None:
    assert parse_money("-42.50") == (Decimal("-42.50"), None)


def test_surrounding_whitespace_is_ignored() -> None:
    assert parse_money("   $ 1,234.56   ") == (Decimal("1234.56"), "USD")


def test_internal_space_groups_thousands() -> None:
    assert parse_money("1 234,56") == (Decimal("1234.56"), None)


def test_no_currency_returns_none() -> None:
    amount, currency = parse_money("42.50")
    assert amount == Decimal("42.50")
    assert currency is None


def test_integer_with_grouped_thousands() -> None:
    assert parse_money("1,234,567") == (Decimal("1234567"), None)


def test_ambiguous_comma_requires_hint() -> None:
    with pytest.raises(MoneyParseError):
        parse_money("1,234")


def test_ambiguous_dot_requires_hint() -> None:
    with pytest.raises(MoneyParseError):
        parse_money("1.234")


def test_hint_comma_is_decimal() -> None:
    assert parse_money("1,234", decimal_comma=True) == (Decimal("1.234"), None)


def test_hint_comma_is_thousands() -> None:
    assert parse_money("1,234", decimal_comma=False) == (Decimal("1234"), None)


def test_four_digit_tail_is_decimal_not_grouping() -> None:
    assert parse_money("1234,567") == (Decimal("1234.567"), None)


def test_decimal_precision_is_exact() -> None:
    amount, _ = parse_money("0.10")
    assert amount == Decimal("0.10")
    assert str(amount) == "0.10"


def test_empty_string_raises() -> None:
    with pytest.raises(MoneyParseError):
        parse_money("   ")


def test_non_numeric_raises() -> None:
    with pytest.raises(MoneyParseError):
        parse_money("abc")


def test_invalid_grouping_raises() -> None:
    with pytest.raises(MoneyParseError):
        parse_money("1,23,456.78")

"""Money: frozen value type, exact arithmetic, same-currency rules, minor units."""

from __future__ import annotations

import dataclasses
from decimal import ROUND_DOWN, Decimal

import pytest

from moneyparse import (
    CurrencyMismatchError,
    MinorUnitError,
    Money,
    MoneyError,
    UnknownCurrencyError,
)


def test_construction_coerces_and_normalises() -> None:
    money = Money("12.30", "usd")
    assert money.amount == Decimal("12.30")
    assert str(money.amount) == "12.30"
    assert money.currency == "USD"
    assert Money(5).currency is None


@pytest.mark.parametrize("bad", [1.5, True, None, [1]])
def test_floats_and_other_types_are_refused(bad: object) -> None:
    with pytest.raises(TypeError):
        Money(bad)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", ["nan", "inf", "-Infinity", "1,5", "abc"])
def test_non_finite_or_non_decimal_text_is_refused(bad: str) -> None:
    with pytest.raises(MoneyError):
        Money(bad)  # type: ignore[arg-type]


def test_unknown_or_numeric_currency_is_refused() -> None:
    with pytest.raises(UnknownCurrencyError):
        Money(1, "ABC")
    with pytest.raises(MoneyError):
        Money(1, "840")


def test_frozen_and_hashable_with_value_equality() -> None:
    money = Money("1.0", "EUR")
    with pytest.raises(dataclasses.FrozenInstanceError):
        money.amount = Decimal(2)  # type: ignore[misc]
    assert money == Money("1.00", "EUR")
    assert len({money, Money("1.00", "EUR")}) == 1
    assert money != Money("1.0", "USD")


def test_arithmetic_is_exact() -> None:
    total = Money("0.10", "USD") + Money("0.20", "USD")
    assert total == Money("0.30", "USD")
    assert Money("1", "USD") - Money("0.01", "USD") == Money("0.99", "USD")
    assert Money("2.50", "USD") * 3 == 3 * Money("2.50", "USD") == Money("7.50", "USD")
    assert Money("2.50", "USD") * Decimal("0.5") == Money("1.25", "USD")
    assert -Money("5", "EUR") == Money("-5", "EUR")
    assert +Money("5", "EUR") == Money("5", "EUR")
    assert abs(Money("-5", "EUR")) == Money("5", "EUR")
    assert not Money("0", "EUR")
    assert Money("0.01", "EUR")


def test_mixing_currencies_is_refused() -> None:
    with pytest.raises(CurrencyMismatchError):
        Money(1, "USD") + Money(1, "EUR")
    with pytest.raises(CurrencyMismatchError):
        Money(1, "USD") - Money(1)
    with pytest.raises(CurrencyMismatchError):
        assert Money(1, "USD") < Money(2, "EUR")
    with pytest.raises(TypeError):
        Money(1, "USD") + 1  # type: ignore[operator]
    with pytest.raises(TypeError):
        Money(1, "USD") * 1.5  # type: ignore[operator]
    with pytest.raises(TypeError):
        Money(1, "USD") * Money(1, "USD")  # type: ignore[operator]


def test_ordering_within_one_currency() -> None:
    small, big = Money("1.00", "EUR"), Money("1.01", "EUR")
    assert small < big and small <= big and big > small and big >= small
    assert sorted([big, small]) == [small, big]


@pytest.mark.parametrize(
    ("amount", "code", "expected"),
    [
        ("2.675", "USD", "2.68"),
        ("2.665", "USD", "2.66"),
        ("1.5", "JPY", "2"),
        ("1.0005", "KWD", "1.000"),
    ],
)
def test_quantize_uses_bankers_rounding(amount: str, code: str, expected: str) -> None:
    assert str(Money(amount, code).quantize().amount) == expected


def test_quantize_accepts_a_rounding_mode() -> None:
    assert Money("2.679", "USD").quantize(ROUND_DOWN) == Money("2.67", "USD")


def test_minor_units() -> None:
    assert Money("12.34", "USD").to_minor() == 1234
    assert Money("-1.234", "BHD").to_minor() == -1234
    assert Money("1234", "JPY").to_minor() == 1234
    assert Money.from_minor(1234, "USD") == Money("12.34", "USD")
    assert Money.from_minor(12345, "CLF") == Money("1.2345", "CLF")
    assert Money("1", "JPY").minor_units == 0
    assert Money("1").minor_units is None
    with pytest.raises(MinorUnitError):
        Money("12.345", "USD").to_minor()
    with pytest.raises(MinorUnitError):
        Money("1", "XAU").to_minor()
    with pytest.raises(MinorUnitError):
        Money.from_minor(1, "XDR")
    with pytest.raises(TypeError):
        Money.from_minor(1.5, "USD")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("amount", "ratios", "expected"),
    [
        ("100.00", [1, 1, 1], ["33.34", "33.33", "33.33"]),
        ("0.05", [3, 7], ["0.02", "0.03"]),
        ("-0.05", [1, 1], ["-0.03", "-0.02"]),
        ("10", [0, 1], ["0.00", "10.00"]),
        ("0.01", [0, 1, 1], ["0.00", "0.01", "0.00"]),
    ],
)
def test_allocate_never_loses_a_cent(amount: str, ratios: list[int], expected: list[str]) -> None:
    parts = Money(amount, "EUR").allocate(ratios)
    assert [str(part.amount) for part in parts] == expected
    assert (
        sum((part.amount for part in parts), Decimal(0)) == Money(amount, "EUR").quantize().amount
    )


@pytest.mark.parametrize("ratios", [[], [0, 0], [-1, 2]])
def test_allocate_rejects_bad_ratios(ratios: list[int]) -> None:
    with pytest.raises((TypeError, ValueError)):
        Money("1", "EUR").allocate(ratios)


def test_str_and_repr() -> None:
    assert str(Money("12.50", "EUR")) == "12.50 EUR"
    assert str(Money("12.50")) == "12.50"
    assert repr(Money("1", "EUR")) == "Money(amount=Decimal('1'), currency='EUR')"

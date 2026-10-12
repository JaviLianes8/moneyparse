"""find_money(): amounts in free text, with exact spans."""

from __future__ import annotations

from decimal import Decimal

import pytest

from moneyparse import AmbiguousCurrencyError, Money, MoneyMatch, find_money

TEXT = (
    "Invoice 7: total €1.234,56 (was 1\N{NARROW NO-BREAK SPACE}500,00 EUR), "
    "fee USD 3.99, refund ($12.00), 5 apples, budget $1.2k or 3 bn JPY."
)


def _pairs(matches: list[MoneyMatch]) -> list[tuple[str, Money]]:
    return [(m.text, m.money) for m in matches]


def test_spans_point_at_the_matched_text() -> None:
    for match in find_money(TEXT, errors="skip"):
        assert TEXT[match.start : match.end] == match.text


def test_finds_amounts_without_a_locale() -> None:
    assert _pairs(find_money(TEXT, errors="skip")) == [
        ("€1.234,56", Money("1234.56", "EUR")),
        ("1\N{NARROW NO-BREAK SPACE}500,00 EUR", Money("1500.00", "EUR")),
        ("USD 3.99", Money("3.99", "USD")),
    ]


def test_locale_and_magnitude() -> None:
    found = _pairs(find_money(TEXT, locale="en-US", magnitude=True, errors="skip"))
    assert found == [
        ("USD 3.99", Money("3.99", "USD")),
        ("($12.00)", Money("-12.00", "USD")),
        ("$1.2k", Money("1200", "USD")),
        ("3 bn JPY", Money("3000000000", "JPY")),
    ]


def test_errors_raise_by_default() -> None:
    with pytest.raises(AmbiguousCurrencyError):
        find_money("refund ($12.00)")


def test_never_stops_inside_a_word_or_number() -> None:
    text = "budget $1.2k, $1.25.3, A4 USD, MP3 EUR"
    assert find_money(text, locale="en-US", errors="skip") == []


def test_letter_symbols_need_word_boundaries() -> None:
    text = "Rp5.000 then Krp5 and 7 kr."
    found = _pairs(find_money(text, locale="id-ID", errors="skip"))
    assert found == [("Rp5.000", Money("5000", "IDR"))]
    assert _pairs(find_money("7 kr.", locale="da-DK")) == [("7 kr.", Money("7", "DKK"))]


def test_unbalanced_parenthesis_is_left_out_of_the_span() -> None:
    text = "(about €5 in total)"
    [match] = find_money(text)
    assert match.text == "€5"
    assert text[match.start : match.end] == "€5"


def test_trailing_minus_only_when_not_a_range() -> None:
    assert _pairs(find_money("€5-10")) == [("€5", Money("5", "EUR"))]
    assert _pairs(find_money("balance: 5 EUR- due")) == [("5 EUR-", Money("-5", "EUR"))]


def test_bare_numbers_need_require_currency_false() -> None:
    assert find_money("3 apples cost 4.50") == []
    found = find_money("3 apples cost 4.50", require_currency=False, currency="EUR")
    assert [m.money for m in found] == [Money("3", "EUR"), Money("4.50", "EUR")]


def test_currency_hint_and_strict_minor_flow_through() -> None:
    assert find_money("pay ¥1,500", currency="JPY", locale="ja-JP")[0].money.amount == 1500
    assert find_money("¥1.5", currency="JPY", strict_minor=True, errors="skip") == []


def test_bad_errors_argument() -> None:
    with pytest.raises(ValueError):
        find_money("x", errors="ignore")  # type: ignore[arg-type]


def test_lowercase_codes_are_not_currency_in_text() -> None:
    assert find_money("all 5 try 3 top 2") == []
    assert find_money("ALL 5")[0].money == Money(Decimal(5), "ALL")

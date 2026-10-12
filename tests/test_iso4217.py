"""The embedded ISO 4217 table and the CLDR locale table."""

from __future__ import annotations

import pytest

from moneyparse import (
    ISO4217_PUBLISHED,
    Currency,
    UnknownCurrencyError,
    UnknownLocaleError,
    currencies,
    get_currency,
    get_locale,
    locales,
)

# (code, numeric, minor units) as printed in ISO 4217 List One, 2026-09-17.
KNOWN = [
    ("USD", "840", 2),
    ("EUR", "978", 2),
    ("JPY", "392", 0),
    ("KRW", "410", 0),
    ("KWD", "414", 3),
    ("BHD", "048", 3),
    ("TND", "788", 3),
    ("CLF", "990", 4),
    ("UYW", "927", 4),
    ("ALL", "008", 2),
    ("XAU", "959", None),
    ("XDR", "960", None),
    ("XCG", "532", 2),
    ("ZWG", "924", 2),
    ("SLE", "925", 2),
]


def test_publication_date_and_size() -> None:
    assert ISO4217_PUBLISHED == "2026-09-17"
    table = currencies()
    assert len(table) == 178
    assert [c.code for c in table] == sorted(c.code for c in table)
    assert len({c.numeric for c in table}) == len(table)


@pytest.mark.parametrize(("code", "numeric", "units"), KNOWN)
def test_known_rows(code: str, numeric: str, units: int | None) -> None:
    currency = get_currency(code)
    assert currency == Currency(code, numeric, units, currency.name)
    assert get_currency(numeric) is currency
    assert get_currency(int(numeric)) is currency
    assert get_currency(code.lower()) is currency


@pytest.mark.parametrize("code", ["HRK", "SLL", "ZWL", "VEF", "XXY", "", "1000", -1, True])
def test_withdrawn_and_invalid_codes(code: str | int) -> None:
    with pytest.raises(UnknownCurrencyError):
        get_currency(code)


def test_every_row_is_well_formed() -> None:
    for currency in currencies():
        assert len(currency.code) == 3 and currency.code.isupper()
        assert len(currency.numeric) == 3 and currency.numeric.isdigit()
        assert currency.minor_units in (None, 0, 2, 3, 4)
        assert currency.name


def test_locale_lookup() -> None:
    assert len(locales()) == 33
    assert get_locale("de_ch").tag == "de-CH"
    assert get_locale("DE").tag == "de-DE"
    assert get_locale("pt").tag == "pt-BR"
    assert get_locale("en").tag == "en-US"
    fr = get_locale("fr-FR")
    assert (fr.decimal, fr.group) == (",", "\N{NARROW NO-BREAK SPACE}")
    assert get_locale("sv-SE").minus == "\N{MINUS SIGN}"
    assert get_locale("es-ES").min_grouping == 2
    assert get_locale("en-IN").indian_grouping
    assert not get_locale("en-US").indian_grouping
    assert get_locale("en-CA").symbol_for("USD") == "US$"
    assert get_locale("en-US").symbol_for("JPY") is None


@pytest.mark.parametrize("tag", ["xx", "de-XX", "", "en-US-x"])
def test_unknown_locales(tag: str) -> None:
    with pytest.raises(UnknownLocaleError):
        get_locale(tag)

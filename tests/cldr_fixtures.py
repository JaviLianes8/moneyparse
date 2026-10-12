"""Ground-truth fixtures built from Unicode CLDR 48 and ISO 4217.

Each formatted string follows the locale's CLDR 48 data in ``cldr-numbers-full``
(github.com/unicode-org/cldr-json): ``symbols-numberSystem-latn`` (decimal, group,
minusSign), ``minimumGroupingDigits``, ``currencyFormats-numberSystem-latn``
(standard and accounting patterns) and the locale's ``currencies`` symbols, plus the
CLDR currencySpacing rule (a no-break space between a letter-edged currency and a
digit). Fraction digits are the ISO 4217 minor units (List One, SIX, 2026-09-17).
Rows: (locale, amount, currency, accounting, expected text).
"""

from __future__ import annotations

from decimal import Decimal

NBSP = "\xa0"
NNBSP = "\N{NARROW NO-BREAK SPACE}"
MINUS = "\N{MINUS SIGN}"
D = Decimal

FORMATTED: list[tuple[str, Decimal, str, bool, str]] = [
    ("en-US", D("1234.56"), "USD", False, "$1,234.56"),
    ("en-US", D("-1234.56"), "USD", False, "-$1,234.56"),
    ("en-US", D("-1234.56"), "USD", True, "($1,234.56)"),
    ("en-US", D("1234.56"), "EUR", False, "€1,234.56"),
    ("en-US", D("1234.5"), "KWD", False, f"KWD{NBSP}1,234.500"),
    ("en-US", D("1.23456"), "CLF", False, f"CLF{NBSP}1.2346"),
    ("en-US", D("1234"), "JPY", False, f"JPY{NBSP}1,234"),
    ("en-GB", D("1234.56"), "GBP", False, "£1,234.56"),
    ("en-GB", D("1234.56"), "USD", False, "US$1,234.56"),
    ("en-CA", D("1234.56"), "CAD", False, "$1,234.56"),
    ("en-CA", D("1234.56"), "USD", False, "US$1,234.56"),
    ("en-AU", D("1234.56"), "USD", False, f"USD{NBSP}1,234.56"),
    ("en-IN", D("12345678.9"), "INR", False, "₹1,23,45,678.90"),
    ("hi-IN", D("123456.78"), "INR", False, "₹1,23,456.78"),
    ("de-DE", D("1234.56"), "EUR", False, f"1.234,56{NBSP}€"),
    ("de-DE", D("-1234.56"), "EUR", False, f"-1.234,56{NBSP}€"),
    ("de-CH", D("1234.5"), "CHF", False, f"CHF{NBSP}1'234.50"),
    ("de-CH", D("-1234.5"), "CHF", False, "CHF-1'234.50"),
    ("de-AT", D("1234.56"), "EUR", False, f"€{NBSP}1.234,56"),
    ("fr-FR", D("1234.56"), "EUR", False, f"1{NNBSP}234,56{NBSP}€"),
    ("fr-FR", D("-1234.56"), "EUR", True, f"(1{NNBSP}234,56{NBSP}€)"),
    ("fr-FR", D("5"), "USD", False, f"5,00{NBSP}$US"),
    ("fr-CH", D("1234.56"), "CHF", False, f"1'234.56{NBSP}CHF"),
    ("fr-CA", D("1234.56"), "CAD", False, f"1{NBSP}234,56{NBSP}$"),
    ("es-ES", D("1234.56"), "EUR", False, f"1234,56{NBSP}€"),
    ("es-ES", D("12345.67"), "EUR", False, f"12.345,67{NBSP}€"),
    ("es-MX", D("1234.56"), "MXN", False, "$1,234.56"),
    ("it-IT", D("1234.56"), "EUR", False, f"1234,56{NBSP}€"),
    ("it-CH", D("-12345.5"), "CHF", False, "CHF-12'345.50"),
    ("pt-BR", D("1234.56"), "BRL", False, f"R${NBSP}1.234,56"),
    ("pt-PT", D("1234.56"), "EUR", False, f"1234,56{NBSP}€"),
    ("nl-NL", D("1234.56"), "EUR", False, f"€{NBSP}1.234,56"),
    ("nl-NL", D("-1234.56"), "EUR", False, f"€{NBSP}-1.234,56"),
    ("nl-NL", D("-1234.56"), "EUR", True, f"(€{NBSP}1.234,56)"),
    ("sv-SE", D("1234.56"), "SEK", False, f"1{NBSP}234,56{NBSP}kr"),
    ("sv-SE", D("-1234.56"), "SEK", False, f"{MINUS}1{NBSP}234,56{NBSP}kr"),
    ("nb-NO", D("-1234.56"), "NOK", False, f"{MINUS}1{NBSP}234,56{NBSP}kr"),
    ("nb-NO", D("-1234.56"), "NOK", True, f"(kr{NBSP}1{NBSP}234,56)"),
    ("da-DK", D("1234.56"), "DKK", False, f"1.234,56{NBSP}kr."),
    ("fi-FI", D("-1234.56"), "EUR", False, f"{MINUS}1{NBSP}234,56{NBSP}€"),
    ("pl-PL", D("1234.56"), "PLN", False, f"1234,56{NBSP}zł"),
    ("cs-CZ", D("1234.56"), "CZK", False, f"1{NBSP}234,56{NBSP}Kč"),
    ("ru-RU", D("1234.56"), "RUB", False, f"1{NBSP}234,56{NBSP}₽"),
    ("uk-UA", D("1234.56"), "UAH", False, f"1{NBSP}234,56{NBSP}₴"),
    ("tr-TR", D("1234.56"), "TRY", False, "₺1.234,56"),
    ("ja-JP", D("1234.56"), "JPY", False, "\N{FULLWIDTH YEN SIGN}1,235"),
    ("zh-CN", D("1234.56"), "CNY", False, "¥1,234.56"),
    ("ko-KR", D("1234.5"), "KRW", False, "₩1,234"),
    ("id-ID", D("1234.56"), "IDR", False, f"Rp{NBSP}1.234,56"),
    ("th-TH", D("-1234.56"), "THB", True, "(฿1,234.56)"),
]

# Strings people actually type, with the value they mean. Rows: (locale or None,
# currency hint or None, text, amount, currency).
TYPED: list[tuple[str | None, str | None, str, Decimal, str | None]] = [
    (None, None, "1.234,56 €", D("1234.56"), "EUR"),
    (None, None, "€1.234,56", D("1234.56"), "EUR"),
    (None, None, "1,234.56 EUR", D("1234.56"), "EUR"),
    (None, None, "USD (42.00)", D("-42.00"), "USD"),
    (None, None, "1,234.00-", D("-1234.00"), None),
    (None, "USD", "(1,234.00)", D("-1234.00"), "USD"),
    (None, None, "CHF 1\N{RIGHT SINGLE QUOTATION MARK}234.50", D("1234.50"), "CHF"),
    (None, None, "1 234,56 €", D("1234.56"), "EUR"),
    ("fr-FR", None, "1 234,56 €", D("1234.56"), "EUR"),
    ("en-IN", None, "1,23,45,678.90", D("12345678.90"), None),
    ("en-IN", None, "Rs. 1,23,456", D("123456"), "INR"),
    ("en-US", None, "-$1,234.56", D("-1234.56"), "USD"),
    ("en-US", None, "$-1,234.56", D("-1234.56"), "USD"),
    ("en-CA", None, "$12.50", D("12.50"), "CAD"),
    ("sv-SE", None, "-1 234,56 kr", D("-1234.56"), "SEK"),
    ("da-DK", None, "kr. 1.234,56", D("1234.56"), "DKK"),
    ("ja-JP", None, "¥1,234", D("1234"), "JPY"),
    ("zh-CN", None, "¥1,234.50", D("1234.50"), "CNY"),
    (None, "JPY", "¥1.234.567", D("1234567"), "JPY"),
    (None, None, "US$5", D("5"), "USD"),
    (None, None, "R$ 10,00", D("10.00"), "BRL"),
    (
        None,
        None,
        "\N{ARABIC-INDIC DIGIT ONE}\N{ARABIC THOUSANDS SEPARATOR}234 KWD",
        D("1234"),
        "KWD",
    ),
    (None, None, "0,125 BHD", D("0.125"), "BHD"),
]

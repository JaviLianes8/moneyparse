"""Number and currency conventions of common locales, from Unicode CLDR 48.

Source: CLDR 48.2 JSON (github.com/unicode-org/cldr-json 48.2.3, ``cldr-numbers-full``),
``symbols-numberSystem-latn``, ``minimumGroupingDigits``,
``currencyFormats-numberSystem-latn`` (standard and accounting) and the locale's own
currency symbols. ``_SEPARATORS`` columns: tag, decimal, group, minus sign, minimum
grouping digits, home currency, its local symbol, the local symbols of USD and EUR.
``_PATTERNS`` columns: tag, standard currency pattern, accounting currency pattern.
"""

from __future__ import annotations

from dataclasses import dataclass

from ._errors import UnknownLocaleError

# CLDR ``currencyDecimal`` / ``currencyGroup``: separators that replace the plain
# ones inside currency amounts. Only these two embedded locales define them.
_CURRENCY_SEPARATORS = {"de-AT": (",", "."), "fr-CH": (".", "'")}

_SEPARATORS = """\
en-US|.|,|-|1|USD|$|$|€
en-GB|.|,|-|1|GBP|£|US$|€
en-IN|.|,|-|1|INR|₹|$|€
en-CA|.|,|-|1|CAD|$|US$|€
en-AU|.|,|-|1|AUD|$|USD|EUR
de-DE|,|.|-|1|EUR|€|$|€
de-CH|.|'|-|1|CHF|CHF|$|EUR
de-AT|,|\xa0|-|1|EUR|€|$|€
fr-FR|,|\u202f|-|1|EUR|€|$US|€
fr-CH|,|'|-|1|CHF|CHF|$US|€
fr-CA|,|\xa0|-|1|CAD|$|$\xa0US|€
es-ES|,|.|-|2|EUR|€|US$|€
es-MX|.|,|-|1|MXN|$|USD|EUR
it-IT|,|.|-|2|EUR|€|USD|€
it-CH|.|'|-|2|CHF|CHF|USD|€
pt-BR|,|.|-|1|BRL|R$|US$|€
pt-PT|,|\xa0|-|2|EUR|€|US$|€
nl-NL|,|.|-|1|EUR|€|US$|€
sv-SE|,|\xa0|\u2212|1|SEK|kr|US$|€
nb-NO|,|\xa0|\u2212|1|NOK|kr|USD|€
da-DK|,|.|-|1|DKK|kr.|US$|€
fi-FI|,|\xa0|\u2212|1|EUR|€|$|€
pl-PL|,|\xa0|-|2|PLN|z\u0142|USD|€
cs-CZ|,|\xa0|-|1|CZK|K\u010d|US$|€
ru-RU|,|\xa0|-|1|RUB|₽|$|€
uk-UA|,|\xa0|-|1|UAH|₴|USD|EUR
tr-TR|,|.|-|1|TRY|₺|$|€
ja-JP|.|,|-|1|JPY|\uffe5|$|€
zh-CN|.|,|-|1|CNY|¥|US$|€
ko-KR|.|,|-|1|KRW|₩|US$|€
hi-IN|.|,|-|1|INR|₹|$|€
id-ID|,|.|-|1|IDR|Rp|US$|€
th-TH|.|,|-|1|THB|฿|US$|€
"""

_PATTERNS = """\
en-US|\xa4#,##0.00|\xa4#,##0.00;(\xa4#,##0.00)
en-GB|\xa4#,##0.00|\xa4#,##0.00;(\xa4#,##0.00)
en-IN|\xa4#,##,##0.00|\xa4#,##0.00;(\xa4#,##0.00)
en-CA|\xa4#,##0.00|\xa4#,##0.00;(\xa4#,##0.00)
en-AU|\xa4#,##0.00|\xa4#,##0.00;(\xa4#,##0.00)
de-DE|#,##0.00\xa0\xa4|#,##0.00\xa0\xa4
de-CH|\xa4\xa0#,##0.00;\xa4-#,##0.00|\xa4\xa0#,##0.00;\xa4-#,##0.00
de-AT|\xa4\xa0#,##0.00|\xa4\xa0#,##0.00
fr-FR|#,##0.00\xa0\xa4|#,##0.00\xa0\xa4;(#,##0.00\xa0\xa4)
fr-CH|#,##0.00\xa0\xa4|#,##0.00\xa0\xa4;(#,##0.00\xa0\xa4)
fr-CA|#,##0.00\xa0\xa4|#,##0.00\xa0\xa4;(#,##0.00\xa0\xa4)
es-ES|#,##0.00\xa0\xa4|#,##0.00\xa0\xa4
es-MX|\xa4#,##0.00|\xa4#,##0.00
it-IT|#,##0.00\xa0\xa4|#,##0.00\xa0\xa4
it-CH|\xa4\xa0#,##0.00;\xa4-#,##0.00|\xa4\xa0#,##0.00;\xa4-#,##0.00
pt-BR|\xa4\xa0#,##0.00|\xa4\xa0#,##0.00
pt-PT|#,##0.00\xa0\xa4|#,##0.00\xa0\xa4;(#,##0.00\xa0\xa4)
nl-NL|\xa4\xa0#,##0.00;\xa4\xa0-#,##0.00|\xa4\xa0#,##0.00;(\xa4\xa0#,##0.00)
sv-SE|#,##0.00\xa0\xa4|#,##0.00\xa0\xa4
nb-NO|#,##0.00\xa0\xa4;-#,##0.00\xa0\xa4|\xa4\xa0#,##0.00;(\xa4\xa0#,##0.00)
da-DK|#,##0.00\xa0\xa4|#,##0.00\xa0\xa4
fi-FI|#,##0.00\xa0\xa4|#,##0.00\xa0\xa4
pl-PL|#,##0.00\xa0\xa4|#,##0.00\xa0\xa4;(#,##0.00\xa0\xa4)
cs-CZ|#,##0.00\xa0\xa4|#,##0.00\xa0\xa4
ru-RU|#,##0.00\xa0\xa4|#,##0.00\xa0\xa4
uk-UA|#,##0.00\xa0\xa4|#,##0.00\xa0\xa4
tr-TR|\xa4#,##0.00|\xa4#,##0.00;(\xa4#,##0.00)
ja-JP|\xa4#,##0.00|\xa4#,##0.00;(\xa4#,##0.00)
zh-CN|\xa4#,##0.00|\xa4#,##0.00;(\xa4#,##0.00)
ko-KR|\xa4#,##0.00|\xa4#,##0.00;(\xa4#,##0.00)
hi-IN|\xa4#,##,##0.00|\xa4#,##,##0.00
id-ID|\xa4#,##0.00|\xa4#,##0.00
th-TH|\xa4#,##0.00|\xa4#,##0.00;(\xa4#,##0.00)
"""


@dataclass(frozen=True, slots=True)
class Locale:
    """CLDR number and currency conventions of one locale.

    Attributes:
        tag: BCP 47 tag, for example ``"de-CH"``.
        decimal: Decimal separator.
        group: Grouping separator (U+202F, a narrow no-break space, in fr-FR).
        minus: Minus sign (U+2212 in sv-SE, fi-FI and nb-NO).
        min_grouping: CLDR ``minimumGroupingDigits``; 2 means four-digit integers
            stay ungrouped (es-ES writes ``1234,56``).
        currency: The locale's home currency code.
        standard: CLDR standard currency pattern.
        accounting: CLDR accounting currency pattern.
        symbols: How the locale writes its home currency, USD and EUR, as
            ``(symbol, code)`` pairs; a pair whose symbol equals the code means the
            locale writes the bare ISO code (en-AU writes ``USD 5.00``).
        currency_decimal: Decimal separator inside currency amounts (CLDR
            ``currencyDecimal``; ``.`` in fr-CH, else the same as ``decimal``).
        currency_group: Grouping separator inside currency amounts (CLDR
            ``currencyGroup``; ``.`` in de-AT, else the same as ``group``).
    """

    tag: str
    decimal: str
    group: str
    minus: str
    min_grouping: int
    currency: str
    standard: str
    accounting: str
    symbols: tuple[tuple[str, str], ...]
    currency_decimal: str
    currency_group: str

    @property
    def indian_grouping(self) -> bool:
        """True when the standard pattern groups by two above the thousands."""
        return "#,##,##0" in self.standard

    def symbol_for(self, code: str) -> str | None:
        """Return this locale's own symbol for ``code``, if it has one."""
        for symbol, owner in self.symbols:
            if owner == code:
                return symbol
        return None


def _load() -> dict[str, Locale]:
    patterns = {row.split("|")[0]: row.split("|")[1:] for row in _PATTERNS.splitlines()}
    table: dict[str, Locale] = {}
    for row in _SEPARATORS.splitlines():
        tag, dec, grp, minus, min_group, home, home_sym, usd_sym, eur_sym = row.split("|")
        pairs = ((home_sym, home), (usd_sym, "USD"), (eur_sym, "EUR"))
        symbols = tuple(dict.fromkeys(pairs))
        standard, accounting = patterns[tag]
        cur_dec, cur_grp = _CURRENCY_SEPARATORS.get(tag, (dec, grp))
        table[tag.lower()] = Locale(
            tag, dec, grp, minus, int(min_group), home, standard, accounting, symbols,
            cur_dec, cur_grp,
        )  # fmt: skip
    return table


_BY_TAG = _load()
# The first row of each language is its main locale (en-US, de-DE, pt-BR, ...).
_BY_LANGUAGE: dict[str, Locale] = {}
for _locale in _BY_TAG.values():
    _BY_LANGUAGE.setdefault(_locale.tag.split("-")[0].lower(), _locale)


def get_locale(tag: str) -> Locale:
    """Return the embedded CLDR data for ``tag``.

    Tags are case-insensitive and accept ``_`` or ``-`` (``"de_CH"``, ``"de-ch"``).
    A bare language (``"de"``) selects its main locale (``de-DE``); ``"pt"`` is
    ``pt-BR`` and ``"en"`` is ``en-US``, as in CLDR.

    Raises:
        UnknownLocaleError: No embedded data for the tag.
    """
    key = tag.strip().replace("_", "-").lower()
    found = _BY_TAG.get(key) or (_BY_LANGUAGE.get(key) if "-" not in key else None)
    if found is None:
        raise UnknownLocaleError(f"no CLDR data embedded for locale {tag!r}")
    return found


def locales() -> tuple[str, ...]:
    """Return the tags of every embedded locale, sorted."""
    return tuple(sorted(locale.tag for locale in _BY_TAG.values()))

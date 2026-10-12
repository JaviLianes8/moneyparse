"""Currency symbols and the policy that resolves them to ISO 4217 codes.

Symbols come from Unicode CLDR 48.2 (``en`` standard and narrow symbols, plus every
symbol the embedded locales use for an active ISO 4217 code) and a few unambiguous
forms in common use (``US$``, ``AU$``, ``S$``, ``JP¥``). A symbol either has a
single default code or is ambiguous: ``$`` alone is the narrow symbol of 28
currencies, so it is never assumed to be USD. Ambiguous symbols need a ``currency``
hint or a ``locale`` whose CLDR data gives the symbol a meaning (``$`` is CAD in
``en-CA`` and USD in ``de``).
"""

from __future__ import annotations

from collections.abc import Mapping

from ._errors import AmbiguousCurrencyError, CurrencyConflictError

_DOLLARS = (
    "ARS", "AUD", "BBD", "BMD", "BND", "BSD", "BZD", "CAD", "CLP", "COP", "CUP", "DOP",
    "FJD", "GYD", "HKD", "JMD", "KYD", "LRD", "MXN", "NAD", "NZD", "SBD", "SGD", "SRD",
    "TTD", "TWD", "USD", "UYU", "XCD",
)  # fmt: skip
_POUNDS = ("GBP", "FKP", "GIP", "SHP", "SSP", "SYP")
_YEN = ("JPY", "CNY")
_KRONA = ("DKK", "ISK", "NOK", "SEK")
_RUPEE = ("INR", "LKR", "MUR", "NPR", "PKR", "SCR")

_AMBIGUOUS: dict[str, tuple[str, ...]] = {
    "$": tuple(sorted(_DOLLARS)),
    "¥": _YEN,
    "￥": _YEN,
    "kr": _KRONA,
    "kr.": _KRONA,
    "Rs": _RUPEE,
    "Rs.": _RUPEE,
    "C$": ("CAD", "NIO"),
}

_DEFAULTS: dict[str, tuple[str, tuple[str, ...]]] = {
    "£": ("GBP", _POUNDS),
    "₩": ("KRW", ("KRW", "KPW")),
}

_TMT = "\N{CYRILLIC CAPITAL LETTER TE}\N{CYRILLIC CAPITAL LETTER EM}\N{CYRILLIC CAPITAL LETTER TE}"

_SINGLE: dict[str, str] = {
    "US$": "USD", "$US": "USD", "$ US": "USD", "CA$": "CAD", "A$": "AUD",
    "AU$": "AUD", "NZ$": "NZD", "HK$": "HKD", "MX$": "MXN", "NT$": "TWD",
    "EC$": "XCD", "S$": "SGD", "R$": "BRL", "T$": "TOP", "CN¥": "CNY",
    "JP¥": "JPY", "€": "EUR", "₹": "INR", "₽": "RUB", "₺": "TRY", "₴": "UAH",
    "₪": "ILS", "₫": "VND", "₱": "PHP", "฿": "THB", "₦": "NGN", "₡": "CRC",
    "₲": "PYG", "₸": "KZT", "₭": "LAK", "₮": "MNT", "₼": "AZN", "₾": "GEL",
    "֏": "AMD", "৳": "BDT", "៛": "KHR", "؋": "AFN", "zł": "PLN", "Kč": "CZK",
    "Ft": "HUF", "Rp": "IDR", "RM": "MYR", "lei": "RON", "E£": "EGP",
    "L£": "LBP", "GH₵": "GHS", "FCFA": "XAF", "F CFA": "XOF", "CFPF": "XPF",
    "Cg.": "XCG", "CHF": "CHF",
    # Further local symbols used by the embedded CLDR 48.2 locales (fr, es, pt, ...).
    "$ AU": "AUD", "$ HK": "HKD", "$ NZ": "NZD", "$ SG": "SGD", "$AR": "ARS",
    "$AU": "AUD", "$BM": "BMD", "$BN": "BND", "$BZ": "BZD", "$CA": "CAD",
    "$CL": "CLP", "$CO": "COP", "$FJ": "FJD", "$MX": "MXN", "$NA": "NAD",
    "$NZ": "NZD", "$SB": "SBD", "$SG": "SGD", "$SR": "SRD", "$TT": "TTD",
    "$UY": "UYU", "$WS": "WST", "BM$": "BMD", "BR$": "BRL", "BS$": "BSD",
    "BZ$": "BZD", "Bds$": "BBD", "FJ$": "FJD", "JM$": "JMD", "RD$": "DOP",
    "SI$": "SBD", "CFP": "XPF", "FCFP": "XPF", "Cf": "XCG", "Cg": "XCG",
    "Dkr": "DKK", "Ikr": "ISK", "Nkr": "NOK", "EG£": "EGP", "£FK": "FKP",
    "£GB": "GBP", "£GI": "GIP", "£LB": "LBP", "UM": "MRU", "ZiG": "ZWG",
    "元": "CNY", _TMT: "TMT",
}  # fmt: skip


def _candidates_of(symbol: str) -> tuple[str | None, tuple[str, ...]]:
    if symbol in _SINGLE:
        code = _SINGLE[symbol]
        return code, (code,)
    if symbol in _DEFAULTS:
        return _DEFAULTS[symbol]
    return None, _AMBIGUOUS[symbol]


SYMBOLS: tuple[str, ...] = tuple(
    sorted({*_SINGLE, *_DEFAULTS, *_AMBIGUOUS}, key=lambda s: (-len(s), s))
)


def resolve_symbol(
    symbol: str,
    hint: str | None,
    local: Mapping[str, str] | None = None,
    home: str | None = None,
) -> str:
    """Return the ISO code ``symbol`` stands for, given an optional hint and locale.

    Order: the ``hint`` (which must be one of the symbol's candidates), then the
    locale's own symbols (``local``, as CLDR writes them), then the locale's ``home``
    currency when it is a candidate (``Rs`` in en-IN is INR), then the global default.
    """
    default, candidates = _candidates_of(symbol)
    if hint is not None:
        if hint in candidates:
            return hint
        raise CurrencyConflictError(f"symbol {symbol!r} cannot mean {hint}")
    if local and symbol in local:
        return local[symbol]
    if home is not None and home in candidates:
        return home
    if default is not None:
        return default
    raise AmbiguousCurrencyError(symbol, candidates)


def is_ambiguous(symbol: str) -> bool:
    """Return True when ``symbol`` needs a hint or a locale to name one currency."""
    return symbol in _AMBIGUOUS


def symbol_codes(symbol: str) -> tuple[str, ...]:
    """Return every ISO code ``symbol`` can stand for."""
    return _candidates_of(symbol)[1]

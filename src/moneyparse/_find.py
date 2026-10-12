"""Find money amounts in free text and report where each one sits."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from ._currencies import currencies
from ._engine import parse
from ._errors import MoneyError
from ._money import Money
from ._symbols import SYMBOLS
from ._tokens import MAGNITUDES

_SPACE = "[ \\xa0\\u202f\\u2009]"
_LETTER_BEFORE, _LETTER_AFTER = r"(?<![^\W\d_])", r"(?![^\W\d_])"


def _symbol_regex(symbol: str) -> str:
    body = re.escape(symbol).replace("\\ ", _SPACE)
    before = _LETTER_BEFORE if symbol[0].isalpha() else ""
    after = _LETTER_AFTER if symbol[-1].isalpha() else ""
    return before + body + after


_CURRENCY = "|".join(
    [_symbol_regex(symbol) for symbol in SYMBOLS]
    + [rf"(?<![A-Za-z]){c.code}(?![A-Za-z])" for c in currencies()]
)
_MINUS = r"[-\N{MINUS SIGN}]"
_NUMBER = r"\d+(?:(?:[.,'\u2019_]|[ \xa0\u202f\u2009](?=\d{3}(?!\d)))\d+)*"
_MAGNITUDE = "|".join(sorted(MAGNITUDES, key=len, reverse=True))


def _pattern(magnitude: bool) -> re.Pattern[str]:
    mag = rf"(?:{_SPACE}?(?:{_MAGNITUDE})(?![^\W\d_]))?" if magnitude else ""
    return re.compile(
        rf"(?P<open>\()?(?:(?<![\w-])[-\u2212+]{_SPACE}?)?"
        # Without a leading currency, a minus glued to a word or number is a hyphen
        # or a range ("5-10 EUR", "x-5 EUR"), not a sign.
        rf"(?P<pre>{_CURRENCY})?{_SPACE}?(?:(?(pre)|(?<![\w-])){_MINUS}{_SPACE}?)?"
        rf"(?<![\d.,])(?P<num>{_NUMBER}){mag}"
        rf"(?:{_SPACE}?(?P<post>{_CURRENCY}))?"
        # A trailing minus followed by another amount is a range ("$5-$10").
        rf"(?:{_MINUS}(?![\d\w]|{_SPACE}?(?:\d|{_CURRENCY})))?(?P<close>\))?"
        # Never stop in the middle of a word or a number ("$1.2k", "$1.25.3").
        r"(?![^\W_]|[.,]\d)"
    )


_PATTERNS = {flag: _pattern(flag) for flag in (False, True)}


@dataclass(frozen=True, slots=True)
class MoneyMatch:
    """One amount found in text.

    Attributes:
        money: The parsed value.
        start: Index of the first character of the match in the searched text.
        end: Index one past the last character, so ``text[start:end]`` is the match.
        text: The matched substring.
    """

    money: Money
    start: int
    end: int
    text: str


def find_money(
    text: str,
    *,
    currency: str | None = None,
    locale: str | None = None,
    decimal: str | None = None,
    group: str | None = None,
    magnitude: bool = False,
    strict_minor: bool = False,
    require_currency: bool = True,
    errors: Literal["raise", "skip"] = "raise",
) -> list[MoneyMatch]:
    """Find every money amount in ``text``, in order, with its span.

    >>> [(m.text, str(m.money)) for m in find_money("Paid €12,50 and 3 USD.")]
    [('€12,50', '12.50 EUR'), ('3 USD', '3 USD')]

    Only amounts next to a currency symbol or an upper-case ISO code count, unless
    ``require_currency=False``. Every candidate is read with :func:`parse` and the
    same options, so ``locale`` matters for ``$`` and for ``1,234``. With
    ``errors="raise"`` (the default) a candidate that looks like money but cannot be
    read, such as an ambiguous ``$1,234`` with no locale, raises its error; with
    ``errors="skip"`` it is left out.
    """
    if errors not in ("raise", "skip"):
        raise ValueError("errors must be 'raise' or 'skip'")
    found: list[MoneyMatch] = []
    for match in _PATTERNS[magnitude].finditer(text):
        start, end = match.span()
        if bool(match.group("open")) != bool(match.group("close")):
            start += 1 if match.group("open") else 0
            end -= 1 if match.group("close") else 0
        has_currency = bool(match.group("pre") or match.group("post"))
        if require_currency and not has_currency:
            continue
        if not match.group("pre") and text[match.start("num") - 1 : match.start("num")].isalpha():
            continue  # digits glued to a word, such as "A4" or "MP3"
        snippet = text[start:end]
        try:
            money = parse(
                snippet,
                currency=currency,
                locale=locale,
                decimal=decimal,
                group=group,
                magnitude=magnitude,
                strict_minor=strict_minor,
            )
        except MoneyError:
            if errors == "raise":
                raise
            continue
        lead = len(snippet) - len(snippet.lstrip())
        trail = len(snippet) - len(snippet.rstrip())
        found.append(MoneyMatch(money, start + lead, end - trail, snippet.strip()))
    return found

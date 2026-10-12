"""Peel signs, parentheses, currency markers and magnitude words off a money string."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ._currencies import is_currency_code
from ._errors import MoneyParseError
from ._symbols import SYMBOLS

MINUS_SIGNS = "-\u2212"
# Bidirectional marks that CLDR puts in RTL patterns; they carry no meaning here.
_BIDI = dict.fromkeys(map(ord, "\u200e\u200f\u061c"))
_SPACES = dict.fromkeys(map(ord, "\xa0\u202f\u2009"), " ")
_CODE = re.compile(r"[A-Za-z]{3}")

MAGNITUDES: dict[str, int] = {
    "k": 3, "K": 3, "thousand": 3,
    "m": 6, "M": 6, "mm": 6, "MM": 6, "mn": 6, "million": 6,
    "b": 9, "B": 9, "bn": 9, "billion": 9,
    "t": 12, "T": 12, "tn": 12, "trillion": 12,
}  # fmt: skip
_MAGNITUDE = re.compile(
    r"(?<=[0-9.,\s])(" + "|".join(sorted(MAGNITUDES, key=len, reverse=True)) + r")$"
)


@dataclass
class Peeled:
    """What surrounded the number: sign, currency markers and magnitude exponent."""

    number: str
    negative: bool = False
    codes: tuple[str, ...] = ()
    symbols: tuple[str, ...] = ()
    exponent: int = 0


def clean(text: str) -> str:
    """Drop bidi marks and fold no-break and thin spaces into plain spaces."""
    return text.translate(_BIDI).translate(_SPACES).strip()


def peel(text: str, *, magnitude: bool) -> Peeled:
    """Split ``text`` into its number and the markers around it."""
    out = Peeled(text.strip())
    signs = 0
    for _ in range(2):
        signs += _peel_sign(out)
        _peel_currency(out)
    if magnitude:
        _peel_magnitude(out)
        _peel_currency(out)
    signs += _peel_sign(out)
    if signs > 1:
        raise MoneyParseError(f"more than one sign in {text!r}")
    if len(out.codes) + len(out.symbols) > 2:
        raise MoneyParseError(f"too many currency markers in {text!r}")
    return out


def _peel_sign(out: Peeled) -> int:
    text, found = out.number, 0
    if len(text) > 1 and text[0] == "(" and text[-1] == ")":
        text, found = text[1:-1].strip(), found + 1
    if text[:1] in MINUS_SIGNS and text:
        text, found = text[1:].strip(), found + 1
    elif text[:1] == "+":
        text = text[1:].strip()
    if text[-1:] in MINUS_SIGNS and text:
        text, found = text[:-1].strip(), found + 1
    out.number = text
    out.negative = out.negative or found > 0
    return found


def _peel_currency(out: Peeled) -> None:
    text = out.number
    head = _CODE.match(text)
    if head and is_currency_code(head.group().upper()) and not text[3:4].isalpha():
        out.codes += (head.group().upper(),)
        text = text[3:].strip()
    elif symbol := _leading_symbol(text):
        out.symbols += (symbol,)
        text = text[len(symbol) :].strip()
    tail = text[-3:]
    if _CODE.fullmatch(tail) and is_currency_code(tail.upper()) and not text[-4:-3].isalpha():
        out.codes += (tail.upper(),)
        text = text[:-3].strip()
    elif symbol := _trailing_symbol(text):
        out.symbols += (symbol,)
        text = text[: -len(symbol)].strip()
    out.number = text


def _leading_symbol(text: str) -> str | None:
    for symbol in SYMBOLS:
        if text.startswith(symbol) and not (
            symbol[-1].isalpha() and text[len(symbol) : len(symbol) + 1].isalpha()
        ):
            return symbol
    return None


def _trailing_symbol(text: str) -> str | None:
    for symbol in SYMBOLS:
        if len(text) > len(symbol) and text.endswith(symbol):
            before = text[-len(symbol) - 1]
            if not (symbol[0].isalpha() and before.isalpha()):
                return symbol
    return None


def _peel_magnitude(out: Peeled) -> None:
    found = _MAGNITUDE.search(out.number)
    if found:
        out.exponent = MAGNITUDES[found.group(1)]
        out.number = out.number[: found.start()].strip()

"""Turn the numeric part of a money string into an exact Decimal."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from ._errors import MoneyParseError

_THOUSANDS_FILLERS = (" ", chr(0x00A0), chr(0x202F), "'", "_")
_NUMERIC = re.compile(r"[0-9.,]+")


def parse_amount(raw: str, decimal_comma: bool | None) -> Decimal:
    """Parse ``raw`` digits with separators into a Decimal, sign excluded."""
    text = raw.strip()
    for filler in _THOUSANDS_FILLERS:
        text = text.replace(filler, "")
    if not text or not _NUMERIC.fullmatch(text):
        raise MoneyParseError(f"not a numeric money value: {raw!r}")
    return _build(text, _decimal_separator(text, decimal_comma), raw)


def _decimal_separator(text: str, decimal_comma: bool | None) -> str | None:
    if decimal_comma is True:
        return "," if "," in text else None
    if decimal_comma is False:
        return "." if "." in text else None
    return _detect(text)


def _detect(text: str) -> str | None:
    has_comma, has_dot = "," in text, "." in text
    if has_comma and has_dot:
        return "," if text.rfind(",") > text.rfind(".") else "."
    if not has_comma and not has_dot:
        return None
    sep = "," if has_comma else "."
    if text.count(sep) > 1:
        return None
    before, _, after = text.partition(sep)
    if len(after) != 3:
        return sep
    if 1 <= len(before) <= 3:
        raise MoneyParseError(
            f"ambiguous separator in {text!r}: pass decimal_comma to disambiguate"
        )
    return sep


def _build(text: str, decimal_sep: str | None, raw: str) -> Decimal:
    if decimal_sep is None:
        integer_part, fraction, thousands = text, "", _lone_separator(text)
    else:
        thousands = "." if decimal_sep == "," else ","
        integer_part, _, fraction = text.partition(decimal_sep)
    if thousands is not None:
        integer_part = _ungroup(integer_part, thousands, raw)
    canonical = f"{integer_part}.{fraction}" if fraction else integer_part
    try:
        return Decimal(canonical)
    except InvalidOperation:
        raise MoneyParseError(f"not a numeric money value: {raw!r}") from None


def _lone_separator(text: str) -> str | None:
    if "," in text:
        return ","
    if "." in text:
        return "."
    return None


def _ungroup(integer_part: str, thousands: str, raw: str) -> str:
    groups = integer_part.split(thousands)
    if len(groups) > 1:
        head, *rest = groups
        if not 1 <= len(head) <= 3 or any(len(group) != 3 for group in rest):
            raise MoneyParseError(f"invalid digit grouping in {raw!r}")
    return "".join(groups)

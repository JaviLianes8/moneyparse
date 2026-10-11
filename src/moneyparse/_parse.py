"""Parse a human money string into an exact Decimal and optional currency."""

from __future__ import annotations

from decimal import Decimal

from ._amount import parse_amount
from ._currency import extract_currency
from ._errors import MoneyParseError


def parse_money(s: str, *, decimal_comma: bool | None = None) -> tuple[Decimal, str | None]:
    """Parse ``s`` into an exact amount and ISO currency code (or None).

    Set ``decimal_comma`` to True (comma is the decimal mark, dot groups thousands)
    or False (dot is the decimal mark, comma groups thousands) to resolve inputs the
    separator convention leaves ambiguous. When left unset the convention is detected,
    and a genuinely ambiguous string raises :class:`MoneyParseError`.
    """
    text = s.strip()
    if not text:
        raise MoneyParseError("empty money string")
    negative, text = _strip_parentheses(text)
    currency, text = extract_currency(text)
    sign, text = _strip_sign(text.strip())
    amount = parse_amount(text, decimal_comma)
    if negative or sign:
        amount = -amount
    return amount, currency


def _strip_parentheses(text: str) -> tuple[bool, str]:
    if text.startswith("(") and text.endswith(")"):
        return True, text[1:-1].strip()
    return False, text


def _strip_sign(text: str) -> tuple[bool, str]:
    negative = False
    if text.endswith("-"):
        negative, text = True, text[:-1].strip()
    if text.startswith("-"):
        negative, text = True, text[1:].strip()
    elif text.startswith("+"):
        text = text[1:].strip()
    return negative, text

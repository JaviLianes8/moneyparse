"""Numeric part of a money string, as the first release's ``parse_money`` reads it."""

from __future__ import annotations

from decimal import Decimal

from ._number import parse_number


def parse_amount(raw: str, decimal_comma: bool | None) -> Decimal:
    """Parse ``raw`` digits with separators into a Decimal, sign excluded.

    ``decimal_comma`` True means ``,`` is the decimal mark, False means ``.``, and
    None detects the convention. Spaces and apostrophes are dropped without checking
    their grouping, exactly as in the first release.
    """
    if decimal_comma is None:
        return parse_number(raw, strict_fillers=False)
    decimal, group = (",", ".") if decimal_comma else (".", ",")
    return parse_number(raw, decimal=decimal, group=group, strict_fillers=False)

"""Parse human money strings into exact Decimal amounts with optional currency."""

from __future__ import annotations

from ._errors import MoneyParseError
from ._parse import parse_money

__version__ = "0.1.0"

__all__ = ["MoneyParseError", "parse_money"]

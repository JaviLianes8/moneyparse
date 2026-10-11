"""Error raised when a money string cannot be parsed."""

from __future__ import annotations


class MoneyParseError(ValueError):
    """Raised when a string is not a valid money value or is ambiguous."""

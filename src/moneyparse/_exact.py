"""Exact Decimal arithmetic, independent of the caller's decimal context.

The default context keeps 28 significant digits and would silently round longer
amounts on ``+``, ``-``, ``*`` or ``scaleb``, and fail on ``quantize``. Every
calculation here runs in a private context wide enough to be exact, and anything
that would still lose a digit raises :class:`MoneyError` instead.
"""

from __future__ import annotations

from collections.abc import Callable
from decimal import (
    ROUND_HALF_EVEN,
    Context,
    Decimal,
    DecimalException,
    Inexact,
    InvalidOperation,
    Overflow,
    Rounded,
    localcontext,
)

from ._errors import MoneyError

MAX_DIGITS = 10_000
_EXACT = Context(prec=MAX_DIGITS, traps=[InvalidOperation, Inexact, Rounded, Overflow])


def exact(operation: Callable[[], Decimal]) -> Decimal:
    """Run ``operation`` with no rounding; raise MoneyError if it would round."""
    try:
        with localcontext(_EXACT):
            return operation()
    except DecimalException:
        raise MoneyError(f"amount does not fit in {MAX_DIGITS} exact digits") from None


def quantize(amount: Decimal, places: int, rounding: str = ROUND_HALF_EVEN) -> Decimal:
    """Round ``amount`` to ``places`` fraction digits, whatever its size."""
    digits = max(amount.adjusted(), 0) + max(places, 0) + 2
    if digits > MAX_DIGITS:
        raise MoneyError(f"amount does not fit in {MAX_DIGITS} exact digits")
    with localcontext(Context(prec=digits, traps=[InvalidOperation])):
        return amount.quantize(Decimal(1).scaleb(-places), rounding=rounding)


def fits(amount: Decimal, places: int) -> bool:
    """True when ``amount`` has no non-zero digit beyond ``places`` fraction digits."""
    return quantize(amount, places) == amount

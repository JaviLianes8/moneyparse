"""Turn digits and separators into an exact Decimal, sign and currency excluded.

The engine works in two modes. With an explicit decimal separator (from a locale,
from ``decimal=`` or from the legacy ``decimal_comma`` flag) it only checks that the
digit grouping is well formed. Without one it detects the convention and refuses to
guess when ``1,234`` or ``1.234`` could mean either thing.
"""

from __future__ import annotations

import unicodedata
from decimal import Decimal, InvalidOperation

from ._errors import AmbiguousSeparatorError, MoneyParseError

# Characters that only ever group digits, in every CLDR locale: spaces (plain,
# no-break U+00A0, narrow no-break U+202F, thin U+2009), apostrophes and underscore.
FILLERS = frozenset(" \xa0\u202f\u2009'\u2019_")
_ARABIC_DECIMAL, _ARABIC_GROUP = "\u066b", "\u066c"


def ascii_digits(text: str) -> str:
    """Map every Unicode decimal digit (Arabic-Indic, Devanagari, fullwidth) to 0-9."""
    if text.isascii():
        return text
    out = []
    for char in text:
        value = unicodedata.decimal(char, None)
        out.append(str(value) if value is not None else char)
    return "".join(out)


def parse_number(
    raw: str,
    *,
    decimal: str | None = None,
    group: str | None = None,
    indian: bool = False,
    strict_fillers: bool = True,
) -> Decimal:
    """Parse ``raw`` into a non-negative Decimal.

    ``decimal`` is the decimal separator (``None`` detects it). ``group`` is the
    grouping separator; when omitted it is ``.`` for a ``,`` decimal and ``,`` for a
    ``.`` decimal. Spaces and apostrophes always group. ``indian`` also accepts the
    lakh pattern ``1,23,45,678``. ``strict_fillers=False`` drops spaces without
    checking their grouping, as the first release did.
    """
    text = ascii_digits(raw.strip())
    if decimal is None and (_ARABIC_DECIMAL in text or _ARABIC_GROUP in text):
        decimal, group = _ARABIC_DECIMAL, _ARABIC_GROUP  # their roles are unambiguous
    if decimal is not None and group is None:
        group = {",": ".", ".": ","}.get(decimal)
    if decimal is not None:
        text = text.replace(_ARABIC_DECIMAL, decimal).replace(_ARABIC_GROUP, group or "")
    if not strict_fillers:
        text = "".join(char for char in text if char not in FILLERS)
    if decimal is None:
        decimal, group = _detect(text, raw)
    return _build(text, decimal, group, indian, raw)


def _detect(text: str, raw: str) -> tuple[str | None, str | None]:
    commas, dots = text.count(","), text.count(".")
    if commas and dots:
        decimal = "," if text.rfind(",") > text.rfind(".") else "."
        return decimal, "." if decimal == "," else ","
    if not commas and not dots:
        return None, None
    sep = "," if commas else "."
    other = "." if sep == "," else ","
    if commas + dots > 1:
        return other, sep
    before, _, after = text.partition(sep)
    head = "".join(char for char in before if char not in FILLERS)
    filler_grouped = len(head) != len(before)
    if filler_grouped or len(after) != 3 or not head or head[0] == "0" or len(head) > 3:
        return sep, other
    raise AmbiguousSeparatorError(
        f"ambiguous separator in {raw.strip()!r}: {head}{sep}{after} may group thousands "
        "or mark decimals; pass locale=, decimal= or decimal_comma=",
        separator=sep,
    )


def _build(text: str, decimal: str | None, group: str | None, indian: bool, raw: str) -> Decimal:
    if decimal is not None and text.count(decimal) > 1:
        raise MoneyParseError(f"more than one decimal separator in {raw!r}")
    integer, _, fraction = text.partition(decimal) if decimal else (text, "", "")
    if fraction and not fraction.isdigit():
        raise MoneyParseError(
            f"not a numeric money value: {raw!r} (digits must follow the decimal "
            f"separator {decimal!r}; check locale= or decimal=)"
        )
    digits = _ungroup(integer, group, indian, raw)
    if not digits and not fraction:
        raise MoneyParseError(f"not a numeric money value: {raw!r}")
    try:
        return Decimal(f"{digits or '0'}.{fraction}" if fraction else digits)
    except InvalidOperation:
        raise MoneyParseError(f"not a numeric money value: {raw!r}") from None


def _ungroup(integer: str, group: str | None, indian: bool, raw: str) -> str:
    separators = {char for char in integer if not char.isdigit()}
    if not separators:
        return integer
    allowed = FILLERS | ({group} if group else set())
    stray = separators - allowed
    if stray and all(char in ".," for char in stray):
        raise MoneyParseError(
            f"unexpected {''.join(sorted(stray))!r} in {raw!r}: the grouping separator "
            f"here is {group!r}; check locale= or decimal="
        )
    if len(separators) > 1 or stray:
        raise MoneyParseError(f"not a numeric money value: {raw!r}")
    groups = integer.split(separators.pop())
    if not _well_grouped(groups) and not (indian and _lakh_grouped(groups)):
        raise MoneyParseError(f"invalid digit grouping in {raw!r}")
    return "".join(groups)


def _well_grouped(groups: list[str]) -> bool:
    head, *rest = groups
    return 1 <= len(head) <= 3 and all(len(part) == 3 for part in rest)


def _lakh_grouped(groups: list[str]) -> bool:
    *front, last = groups
    head, *middle = front
    return len(last) == 3 and 1 <= len(head) <= 2 and all(len(part) == 2 for part in middle)

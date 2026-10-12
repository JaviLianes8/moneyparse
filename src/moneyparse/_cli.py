"""Command-line interface: ``moneyparse parse | find | format | currency``."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation
from typing import Any, NoReturn

from . import __version__
from ._currencies import currencies, get_currency
from ._engine import parse
from ._errors import MoneyError
from ._find import find_money
from ._format import format_money
from ._money import Money

_EXAMPLES = """\
examples:
  moneyparse parse "1.234,56 EUR"
  moneyparse parse '$1,234.56' --locale en-US
  moneyparse parse "1,234" --decimal ,
  moneyparse parse '$1.2k' --currency USD --magnitude --json
  echo "Paid 12,50 EUR and USD 3.99" | moneyparse find
  moneyparse format 1234.5 --currency EUR --locale de-DE
  moneyparse format -1234 --currency USD --accounting
  moneyparse currency KWD JPY CLF

Errors go to stderr and the exit code is 1.
"""


class _Parser(argparse.ArgumentParser):
    """Argument parser whose usage errors exit with 1, like every other error."""

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(1, f"{self.prog}: error: {message}\n")


def _add_reading_options(sub: argparse.ArgumentParser) -> None:
    sub.add_argument("--locale", help="CLDR locale tag, e.g. de-DE, fr-FR, en-IN")
    sub.add_argument("--currency", help="ISO 4217 code: resolves '$', '¥', 'kr', fills a gap")
    sub.add_argument("--decimal", help="explicit decimal separator, e.g. ',' or '.'")
    sub.add_argument("--group", help="explicit grouping separator")
    sub.add_argument("--magnitude", action="store_true", help="accept 1.2k, 3m, 4bn")
    sub.add_argument(
        "--strict-minor", action="store_true", help="reject more decimals than ISO 4217 allows"
    )
    sub.add_argument("--json", action="store_true", help="print JSON instead of text")


def _build_parser() -> argparse.ArgumentParser:
    parser = _Parser(
        prog="moneyparse",
        description="Parse, find and format money amounts with exact decimals.",
        epilog=_EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"moneyparse {__version__}")
    commands = parser.add_subparsers(
        dest="command", required=True, metavar="COMMAND", parser_class=_Parser
    )
    p_parse = commands.add_parser("parse", help="parse one money string")
    p_parse.add_argument("text", help="the money string")
    p_parse.add_argument(
        "--require-currency", action="store_true", help="fail when no currency is found"
    )
    _add_reading_options(p_parse)
    p_find = commands.add_parser("find", help="find amounts in text read from stdin")
    p_find.add_argument("--any", action="store_true", help="also report numbers without currency")
    p_find.add_argument("--skip-errors", action="store_true", help="skip unreadable candidates")
    _add_reading_options(p_find)
    p_format = commands.add_parser("format", help="format an amount for a locale")
    p_format.add_argument("amount", help="decimal amount, e.g. 1234.5 or -12")
    p_format.add_argument("--currency", help="ISO 4217 code")
    p_format.add_argument("--locale", default="en-US", help="CLDR locale tag (default en-US)")
    p_format.add_argument("--style", choices=("symbol", "code", "plain"), default="symbol")
    p_format.add_argument("--accounting", action="store_true", help="parentheses for negatives")
    p_format.add_argument("--digits", type=int, help="fraction digits (default: minor units)")
    p_currency = commands.add_parser("currency", help="show ISO 4217 data")
    p_currency.add_argument("codes", nargs="*", help="alphabetic or numeric codes (none: all)")
    return parser


def _reading(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "currency": args.currency,
        "locale": args.locale,
        "decimal": args.decimal,
        "group": args.group,
        "magnitude": args.magnitude,
        "strict_minor": args.strict_minor,
    }


def _money_dict(money: Money) -> dict[str, Any]:
    return {"amount": str(money.amount), "currency": money.currency}


def _cmd_parse(args: argparse.Namespace) -> str:
    money = parse(args.text, require_currency=args.require_currency, **_reading(args))
    return json.dumps(_money_dict(money), ensure_ascii=False) if args.json else str(money)


def _cmd_find(args: argparse.Namespace) -> str:
    matches = find_money(
        sys.stdin.read(),
        require_currency=not args.any,
        errors="skip" if args.skip_errors else "raise",
        **_reading(args),
    )
    if args.json:
        rows = [
            {**_money_dict(m.money), "start": m.start, "end": m.end, "text": m.text}
            for m in matches
        ]
        return json.dumps(rows, ensure_ascii=False)
    lines = [
        f"{m.start}\t{m.end}\t{m.money.amount}\t{m.money.currency or ''}\t{m.text}" for m in matches
    ]
    return "\n".join(lines)


def _cmd_format(args: argparse.Namespace) -> str:
    try:
        amount = Decimal(args.amount)
    except InvalidOperation:
        raise MoneyError(f"not a decimal amount: {args.amount!r}") from None
    return format_money(
        amount,
        args.currency,
        locale=args.locale,
        style=args.style,
        accounting=args.accounting,
        digits=args.digits,
    )


def _cmd_currency(args: argparse.Namespace) -> str:
    chosen = [get_currency(code) for code in args.codes] if args.codes else list(currencies())
    rows = []
    for item in chosen:
        units = "N.A." if item.minor_units is None else str(item.minor_units)
        rows.append(f"{item.code}\t{item.numeric}\t{units}\t{item.name}")
    return "\n".join(rows)


_COMMANDS = {"parse": _cmd_parse, "find": _cmd_find, "format": _cmd_format}


def _utf8_streams() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the exit code (0 success, 1 error)."""
    _utf8_streams()
    args = _build_parser().parse_args(argv)
    handler = _COMMANDS.get(args.command, _cmd_currency)
    try:
        output = handler(args)
    except (ValueError, TypeError) as error:
        print(f"moneyparse: error: {error}", file=sys.stderr)
        return 1
    if output:
        print(output)
    return 0

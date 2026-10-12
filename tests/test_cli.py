"""The command line, driven in-process through main()."""

from __future__ import annotations

import io
import json

import pytest

from moneyparse import __version__
from moneyparse._cli import main


def _run(capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, str, str]:
    code = main(list(args))
    out, err = capsys.readouterr()
    return code, out, err


def test_parse(capsys: pytest.CaptureFixture[str]) -> None:
    assert _run(capsys, "parse", "1.234,56 EUR") == (0, "1234.56 EUR\n", "")
    assert _run(capsys, "parse", "$1,234.56", "--locale", "en-US")[1] == "1234.56 USD\n"
    assert _run(capsys, "parse", "1,234", "--decimal", ",")[1] == "1.234\n"


def test_parse_json_and_magnitude(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "parse", "$1.2k", "--currency", "USD", "--magnitude", "--json")
    assert code == 0
    assert json.loads(out) == {"amount": "1200", "currency": "USD"}


def test_parse_errors_go_to_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = _run(capsys, "parse", "1,234")
    assert (code, out) == (1, "")
    assert "ambiguous" in err
    assert _run(capsys, "parse", "5", "--require-currency")[0] == 1
    assert _run(capsys, "parse", "¥1.5", "--currency", "JPY", "--strict-minor")[0] == 1


def test_find(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("Paid 12,50 EUR and USD 3.99 today"))
    code, out, _ = _run(capsys, "find")
    assert code == 0
    assert out.splitlines() == ["5\t14\t12.50\tEUR\t12,50 EUR", "19\t27\t3.99\tUSD\tUSD 3.99"]


def test_find_json_any_and_skip(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("3 items, $1,234 total"))
    code, out, _ = _run(capsys, "find", "--any", "--skip-errors", "--json")
    assert code == 0
    assert json.loads(out) == [{"amount": "3", "currency": None, "start": 0, "end": 1, "text": "3"}]
    monkeypatch.setattr("sys.stdin", io.StringIO("total $1,234"))
    assert _run(capsys, "find")[0] == 1


def test_format(capsys: pytest.CaptureFixture[str]) -> None:
    out = _run(capsys, "format", "1234.5", "--currency", "EUR", "--locale", "de-DE")[1]
    assert out == "1.234,50\xa0€\n"
    assert _run(capsys, "format", "-1234", "--currency", "USD", "--accounting")[1] == (
        "($1,234.00)\n"
    )
    assert _run(capsys, "format", "5", "--currency", "GBP", "--style", "code")[1] == (
        "GBP\xa05.00\n"
    )
    assert _run(capsys, "format", "1.5", "--digits", "3")[1] == "1.500\n"
    assert _run(capsys, "format", "abc")[0] == 1
    assert _run(capsys, "format", "1", "--currency", "ZZZ")[0] == 1


def test_currency(capsys: pytest.CaptureFixture[str]) -> None:
    out = _run(capsys, "currency", "KWD", "392", "XAU")[1]
    assert out.splitlines() == [
        "KWD\t414\t3\tKuwaiti Dinar",
        "JPY\t392\t0\tYen",
        "XAU\t959\tN.A.\tGold",
    ]
    assert len(_run(capsys, "currency")[1].splitlines()) == 178


def test_usage_errors_exit_one(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as caught:
        main([])
    assert caught.value.code == 1
    with pytest.raises(SystemExit) as caught:
        main(["format", "1", "--style", "fancy"])
    assert caught.value.code == 1


def test_help_and_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as caught:
        main(["--help"])
    assert caught.value.code == 0
    out = capsys.readouterr().out
    assert "examples:" in out and "moneyparse find" in out
    with pytest.raises(SystemExit):
        main(["--version"])
    assert capsys.readouterr().out.strip() == f"moneyparse {__version__}"

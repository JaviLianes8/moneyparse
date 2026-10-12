"""Real end-to-end test: build a wheel, install it into a throwaway virtual
environment and drive the installed ``moneyparse`` script through subprocess.

No mocks and no import of the in-tree package: this proves the wheel contains the
package and its data, that ``[project.scripts]`` is wired, and that the real
executable prints the documented output and exit codes.
"""

from __future__ import annotations

import json
import os
import subprocess
import venv
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BIN = "Scripts" if os.name == "nt" else "bin"
EXE = ".exe" if os.name == "nt" else ""


@pytest.fixture(scope="module")
def script(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build the wheel, install it into a fresh venv and return the console script."""
    work = tmp_path_factory.mktemp("moneyparse_e2e")
    venv.create(work / "env", with_pip=True)
    python = work / "env" / BIN / f"python{EXE}"
    wheels = work / "wheels"
    build = subprocess.run(
        [str(python), "-m", "pip", "wheel", str(ROOT), "--no-deps", "-w", str(wheels), "-q"],
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert build.returncode == 0, build.stderr
    [wheel] = wheels.glob("moneyparse-*.whl")
    install = subprocess.run(
        [str(python), "-m", "pip", "install", str(wheel), "--no-deps", "-q"],
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert install.returncode == 0, install.stderr
    path = work / "env" / BIN / f"moneyparse{EXE}"
    assert path.is_file(), f"console script not installed at {path}"
    return path


def _run(script: Path, *args: str, stdin: str = "") -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONUTF8": "1"}
    return subprocess.run(
        [str(script), *args],
        input=stdin,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        env=env,
        cwd=script.parent,
    )


def test_parse_european_amount(script: Path) -> None:
    result = _run(script, "parse", "1.234,56 €")
    assert (result.returncode, result.stdout, result.stderr) == (0, "1234.56 EUR\n", "")


def test_parse_with_locale_and_json(script: Path) -> None:
    result = _run(script, "parse", "($1,234.00)", "--locale", "en-US", "--json")
    assert result.returncode == 0
    assert json.loads(result.stdout) == {"amount": "-1234.00", "currency": "USD"}


def test_find_reads_stdin(script: Path) -> None:
    text = "Paid 1\N{NARROW NO-BREAK SPACE}234,56 EUR, then USD 3.99."
    result = _run(script, "find", stdin=text)
    assert result.returncode == 0
    rows = [line.split("\t") for line in result.stdout.splitlines()]
    assert [(row[2], row[3]) for row in rows] == [("1234.56", "EUR"), ("3.99", "USD")]
    for start, end, *_, snippet in rows:
        assert text[int(start) : int(end)] == snippet


def test_format_for_locales(script: Path) -> None:
    fr = _run(script, "format", "1234.5", "--currency", "EUR", "--locale", "fr-FR")
    assert fr.stdout == "1\N{NARROW NO-BREAK SPACE}234,50\xa0€\n"
    india = _run(script, "format", "12345678.9", "--currency", "INR", "--locale", "en-IN")
    assert india.stdout == "₹1,23,45,678.90\n"


def test_round_trip_through_the_real_script(script: Path) -> None:
    formatted = _run(script, "format", "-98765.4", "--currency", "CHF", "--locale", "de-CH")
    assert formatted.stdout == "CHF-98'765.40\n"
    parsed = _run(script, "parse", formatted.stdout.strip(), "--locale", "de-CH")
    assert parsed.stdout == "-98765.40 CHF\n"


def test_errors_exit_one_on_stderr(script: Path) -> None:
    result = _run(script, "parse", "$5")
    assert result.returncode == 1
    assert result.stdout == ""
    assert "ambiguous" in result.stderr
    assert _run(script, "parse").returncode == 1


def test_help_and_version(script: Path) -> None:
    result = _run(script, "--help")
    assert result.returncode == 0
    assert "examples:" in result.stdout
    version = _run(script, "--version")
    assert version.stdout.strip() == f"moneyparse {_version()}"


def test_module_entry_point(script: Path) -> None:
    python = script.parent / f"python{EXE}"
    result = subprocess.run(
        [str(python), "-m", "moneyparse", "currency", "CLF"],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=script.parent,
    )
    assert result.stdout == "CLF\t990\t4\tUnidad de Fomento\n"


def _version() -> str:
    for line in (ROOT / "src" / "moneyparse" / "__init__.py").read_text().splitlines():
        if line.startswith("__version__"):
            return line.split('"')[1]
    raise AssertionError("version not found")

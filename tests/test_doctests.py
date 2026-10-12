"""Every example in the public docstrings runs and prints what it claims."""

from __future__ import annotations

import doctest
import importlib
from decimal import Decimal

import pytest

import moneyparse

MODULES = [
    "moneyparse._currencies",
    "moneyparse._engine",
    "moneyparse._find",
    "moneyparse._format",
    "moneyparse._money",
]


@pytest.mark.parametrize("name", MODULES)
def test_docstring_examples(name: str) -> None:
    module = importlib.import_module(name)
    globs = {**vars(moneyparse), "Decimal": Decimal}
    result = doctest.testmod(module, extraglobs=globs)
    assert result.attempted > 0
    assert result.failed == 0

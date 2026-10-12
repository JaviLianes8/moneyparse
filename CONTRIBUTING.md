# Contributing

Thanks for taking the time. This project keeps a small, predictable shape.

## Setup

```
pip install -r requirements-dev.txt
```

## Before you open a pull request

- Keep public API in `src/moneyparse/__init__.py`; internals live in `_`-prefixed modules.
- Add a test for the behaviour you change. Unit tests are hermetic. The end-to-end
  test builds a wheel, installs it into a throwaway virtual environment and runs the
  real `moneyparse` script, so pip may download the build backend.
- Currency and locale data are generated from ISO 4217 List One and CLDR; cite the
  source and its date when you refresh them.
- Run `scripts/check.ps1` (format, lint, types, tests) and make sure it passes.
- One logical change per commit, imperative subject line.

Open an issue first if the change is large or shifts the public API.

# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-10-12

### Added

- `parse` returns a frozen `Money` and accepts `locale` (33 embedded CLDR 48.2
  locales), explicit `decimal` / `group` separators, a `currency` hint, `magnitude`
  suffixes (`1.2k`, `3 bn`), `strict_minor` and `require_currency`.
- Ambiguity policy: `1,234` without a convention raises `AmbiguousSeparatorError`;
  `$`, `¥`, `kr`, `Rs` and `C$` without a hint or locale raise
  `AmbiguousCurrencyError` with the candidate codes.
- Every negative form: leading or trailing minus (ASCII or U+2212), accounting
  parentheses, sign on either side of the symbol.
- Unicode digits and the Arabic decimal and thousands separators.
- `find_money` finds amounts in free text with exact spans (`MoneyMatch`).
- `format_money` and `Money.format` write amounts per CLDR: standard and accounting
  patterns, currency separators, minus sign, minimum grouping digits, Indian
  grouping and currency spacing.
- `Money`: exact same-currency arithmetic and ordering, `quantize`, `to_minor`,
  `from_minor`, `allocate`.
- Embedded ISO 4217 List One (SIX, published 2026-09-17): `Currency`,
  `get_currency`, `currencies`, `ISO4217_PUBLISHED`; CLDR data via `Locale`,
  `get_locale`, `locales`.
- Typed errors under `MoneyError`: `AmbiguousSeparatorError`,
  `AmbiguousCurrencyError`, `CurrencyConflictError`, `MinorUnitError`,
  `UnknownCurrencyError`, `UnknownLocaleError`, `CurrencyMismatchError`.
- `moneyparse` command line (`parse`, `find`, `format`, `currency`) and
  `python -m moneyparse`.
- GUIDE.md.

### Changed

- `parse_money` keeps its results and errors. Its ambiguity error is now the more
  specific `AmbiguousSeparatorError` (still a `MoneyParseError`). Inputs it used to
  reject because they are unambiguous after all now parse: `0,123` (a thousands
  group never follows a lone zero), Unicode digits, the Arabic decimal and thousands
  separators, and thin spaces or typographic apostrophes as digit grouping.
- Negating amounts longer than 28 digits no longer rounds them.

## [0.1.0]

- First release.
- `parse_money` turns a money string into an exact `Decimal` and an optional ISO currency
  code, detecting the separator convention and resolving ambiguity with `decimal_comma`.
- `MoneyParseError` for invalid, unknown or ambiguous input.

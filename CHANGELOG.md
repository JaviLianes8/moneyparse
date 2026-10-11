# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0]

- First release.
- `parse_money` turns a money string into an exact `Decimal` and an optional ISO currency
  code, detecting the separator convention and resolving ambiguity with `decimal_comma`.
- `MoneyParseError` for invalid, unknown or ambiguous input.

# Improvements round

Ranked, substantial improvements for `moneyparse`, measured against the `0.1.0`
surface: `parse_money(s, *, decimal_comma=None) -> (Decimal, str | None)` and
`MoneyParseError`, with a 32-code currency list, ten symbols (`$` always read as
USD) and auto-detected separators. Every item is additive: `parse_money` keeps its
results, so code written against `0.1.0` keeps working.

Ground truth: ISO 4217 List One (SIX, published 2026-09-17) for codes, numeric
codes and minor units; Unicode CLDR 48.2 (`cldr-json`, `cldr-numbers-full`) for
separators, minus signs, grouping, currency patterns and symbols.

## Shipped in this round (0.2.0)

1. **Locale-aware parsing with honest ambiguity.** `parse(..., locale="de-DE")`
   uses the CLDR decimal and group separators (and `currencyDecimal` /
   `currencyGroup`), the lakh grouping of en-IN and hi-IN, and refuses the other
   convention. Explicit `decimal=` / `group=` override it. Without either, `1,234`
   raises `AmbiguousSeparatorError` instead of guessing; everything that can be
   decided (`1.234,56`, `12,50`, `0,125`, `1 234,567`) is decided.

2. **A currency policy that never assumes `$` is USD.** All 178 ISO 4217 codes,
   every CLDR symbol of the embedded locales, and an explicit ambiguous set (`$`,
   `¥`, `kr`, `Rs`, `C$`) resolved by a `currency=` hint, the locale's own symbols
   (`$` is CAD in en-CA, USD in de-DE) or its home currency. Conflicts between the
   text and the hint raise `CurrencyConflictError`.

3. **ISO 4217 as data.** `Currency`, `get_currency` (alphabetic or numeric),
   `currencies`, `ISO4217_PUBLISHED`. Minor units drive `strict_minor` validation
   (`¥1.5` is invalid), `Money.quantize`, `to_minor` / `from_minor` and the
   default fraction digits when formatting (KWD 3, JPY 0, CLF 4).

4. **Every negative form.** Leading or trailing minus (ASCII or U+2212), accounting
   parentheses, the sign on either side of the symbol (`CHF-1'234.50`,
   `€ -1.234,56`), exactly one per amount.

5. **Formatting back.** `format_money` / `Money.format` follow CLDR 48.2 exactly:
   standard and accounting patterns, currency separators, locale minus sign,
   `minimumGroupingDigits`, Indian grouping, currencySpacing. The symbol choice
   never emits a symbol the reader could not resolve. Every output parses back.

6. **Finding amounts in free text.** `find_money` returns `MoneyMatch` objects with
   exact spans, needs a currency marker by default, never stops inside a word or a
   number, and does not read a hyphen or range (`5-10 EUR`, `$5-$10`) as a negative.

7. **A frozen `Money` type.** Exact `Decimal` amount, ISO code, same-currency
   arithmetic and ordering (`CurrencyMismatchError` otherwise), no floats,
   banker's rounding, and `allocate` that never loses a minor unit.

8. **Typed errors.** `MoneyError` at the root (a `ValueError`), with
   `AmbiguousSeparatorError`, `AmbiguousCurrencyError` (carries the candidates),
   `CurrencyConflictError`, `MinorUnitError`, `UnknownCurrencyError`,
   `UnknownLocaleError` and `CurrencyMismatchError`.

9. **Magnitude suffixes and native digits.** Opt-in `k` / `m` / `bn` / `tn` and
   their words; Arabic-Indic, Devanagari and fullwidth digits plus the Arabic
   decimal and thousands separators.

10. **Command line.** `moneyparse parse | find | format | currency`, JSON output,
    runnable examples in `--help`, errors on stderr with exit code 1.

11. **Docs and tests.** Docstrings with doctested examples on every public callable,
    GUIDE.md, a contract suite over CLDR and ISO fixtures with a round-trip sweep of
    every locale, an optional Babel oracle, and a real end-to-end test that builds
    the wheel, installs it into a throwaway venv and drives the installed script.

## Notes from the Babel oracle

Babel 2.18 output parses back exactly in all 33 locales. Where the formatted text
differs, `moneyparse` follows CLDR 48.2 and Babel does not: Babel ignores
`minimumGroupingDigits` (es-ES `1234,50 €`), the locale minus sign (sv-SE
U+2212) and currencySpacing (`USD 5.00`), and ships data older than CLDR 48.2
(cldr-json 48.2.3) for de-CH, it-CH and fr-CH grouping: 48.2 changed the fr-CH
group from U+202F to the apostrophe.

## Considered and deliberately deferred

- **Currency words** (`5 dollars`, `10 euros`). Plural rules and translations per
  language would need a large table; codes and symbols cover structured text.
- **Assuming `$` is USD by default.** Rejected: it is the symbol of 29 currencies.
  A `locale` or `currency` hint makes the intent explicit at no cost.
- **Arabic and Hebrew formatting.** Parsing ignores bidi marks and reads Arabic
  digits, but formatting RTL patterns needs more than this library should carry.
- **Exchange rates and conversion.** Out of scope for a zero-dependency parser.

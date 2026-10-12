# moneyparse guide

Everything `moneyparse` does, with runnable examples. All amounts are
`decimal.Decimal`; nothing is ever converted to `float`.

## 1. Parsing one string: `parse`

```python
parse(text, *, currency=None, locale=None, decimal=None, group=None,
      magnitude=False, strict_minor=False, require_currency=False) -> Money
```

`parse` peels the currency marker, the sign and an optional magnitude off the text,
reads the digits with the right separators and returns a frozen `Money`.

```python
parse("1.234,56 €")  # Money(Decimal('1234.56'), 'EUR')
parse("USD (42.00)")  # Money(Decimal('-42.00'), 'USD')
parse("99.95-")  # Money(Decimal('-99.95'), None)
parse("12.50", currency="EUR")  # the hint fills a missing currency
```

### Currency markers

- **ISO 4217 codes**, before or after the number, any case: `USD 10`, `10 usd`.
- **Unambiguous symbols**: `€`, `£` (GBP), `₹`, `₩` (KRW), `₽`, `₺`, `₪`, `R$`,
  `CA$`, `US$`, `A$`, `zł`, `Kč`, `Ft`, `Rp`, `CHF`, `$US`, `£GB` and every other
  symbol CLDR 48.2 uses in the embedded locales.
- **Ambiguous symbols**: `$`, `¥`, `￥`, `kr`, `kr.`, `Rs`, `Rs.`, `C$`. They resolve
  through, in order: the `currency=` hint (which must be one of the symbol's
  candidates), the locale's own symbols (`$` is USD in `de-DE`, CAD in `en-CA`), the
  locale's home currency (`Rs` is INR in `en-IN`, `¥` is JPY in `ja-JP`). Otherwise
  `AmbiguousCurrencyError` lists the candidates.
- A symbol and a code together must agree: `$5 USD` is fine, `€5 USD` raises
  `CurrencyConflictError`, and so does a hint that contradicts the text.

### Separators

| You pass | Decimal mark | Grouping |
| --- | --- | --- |
| nothing | detected | detected |
| `locale="de-DE"` | CLDR decimal (and `currencyDecimal`) | CLDR group (and `currencyGroup`) |
| `decimal=","` | `,` | `.` unless `group=` says otherwise |
| `group="."` | the other of `.` and `,` | `.` (any other `group` needs `decimal=`) |

Spaces (plain, no-break U+00A0, narrow no-break U+202F, thin), apostrophes (`'` and
the typographic one) and underscores always group digits. Groups must be well formed:
three digits each, or the Indian lakh pattern `1,23,45,678` in `en-IN` and `hi-IN`.

Detection reads `1.234,56` and `1,234.56` (the last mark is the decimal), repeated
marks as grouping (`1,234,567`), and a single mark as a decimal when the fraction is
not three digits (`12,50`), the head starts with `0` (`0,125`), the head is longer
than three digits (`1234,567`) or the integer part is grouped with spaces
(`1 234,567`). What is left, `1,234` and `1.234`, raises `AmbiguousSeparatorError`
(its `separator` attribute is the mark in question).

With a locale the other convention is refused: `parse("1,234.56", locale="de-DE")`
raises `MoneyParseError` with a hint to check `locale=` or `decimal=`.

Unicode digits (Arabic-Indic, Devanagari, fullwidth) and the Arabic decimal and
thousands separators are understood: `parse("١٬٢٣٤ KWD")` is 1234 KWD.

### Negatives

Every common form, exactly one per amount: `-5 EUR`, `−5 EUR` (U+2212, as CLDR
writes it for sv-SE, fi-FI and nb-NO), `(5) EUR`, `EUR (5)`, `5- EUR`, `EUR 5-`,
`€-5`, `-€5`, `CHF-1'234.50`, `€ -1.234,56`. Two signs (`-(5)`, `--5`) are an error.

### Magnitude suffixes (opt-in)

With `magnitude=True`: `k`, `K`, `thousand`; `m`, `M`, `mm`, `MM`, `mn`, `million`;
`b`, `B`, `bn`, `billion`; `t`, `T`, `tn`, `trillion`.

```python
parse("$1.2k", currency="USD", magnitude=True)  # 1200 USD
parse("€3.5 bn", magnitude=True)  # 3500000000 EUR
```

### Minor units

`strict_minor=True` rejects amounts the currency cannot hold in its ISO 4217 minor
units with `MinorUnitError`: `¥1.5` (JPY has 0), `$0.001` (USD has 2). The check
is on the value, so trailing zeros are fine once the separators are known:
`parse("10.500 USD", decimal=".", strict_minor=True)` is 10.500 USD.

Under `strict_minor`, the currency also settles an ambiguous separator when only one
reading is valid: `parse("$1,234", currency="USD", strict_minor=True)` is 1234 USD
because 1.234 USD would hold a tenth of a cent. `10.500 USD` stays ambiguous (10.50
is a valid amount too), and so does any amount with a magnitude suffix. Without
`strict_minor` nothing is assumed, since prices such as `$3.459` per gallon of fuel
are real: pass `locale=` or `decimal=` for those.

## 2. Finding amounts in text: `find_money`

```python
find_money(text, *, currency=None, locale=None, decimal=None, group=None,
           magnitude=False, strict_minor=False, require_currency=True,
           errors="raise") -> list[MoneyMatch]
```

Each `MoneyMatch` has `money`, `start`, `end` and `text`, with
`text == source[start:end]`. Only amounts next to a symbol or an upper-case ISO code
count (lower-case `all`, `try`, `top` are words), unless `require_currency=False`.
Codes may touch the digits (`EUR5`, `5EUR`). Matches never stop inside a word or a
number (`$1.2k` without `magnitude`, `A4 USD`), and a hyphen or range is not a
negative: `5-10 EUR`, `$5-$10`, `x-5 EUR` and `555-1234` give no minus sign.

```python
text = "Total €1.234,56, fee USD 3.99, refund ($12.00)"
find_money(text, locale="en-US", errors="skip")
# USD 3.99 and ($12.00); €1.234,56 is not valid en-US, so it is skipped
```

`errors="raise"` (the default) raises the first candidate that looks like money but
cannot be read, such as `$1,234` with no locale; `errors="skip"` leaves it out.

## 3. Formatting: `format_money`

```python
format_money(value, currency=None, *, locale="en-US", style="symbol",
             accounting=False, digits=None, rounding=ROUND_HALF_EVEN) -> str
```

The output follows CLDR 48.2 for the locale: standard or accounting pattern, decimal
and grouping separators (including `currencyDecimal` and `currencyGroup`), the minus
sign, `minimumGroupingDigits` (es-ES writes `1234,56 €`), Indian grouping, and the
currencySpacing rule (a no-break space between a letter-edged symbol and a digit).

| Locale | `format_money(Decimal("-1234.5"), code, locale=...)` |
| --- | --- |
| en-US, USD | `-$1,234.50` (accounting: `($1,234.50)`) |
| de-DE, EUR | `-1.234,50 €` |
| fr-FR, EUR | `-1 234,50 €` (narrow no-break space groups) |
| de-CH, CHF | `CHF-1'234.50` |
| sv-SE, SEK | `−1 234,50 kr` |
| ja-JP, JPY | `-￥1,234` (0 minor units, half-even rounding) |

`style="symbol"` uses the locale's own symbol for its home currency, USD and EUR,
then an unambiguous CLDR symbol (`CA$`, `£`, `₹`), then the ISO code: it never emits
`$` or `¥` where the reader could not tell which currency is meant. `style="code"`
writes `USD`; `style="plain"` drops the currency. `digits` defaults to the
currency's minor units (KWD 3, JPY 0, CLF 4). Every output parses back with
`parse(text, locale=locale, currency=code)`.

## 4. The `Money` type

`Money(amount, currency=None)` is a frozen, hashable dataclass. `amount` accepts
`int`, `str` or `Decimal` (never `float`), `currency` an ISO code (upper-cased).

- `+`, `-` and comparisons need the same currency, else `CurrencyMismatchError`.
- `*` takes an `int` or `Decimal`; `-m`, `+m`, `abs(m)`, `bool(m)` work.
- `quantize(rounding=ROUND_HALF_EVEN)` rounds to minor units.
- `to_minor()` / `Money.from_minor(1234, "USD")` convert to and from integer cents.
- `allocate([1, 1, 1])` splits without losing a minor unit.
- `format(locale, ...)` is `format_money(self, ...)`; `str(m)` is `"12.50 EUR"`.

## 5. Errors

```
ValueError
└── MoneyError
    ├── MoneyParseError            (parse, find_money, parse_money)
    │   ├── AmbiguousSeparatorError   .separator
    │   ├── AmbiguousCurrencyError    .symbol, .candidates
    │   ├── CurrencyConflictError
    │   └── MinorUnitError
    ├── UnknownCurrencyError
    ├── UnknownLocaleError
    └── CurrencyMismatchError
```

## 6. Data

- `get_currency("KWD")`, `get_currency(414)`, `get_currency("008")` return a
  `Currency(code, numeric, minor_units, name)`; `currencies()` lists all 178 active
  codes of ISO 4217 List One as published by SIX on 2026-09-17
  (`ISO4217_PUBLISHED`). Funds and metals with "N.A." minor units have `None`.
- `get_locale("de-CH")` returns the embedded CLDR 48.2 data; `locales()` lists the 33
  tags: cs-CZ, da-DK, de-AT, de-CH, de-DE, en-AU, en-CA, en-GB, en-IN, en-US, es-ES,
  es-MX, fi-FI, fr-CA, fr-CH, fr-FR, hi-IN, id-ID, it-CH, it-IT, ja-JP, ko-KR, nb-NO,
  nl-NL, pl-PL, pt-BR, pt-PT, ru-RU, sv-SE, th-TH, tr-TR, uk-UA, zh-CN. A bare
  language picks its main locale (`de` is de-DE, `pt` is pt-BR).

## 7. Command line

```
moneyparse parse TEXT [--locale L] [--currency C] [--decimal D] [--group G]
                      [--magnitude] [--strict-minor] [--require-currency] [--json]
moneyparse find [same reading options] [--any] [--skip-errors] [--json] < file
moneyparse format AMOUNT [--currency C] [--locale L] [--style symbol|code|plain]
                         [--accounting] [--digits N]
moneyparse currency [CODE ...]
```

`find` prints tab-separated `start end amount currency text` lines (or JSON).
Output is UTF-8. Errors go to stderr with exit code 1; `python -m moneyparse` works
too.

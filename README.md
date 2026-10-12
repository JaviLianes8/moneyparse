# moneyparse

Parse, find and format money strings as exact `Decimal` amounts with their ISO 4217
currency. It reads `1.234,56 €`, `$1,234.56`, `CHF-1'234.50`, `(1,234.00)`,
`₹1,23,45,678.90` and `1 234,56 kr`, finds amounts inside free text with their
positions, and writes amounts back the way a locale does. Separator rules, minus
signs and currency patterns come from Unicode CLDR 48.2; codes, numeric codes and minor
units come from the ISO 4217 list published on 2026-09-17. No dependencies, no floats.

## Install

```
pip install moneyparse
```

## Quick start

```python
from decimal import Decimal
from moneyparse import Money, find_money, format_money, parse

parse("1.234,56 €")  # Money(amount=Decimal('1234.56'), currency='EUR')
parse("$1,234.56", locale="en-US")  # Money(amount=Decimal('1234.56'), currency='USD')
parse("$1,234.56", locale="en-CA")  # ... currency='CAD'
parse("(1,234.00)", currency="USD", locale="en-US")  # Decimal('-1234.00'), 'USD'
parse("₹1,23,45,678.90", locale="en-IN")  # Decimal('12345678.90'), 'INR'
parse("$1.2k", currency="USD", magnitude=True)  # Decimal('1200'), 'USD'

[(m.text, m.start, m.end) for m in find_money("Paid €12,50 and 3 USD.")]
# [('€12,50', 5, 11), ('3 USD', 16, 21)]

format_money(Decimal("1234.5"), "EUR", locale="de-DE")  # '1.234,50\xa0€'
format_money(Decimal("-1234"), "USD", accounting=True)  # '($1,234.00)'

Money("10.50", "EUR") + Money("0.25", "EUR")  # Money(... Decimal('10.75'), 'EUR')
Money("100.00", "EUR").allocate([1, 1, 1])  # 33.34, 33.33, 33.33 EUR
```

## No guessing

Two things in a money string can be genuinely ambiguous, and `moneyparse` raises a
typed error instead of guessing:

- **Separators.** `1,234` is one thousand two hundred thirty-four in `en-US` and one
  point two three four in `de-DE`. Without `locale=` or `decimal=` it raises
  `AmbiguousSeparatorError`. Strings with both marks (`1.234,56`), repeated groups
  (`1,234,567`) or a fraction that is not three digits (`12,50`) are read directly.
- **Symbols.** `$` is the narrow symbol of 29 currencies, `¥` of JPY and CNY, `kr` of
  four. Without `currency=` or a `locale=` that gives the symbol a meaning (`$` is
  CAD in `en-CA`, `kr` is SEK in `sv-SE`), it raises `AmbiguousCurrencyError` with
  the candidate codes. Unambiguous symbols (`€`, `£`, `₹`, `R$`, `zł`, `CA$`) and ISO
  codes need nothing.

## Command line

```
moneyparse parse "1.234,56 EUR"                 # 1234.56 EUR
moneyparse parse '$1,234.56' --locale en-US --json
echo "Paid 12,50 EUR and USD 3.99" | moneyparse find
moneyparse format 1234.5 --currency EUR --locale de-DE
moneyparse currency KWD JPY CLF
```

Errors go to stderr with exit code 1. `moneyparse --help` lists every option.

## Learn more

[GUIDE.md](GUIDE.md) covers every option: locales, explicit separators, negatives,
magnitude suffixes, minor units, finding amounts in text, formatting, the `Money`
type, the error hierarchy and where the data comes from.

`parse_money`, the tuple-returning function of the first release, is unchanged:

```python
from moneyparse import parse_money

parse_money("$1,234.56")  # (Decimal('1234.56'), 'USD')
```

## Why

Amounts arrive as strings from invoices, spreadsheets, scraped pages and user input,
in whatever locale wrote them. `py-moneyed` models money but does not parse locale
strings; `babel` formats and parses numbers but is heavy, does not find amounts in
text and leaves currency symbols to you; `price-parser` targets scraped text and
returns floats, which lose cents. `moneyparse` turns money text into an exact
`Decimal` plus its currency, refuses to guess, and writes it back.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/

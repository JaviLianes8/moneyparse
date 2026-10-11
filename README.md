# moneyparse

Parse a human-written money string into an exact `Decimal` amount and an optional
currency code. It understands both separator conventions (`1,234.56` and `1.234,56`),
currency symbols and ISO codes, parenthesised and trailing-minus negatives, and loose
whitespace. It has no dependencies beyond the standard library.

## Install

```
pip install moneyparse
```

## Usage

```python
from decimal import Decimal
from moneyparse import parse_money, MoneyParseError

parse_money("$1,234.56")      # (Decimal("1234.56"), "USD")
parse_money("1.234,56 EUR")   # (Decimal("1234.56"), "EUR")
parse_money("USD 10")         # (Decimal("10"), "USD")
parse_money("($42.00)")       # (Decimal("-42.00"), "USD")
parse_money("99.95-")         # (Decimal("-99.95"), None)
parse_money("1 234,56")       # (Decimal("1234.56"), None)
```

The convention is detected when the string is unambiguous. A lone separator followed by
exactly three digits (`1,234` or `1.234`) could mean either a thousands group or a
decimal fraction, so it is ambiguous and must be told which:

```python
parse_money("1,234")                       # raises MoneyParseError
parse_money("1,234", decimal_comma=True)    # (Decimal("1.234"), None)
parse_money("1,234", decimal_comma=False)   # (Decimal("1234"), None)
```

Pass `decimal_comma=True` when the comma is the decimal mark (and the dot groups
thousands), or `decimal_comma=False` for the opposite. Invalid numbers, unknown input and
malformed digit grouping raise `MoneyParseError`.

## Why

Amounts arrive as strings from invoices, spreadsheets, scraped pages and user input, in
whatever locale wrote them. `py-moneyed` models money but does not parse these locale
strings; `babel` can, but it is heavy and bound to its locale database; `price-parser`
targets scraped text and returns floats, which lose cents. `moneyparse` does one thing:
turn a money string into an exact `Decimal` plus its currency, with an honest error when
the separators are genuinely ambiguous.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/

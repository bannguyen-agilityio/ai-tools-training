"""Formula-injection guard for exports (R28, spec 8).

A cell that starts with `=`, `+`, `-`, `@`, a tab or a carriage return, even after leading
whitespace that an importer may trim, would be run as a formula by a spreadsheet, so it is
prefixed with a single quote. Only text is touched: numbers
and dates are written as their own types and are never strings that could start with `-`.
"""

from datetime import date
from decimal import Decimal

Cell = str | int | float | Decimal | date | None

DANGEROUS = ("=", "+", "-", "@", "\t", "\r")
TRIMMED = " \n\v\f"


def escape_cell(value: Cell) -> Cell:
    if isinstance(value, str) and value.lstrip(TRIMMED).startswith(DANGEROUS):
        return "'" + value
    return value

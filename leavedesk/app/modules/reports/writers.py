"""CSV and xlsx writers. Every text cell goes through `escape_cell` (R28); the file says it is
confidential in its first row, its sheet banners and (xlsx) its document properties."""

import csv
import io
import re
from collections.abc import Iterable, Sequence
from datetime import date
from decimal import Decimal

from openpyxl import Workbook

from app.modules.reports.escape import Cell, escape_cell
from app.modules.reports.schemas import MonthlyReport

BANNER = (
    "CONFIDENTIAL - HR only. Contains Sick leave types. Do not forward or store in shared folders."
)
SUMMARY_HEAD = ["Employee", "Leave type", "Days taken"]
BALANCE_HEAD = ["Employee", "Annual available", "Annual carried", "Sick available"]
OFF_HEAD = ["Employee", "Leave type", "From", "To", "Days in month"]


def _tables(report: MonthlyReport) -> list[tuple[str, list[str], list[list[Cell]]]]:
    return [
        (
            "Days taken",
            SUMMARY_HEAD,
            [[r.employee, r.leave_type, r.days_taken] for r in report.summary],
        ),
        (
            f"Remaining balances at the end of {report.month}",
            BALANCE_HEAD,
            [
                [r.employee, r.annual_available, r.annual_carried, r.sick_available]
                for r in report.balances
            ],
        ),
        (
            "Who was off and when",
            OFF_HEAD,
            [
                [r.employee, r.leave_type, r.start_date, r.end_date, r.days_in_month]
                for r in report.off
            ],
        ),
    ]


CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _safe(row: Iterable[Cell]) -> list[Cell]:
    return [escape_cell(cell) for cell in row]


def _printable(cell: Cell) -> Cell:
    """xlsx refuses control characters in text (it would be a 500); drop them there only."""
    return CONTROL.sub("", cell) if isinstance(cell, str) else cell


def _text(cell: Cell) -> str:
    if cell is None:
        return ""
    return cell.isoformat() if isinstance(cell, date) else str(cell)


def to_csv(report: MonthlyReport) -> bytes:
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\r\n")
    writer.writerow([BANNER])
    writer.writerow([f"Leave report {report.month}"])
    for title, head, rows in _tables(report):
        writer.writerow([])
        writer.writerow([title])
        writer.writerow(head)
        for row in rows:
            writer.writerow([_text(cell) for cell in _safe(row)])
    return ("﻿" + out.getvalue()).encode("utf-8")  # BOM so Excel reads Vietnamese names


def to_xlsx(report: MonthlyReport) -> bytes:
    book = Workbook()
    if book.active is not None:
        book.remove(book.active)  # the default empty sheet
    book.properties.title = f"CONFIDENTIAL leave report {report.month}"
    book.properties.subject = "CONFIDENTIAL - HR only"
    book.properties.keywords = "confidential"
    for (title, head, rows), name in zip(
        _tables(report), ("Days taken", "Balances", "Who was off"), strict=True
    ):
        sheet = book.create_sheet(name)
        sheet.append([BANNER])
        sheet.append([title])
        sheet.append(list(head))
        for row in rows:
            sheet.append(_safe_xlsx(_safe(row)))
    out = io.BytesIO()
    book.save(out)
    return out.getvalue()


def _safe_xlsx(row: Sequence[Cell]) -> list[object]:
    # Decimal is not an xlsx type; the text cells are already prefixed.
    return [float(c) if isinstance(c, Decimal) else _printable(c) for c in row]

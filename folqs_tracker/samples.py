"""Count samples shipped in a week, from the retainer sample tracker.

This automates the "how many samples did we send" step. It is a *suggestion*,
never an authority: the tracker only records POs raised through the warehouse
portal, and the monthly figures in the wiki are consistently higher than the PO
count, so samples clearly also ship by routes this sheet never sees.

So the digest always shows the suggestion next to what it was derived from, and
`--samples-sent N` overrides it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from .weeks import Week

DATE_COLUMN_HINTS = ("date",)
QTY_COLUMN_HINTS = ("qty", "quantity")

# The tracker mixes "08/24/26" and "8/25/26"; both are US month-first.
_DATE_FORMATS = ("%m/%d/%y", "%m/%d/%Y", "%Y-%m-%d", "%d/%m/%y")


@dataclass
class SampleCount:
    week: Week
    rows: int          # purchase orders raised
    units: int         # sum of the QTY column
    unparsed: int      # rows whose date could not be read

    @property
    def suggestion(self) -> int:
        return self.units

    def describe(self) -> str:
        text = f"{self.units} units across {self.rows} POs in the sample tracker"
        if self.unparsed:
            text += f" ({self.unparsed} row(s) had an unreadable date and were skipped)"
        return text


def parse_date(text: str) -> Optional[date]:
    raw = str(text or "").strip()
    if not raw:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _column(header: list[str], hints: tuple[str, ...]) -> Optional[int]:
    for i, name in enumerate(header):
        cleaned = re.sub(r"\s+", " ", str(name or "")).strip().lower()
        if any(cleaned.startswith(h) for h in hints):
            return i
    return None


def count_from_rows(values: list[list[str]], week: Week) -> SampleCount:
    """Count shipments inside `week` from a raw grid of the tracker tab."""
    if not values:
        return SampleCount(week, 0, 0, 0)

    header = values[0]
    date_col = _column(header, DATE_COLUMN_HINTS)
    qty_col = _column(header, QTY_COLUMN_HINTS)
    if date_col is None:
        raise ValueError(
            f"no date column in the sample tracker; header was: {header}"
        )

    rows = units = unparsed = 0
    for row in values[1:]:
        if not any(str(c).strip() for c in row):
            continue
        raw_date = row[date_col] if date_col < len(row) else ""
        shipped = parse_date(raw_date)
        if shipped is None:
            if str(raw_date).strip():
                unparsed += 1
            continue
        if not week.contains(shipped):
            continue
        rows += 1
        qty = 1
        if qty_col is not None and qty_col < len(row):
            try:
                qty = int(float(str(row[qty_col]).strip() or 1))
            except ValueError:
                qty = 1
        units += max(qty, 0)

    return SampleCount(week, rows, units, unparsed)


def count_samples(
    service_account_json: str, sheet_id: str, tab: str, week: Week
) -> SampleCount:
    from .sheets import _open_worksheet

    worksheet = _open_worksheet(service_account_json, sheet_id, tab)
    return count_from_rows(worksheet.get_all_values(), week)

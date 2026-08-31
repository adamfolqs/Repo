"""Read and write the "Weekly Performance (1)" tab.

The tab is transposed -- metrics are rows, weeks are columns -- so publishing a
week means writing a *column*, not appending a row.

Two structural details drive the whole module:

* Section scoping. "Orders" is a row under both OVERALL METRICS and GMV MAX.
  Rows are therefore resolved within their section's boundaries, never by a
  global search of column A.
* Repeated headers. Every section carries its own ``Metric | week | week ...``
  header row. All four must be given the new week label, or the column reads as
  unlabelled inside the lower sections.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from .models import SECTIONS, WeeklyMetrics, coerce, format_value
from .weeks import EN_DASH

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
HEADER_LABEL = "Metric"
FIRST_DATA_COL = 1  # 0-based; column B


def _norm(text: str) -> str:
    """Normalize a label for comparison.

    Dashes are folded together because week labels are the lookup key and the
    tab is hand-edited: a column typed with a hyphen instead of an en dash
    would otherwise read as a different week, producing a duplicate column and
    silently losing every week-over-week delta.
    """
    text = str(text or "")
    for dash in ("\u2013", "\u2014", "\u2212"):
        text = text.replace(dash, "-")
    return re.sub(r"\s+", " ", text).strip().lower()


def parse_cell(text: str) -> Optional[float]:
    """Turn a displayed cell ("$4,061.21", "5.23%", "1,019") back into a number."""
    raw = str(text or "").strip()
    if not raw:
        return None
    cleaned = raw.replace("$", "").replace(",", "").replace("%", "").strip()
    if cleaned in {"", "-", "--", "N/A", "n/a"}:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


@dataclass
class SectionIndex:
    header: str
    metric_row: int              # 0-based index of this section's "Metric" row
    rows: dict[str, int]         # normalized row label -> 0-based row index


class WeeklyTrackerSheet:
    """The weekly tracker tab, indexed by section and row label."""

    def __init__(self, worksheet, values: list[list[str]]):
        self._ws = worksheet
        self._values = values
        self.sections = self._index(values)

    # ---------------------------------------------------------------- loading

    @classmethod
    def open(cls, service_account_json: str, sheet_id: str, tab: str) -> "WeeklyTrackerSheet":
        worksheet = _open_worksheet(service_account_json, sheet_id, tab)
        return cls(worksheet, worksheet.get_all_values())

    @staticmethod
    def _index(values: list[list[str]]) -> list[SectionIndex]:
        """Walk column A once, slicing the grid into the sections we know about."""
        wanted = {_norm(s.header): s for s in SECTIONS}
        col_a = [_norm(row[0]) if row else "" for row in values]

        starts: list[tuple[int, str]] = [
            (i, col_a[i]) for i in range(len(col_a)) if col_a[i] in wanted
        ]
        found: list[SectionIndex] = []

        for position, (start, key) in enumerate(starts):
            end = starts[position + 1][0] if position + 1 < len(starts) else len(values)
            metric_row = next(
                (i for i in range(start, end) if col_a[i] == _norm(HEADER_LABEL)), None
            )
            if metric_row is None:
                continue
            labels = {r.label for r in wanted[key].rows}
            rows = {
                col_a[i]: i
                for i in range(metric_row + 1, end)
                if col_a[i] and col_a[i] in {_norm(x) for x in labels}
            }
            found.append(SectionIndex(wanted[key].header, metric_row, rows))
        return found

    def validate(self) -> list[str]:
        """Every problem with the tab's shape, as human-readable strings."""
        problems: list[str] = []
        seen = {s.header for s in self.sections}
        for section in SECTIONS:
            if section.header not in seen:
                problems.append(f"section {section.header!r} not found in the tab")
                continue
            index = next(s for s in self.sections if s.header == section.header)
            for row in section.rows:
                if _norm(row.label) not in index.rows:
                    problems.append(
                        f"row {row.label!r} not found under {section.header!r}"
                    )
        return problems

    # ---------------------------------------------------------------- columns

    def _cell(self, row: int, col: int) -> str:
        if row >= len(self._values) or col >= len(self._values[row]):
            return ""
        return str(self._values[row][col] or "")

    @property
    def _primary_header(self) -> int:
        if not self.sections:
            raise RuntimeError("no known sections found in the tab")
        return self.sections[0].metric_row

    def week_labels(self) -> list[str]:
        row = self._values[self._primary_header] if self._primary_header < len(self._values) else []
        return [str(v).strip() for v in row[FIRST_DATA_COL:] if str(v).strip()]

    def find_column(self, label: str) -> Optional[int]:
        """0-based column for an existing week label, or None."""
        row = self._values[self._primary_header]
        for col in range(FIRST_DATA_COL, len(row)):
            if _norm(row[col]) == _norm(label):
                return col
        return None

    def next_free_column(self) -> int:
        row = self._values[self._primary_header]
        col = len(row)
        while col > FIRST_DATA_COL and not str(row[col - 1]).strip():
            col -= 1
        return max(col, FIRST_DATA_COL)

    # ---------------------------------------------------------------- reading

    def read_week(self, label: str) -> Optional[WeeklyMetrics]:
        """Pull a stored column back out as metrics, for week-over-week deltas."""
        col = self.find_column(label)
        if col is None:
            return None
        data: dict[str, float] = {}
        for section in SECTIONS:
            index = next((s for s in self.sections if s.header == section.header), None)
            if index is None:
                continue
            for row in section.rows:
                at = index.rows.get(_norm(row.label))
                if at is None:
                    continue
                value = parse_cell(self._cell(at, col))
                if value is not None:
                    # Counts are declared int. A cell holding "20.5" would fail
                    # validation and, through cmd_run's blanket handler, abandon
                    # an otherwise valid write over a stale neighbouring cell.
                    data[row.field] = coerce(row.field, value)
        return WeeklyMetrics(**data) if data else WeeklyMetrics()

    def completeness(self, label: str) -> tuple[int, int]:
        """(filled cells, total metric rows) for a week's column.

        Backfill uses this to tell an untouched week from a half-typed one, and
        to leave finished weeks alone.
        """
        total = sum(len(s.rows) for s in SECTIONS)
        col = self.find_column(label)
        if col is None:
            return 0, total
        filled = 0
        for section in SECTIONS:
            index = next((s for s in self.sections if s.header == section.header), None)
            if index is None:
                continue
            for row in section.rows:
                at = index.rows.get(_norm(row.label))
                if at is not None and self._cell(at, col).strip():
                    filled += 1
        return filled, total

    # ---------------------------------------------------------------- writing

    def plan_write(
        self, label: str, metrics: WeeklyMetrics, *, overwrite: bool = False
    ) -> tuple[list[dict], list[str], int]:
        """Build the cell updates for one week.

        Returns (updates, skipped, column). `skipped` lists cells left alone
        because they already hold a different value -- a re-run must not quietly
        wipe a correction someone typed in by hand.
        """
        import gspread.utils as gutils

        col = self.find_column(label)
        is_new = col is None
        if col is None:
            col = self.next_free_column()

        updates: list[dict] = []
        skipped: list[str] = []

        def put(row: int, value: str) -> None:
            updates.append({"range": gutils.rowcol_to_a1(row + 1, col + 1),
                            "values": [[value]]})

        for index in self.sections:
            if is_new or _norm(self._cell(index.metric_row, col)) != _norm(label):
                put(index.metric_row, label)

        for section in SECTIONS:
            index = next((s for s in self.sections if s.header == section.header), None)
            if index is None:
                continue
            for row in section.rows:
                at = index.rows.get(_norm(row.label))
                if at is None:
                    continue
                value = metrics.get(row.field)
                if value is None:
                    continue  # unknown stays empty, never zero
                rendered = format_value(value, row.kind)
                existing = self._cell(at, col).strip()
                if existing and not overwrite:
                    if parse_cell(existing) != parse_cell(rendered):
                        skipped.append(f"{row.label} (sheet has {existing}, run produced {rendered})")
                    continue
                put(at, rendered)

        return updates, skipped, col

    def apply(self, updates: list[dict], column: int) -> None:
        """Push the updates, growing the sheet first if the column is new."""
        if not updates:
            return
        if column + 1 > self._ws.col_count:
            self._ws.add_cols(column + 1 - self._ws.col_count)
        self._ws.batch_update(updates, value_input_option="USER_ENTERED")


def _open_worksheet(service_account_json: str, sheet_id: str, tab: str):
    from pathlib import Path

    import gspread
    from google.oauth2.service_account import Credentials

    key = Path(service_account_json)
    if not key.exists():
        raise FileNotFoundError(
            f"Service account key not found at {key}.\n"
            "Create one in Google Cloud Console, then share the target Sheet with "
            "its client_email as an Editor -- that share step is the one people miss."
        )
    creds = Credentials.from_service_account_file(str(key), scopes=SCOPES)
    book = gspread.authorize(creds).open_by_key(sheet_id)
    try:
        return book.worksheet(tab)
    except gspread.WorksheetNotFound as exc:
        available = ", ".join(w.title for w in book.worksheets())
        raise RuntimeError(
            f"tab {tab!r} not found in the sheet. Available tabs: {available}"
        ) from exc

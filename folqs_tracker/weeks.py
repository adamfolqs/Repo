"""Reporting weeks.

The Weekly Performance tracker runs **Friday -> Thursday**, labelled
``DD/MM–DD/MM`` with an EN DASH (U+2013). Both facts are load-bearing: the
label is how a week is located in the sheet, so a hyphen instead of an en dash
silently creates a duplicate column instead of updating the existing one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta

EN_DASH = "–"

# Friday. date.weekday() is Mon=0 .. Sun=6.
WEEK_START_WEEKDAY = 4

_LABEL_RE = re.compile(
    r"^\s*(\d{1,2})/(\d{1,2})\s*[" + EN_DASH + r"\-]\s*(\d{1,2})/(\d{1,2})\s*$"
)


@dataclass(frozen=True)
class Week:
    """One Friday-to-Thursday reporting week."""

    start: date  # Friday
    end: date    # Thursday

    @property
    def label(self) -> str:
        return f"{self.start:%d/%m}{EN_DASH}{self.end:%d/%m}"

    def contains(self, day: date) -> bool:
        return self.start <= day <= self.end

    def previous(self) -> "Week":
        return Week(self.start - timedelta(days=7), self.end - timedelta(days=7))

    def __str__(self) -> str:
        return self.label


def week_containing(day: date) -> Week:
    """The Fri->Thu week that `day` falls inside."""
    offset = (day.weekday() - WEEK_START_WEEKDAY) % 7
    start = day - timedelta(days=offset)
    return Week(start, start + timedelta(days=6))


def last_complete_week(today: date | None = None) -> Week:
    """The most recent week that has fully ended.

    Run on Friday the 28th, this returns the week ending Thursday the 27th --
    never the week in progress, which would report partial numbers as final.
    """
    today = today or date.today()
    current = week_containing(today)
    return current if today > current.end else current.previous()


def parse_label(label: str, reference_year: int) -> Week | None:
    """Parse a ``DD/MM–DD/MM`` column header back into a Week.

    The sheet omits the year, so `reference_year` supplies it; a week whose end
    month is lower than its start month has wrapped into January.
    """
    match = _LABEL_RE.match(str(label or ""))
    if not match:
        return None
    d1, m1, d2, m2 = (int(g) for g in match.groups())
    try:
        start = date(reference_year, m1, d1)
        end = date(reference_year + (1 if m2 < m1 else 0), m2, d2)
    except ValueError:
        return None
    return Week(start, end)

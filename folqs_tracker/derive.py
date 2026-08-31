"""Fill in computed metrics, and cross-check the ones Claude read off a screenshot.

Six of the tracker's rows are functions of other rows. Every formula here was
verified against the tracker's own history (May-July 2026) before being written
down, so a disagreement means bad input, not a bad formula.

The cross-check is the point. If a screenshot says AOV is $48.35 and
GMV/Orders says $57.22, one of the three numbers was misread -- and a silent
wrong number in a sheet that drives spend decisions is far worse than a loud
"check this". So we keep what was read, and report the discrepancy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from .models import WeeklyMetrics

SAMPLE_COGS_UNIT = 15.0  # matches the row label "Sample COGS Estimate ($15/sample)"

# Values are rounded to 2dp everywhere in this sheet, so allow a rounding-sized
# gap plus a little slack for the source dashboard's own rounding.
TOLERANCE = 0.02
RELATIVE_TOLERANCE = 0.01  # 1% -- dashboards round large currency figures


@dataclass
class Discrepancy:
    field: str
    read: float
    computed: float

    @property
    def pct(self) -> float:
        return abs(self.read - self.computed) / abs(self.computed) * 100 if self.computed else 100.0

    def __str__(self) -> str:
        return f"{self.field}: screenshot says {self.read:,.2f}, but the other numbers imply {self.computed:,.2f}"


def _ratio(numerator: Optional[float], denominator: Optional[float], scale: float = 1.0):
    if numerator is None or not denominator:
        return None
    return round(numerator / denominator * scale, 2)


# field -> how to compute it from the rest of the week
FORMULAS: dict[str, Callable[[WeeklyMetrics], Optional[float]]] = {
    "aov": lambda m: _ratio(m.gmv, m.orders),
    "ctr": lambda m: _ratio(m.clicks, m.impressions, 100.0),
    "ctor": lambda m: _ratio(m.orders, m.clicks, 100.0),
    "gmv_per_video": lambda m: _ratio(m.affiliate_gmv, m.videos_posted),
    "gmv_max_cost_per_order": lambda m: _ratio(m.gmv_max_cost, m.gmv_max_orders),
    "gmv_max_roi": lambda m: _ratio(m.gmv_max_revenue, m.gmv_max_cost),
    "sample_cogs": lambda m: (
        None if m.samples_sent is None else round(m.samples_sent * SAMPLE_COGS_UNIT, 2)
    ),
}


def _agrees(read: float, computed: float) -> bool:
    return abs(read - computed) <= max(TOLERANCE, abs(computed) * RELATIVE_TOLERANCE)


def derive(metrics: WeeklyMetrics) -> tuple[WeeklyMetrics, list[Discrepancy]]:
    """Return (completed metrics, discrepancies).

    Fills any derivable field left empty. Fields that were read are never
    overwritten -- the dashboard is the source of truth, and we only flag it.
    """
    filled = metrics.model_copy()
    discrepancies: list[Discrepancy] = []

    for field, formula in FORMULAS.items():
        computed = formula(filled)
        if computed is None:
            continue
        read = filled.get(field)
        if read is None:
            setattr(filled, field, computed)
        elif not _agrees(read, computed):
            discrepancies.append(Discrepancy(field, read, computed))

    return filled, discrepancies


def deltas(current: WeeklyMetrics, previous: Optional[WeeklyMetrics]) -> dict[str, float]:
    """Week-over-week percentage change, for the fields both weeks have.

    Skips a metric when last week was zero -- "up 0%" and "up infinity%" are
    both lies, and neither belongs in a digest someone acts on.
    """
    if previous is None:
        return {}
    out: dict[str, float] = {}
    for field in WeeklyMetrics.model_fields:
        now, before = current.get(field), previous.get(field)
        if now is None or before is None or not before:
            continue
        out[field] = round((now - before) / abs(before) * 100, 1)
    return out

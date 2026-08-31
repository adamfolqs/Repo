"""The weekly metric set, and how it maps onto the tracker tab.

`SECTIONS` mirrors the real layout of "Weekly Performance (1)" in the Folqs
TikTok Shop Wiki. That tab is **transposed**: metrics are rows, and each week
is a new *column*. Row labels are matched against column A, scoped to their
section -- "Orders" appears under both OVERALL METRICS and GMV MAX, so an
unscoped label lookup would write ad orders into the shop orders row.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel, Field

MONEY, COUNT, PERCENT, RATIO = "money", "count", "percent", "ratio"


@dataclass(frozen=True)
class MetricRow:
    label: str            # exact text in column A of the tab
    field: str            # attribute on WeeklyMetrics
    kind: str             # money | count | percent | ratio
    derived: bool = False  # computed by derive.py when absent from screenshots


@dataclass(frozen=True)
class Section:
    header: str           # the merged banner row, e.g. "OVERALL METRICS"
    rows: tuple[MetricRow, ...]


SECTIONS: tuple[Section, ...] = (
    Section("OVERALL METRICS", (
        MetricRow("GMV", "gmv", MONEY),
        MetricRow("Orders", "orders", COUNT),
        MetricRow("Items Sold", "items_sold", COUNT),
        MetricRow("Customers", "customers", COUNT),
        MetricRow("AOV", "aov", MONEY, derived=True),
        MetricRow("Refunds", "refunds", MONEY),
        MetricRow("Impressions", "impressions", COUNT),
        MetricRow("CTR", "ctr", PERCENT, derived=True),
        MetricRow("Clicks", "clicks", COUNT),
        MetricRow("CTOR", "ctor", PERCENT, derived=True),
        MetricRow("Shop Performance Score", "shop_performance_score", RATIO),
    )),
    Section("AFFILIATE PERFORMANCE", (
        MetricRow("Affiliate GMV", "affiliate_gmv", MONEY),
        MetricRow("Samples Sent", "samples_sent", COUNT),
        MetricRow("Videos Posted", "videos_posted", COUNT),
        MetricRow("GMV Per Video", "gmv_per_video", MONEY, derived=True),
    )),
    Section("GMV MAX", (
        MetricRow("Cost", "gmv_max_cost", MONEY),
        MetricRow("Orders", "gmv_max_orders", COUNT),
        MetricRow("Cost Per Order", "gmv_max_cost_per_order", MONEY, derived=True),
        MetricRow("ROI", "gmv_max_roi", RATIO, derived=True),
    )),
    Section("EXPENSES", (
        MetricRow("Retainer & Whitelisting Payments", "retainer_payments", MONEY),
        MetricRow("Sample COGS Estimate ($15/sample)", "sample_cogs", MONEY, derived=True),
    )),
)

ALL_ROWS: tuple[MetricRow, ...] = tuple(r for s in SECTIONS for r in s.rows)


class WeeklyMetrics(BaseModel):
    """One week's numbers.

    Every field is optional and defaults to None. That is deliberate: a metric
    nobody could read stays **empty**, and an empty cell is honest. A zero is
    not -- it silently drags down every average and trend computed over the row.
    """

    # OVERALL
    gmv: Optional[float] = None
    orders: Optional[int] = None
    items_sold: Optional[int] = None
    customers: Optional[int] = None
    aov: Optional[float] = None
    refunds: Optional[float] = None
    impressions: Optional[int] = None
    ctr: Optional[float] = Field(default=None, description="Percent, e.g. 2.83")
    clicks: Optional[int] = None
    ctor: Optional[float] = Field(default=None, description="Percent, e.g. 6.84")
    shop_performance_score: Optional[float] = None

    # AFFILIATE
    affiliate_gmv: Optional[float] = None
    samples_sent: Optional[int] = None
    videos_posted: Optional[int] = None
    gmv_per_video: Optional[float] = None

    # GMV MAX (paid ads)
    gmv_max_cost: Optional[float] = None
    gmv_max_orders: Optional[int] = None
    gmv_max_cost_per_order: Optional[float] = None
    gmv_max_roi: Optional[float] = None
    gmv_max_revenue: Optional[float] = Field(
        default=None,
        description="Ad-attributed gross revenue. Not a row in the weekly tab; "
                    "kept only so ROI can be derived and cross-checked.",
    )

    # EXPENSES
    retainer_payments: Optional[float] = None
    sample_cogs: Optional[float] = None

    def get(self, field: str) -> Optional[float]:
        return getattr(self, field, None)

    def missing(self, rows: tuple[MetricRow, ...] = ALL_ROWS) -> list[str]:
        return [r.label for r in rows if self.get(r.field) is None]


INT_FIELDS: frozenset[str] = frozenset(
    name for name, info in WeeklyMetrics.model_fields.items()
    if "int" in str(info.annotation)
)


def coerce(field: str, value: Optional[float]) -> Optional[float]:
    """Cast a parsed number to the type its field declares.

    Count metrics are declared int; letting a float land in one produces
    `48.0` in the JSON snapshot and a pydantic serializer warning on every run.
    """
    if value is None:
        return None
    return int(round(value)) if field in INT_FIELDS else float(value)


def format_value(value: Optional[float], kind: str) -> str:
    """Render a value the way the tracker's existing columns render it.

    Written with USER_ENTERED so Sheets parses "$1,234.56" back into a currency
    number and "2.83%" into a percentage -- value and appearance both preserved.
    """
    if value is None:
        return ""
    if kind == MONEY:
        return f"${value:,.2f}"
    if kind == COUNT:
        return f"{int(round(value)):,}"
    if kind == PERCENT:
        return f"{value:.2f}%"
    return f"{value:.2f}"

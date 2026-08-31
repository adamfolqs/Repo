"""Read TikTok Shop analytics screenshots into a WeeklyMetrics, using Claude.

This replaces the manual step: drop the week's screenshots in a folder, and the
numbers come back typed and validated instead of retyped by hand.

The prompt's one non-negotiable rule is that an unreadable number comes back
`null`. A hallucinated metric here doesn't look wrong -- it looks like data,
lands in the tracker, and quietly becomes the basis for a spend decision.
"""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from .models import WeeklyMetrics
from .weeks import Week

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
MAX_IMAGES = 20  # a week's dashboards; well inside request limits

SYSTEM = """\
You read TikTok Shop analytics screenshots and return the figures exactly as \
displayed.

Rules, in priority order:

1. NEVER invent, estimate, extrapolate or infer a number. If a metric is not \
   plainly legible in the images, return null for it. A null is correct and \
   expected; a plausible-looking guess is a serious error, because these \
   numbers drive real spend decisions and nobody can tell a guess from a \
   reading once it is in the spreadsheet.
2. Return figures for the requested reporting period only. Screenshots often \
   also show lifetime, 7-day, 28-day or comparison figures -- if you cannot \
   tell which period a number belongs to, return null.
3. Strip formatting: "$4,061.21" -> 4061.21, "58.7K" -> 58700, "5.23%" -> 5.23 \
   (percentages as the displayed number, NOT a fraction).
4. Distinguish shop-wide totals from paid-ads (GMV Max / ad manager) totals. \
   The gmv_max_* fields are ONLY for ads dashboards. If a screenshot does not \
   make clear which it is, return null rather than assuming.
5. In `sources`, name which screenshot each figure came from, and in \
   `unreadable`, list any metric you were asked for but could not read, with \
   the reason. Be specific -- this is what tells a human what to fill in by hand.
"""


class ExtractedMetrics(BaseModel):
    """What Claude reports back. Every metric is nullable by design."""

    gmv: Optional[float] = Field(None, description="Total shop GMV for the period")
    orders: Optional[int] = Field(None, description="Total shop orders")
    items_sold: Optional[int] = None
    customers: Optional[int] = None
    aov: Optional[float] = Field(None, description="Average order value, if shown")
    refunds: Optional[float] = Field(None, description="Refund amount, 0 only if explicitly shown as 0")
    impressions: Optional[int] = None
    ctr: Optional[float] = Field(None, description="Click-through rate as a percent, e.g. 5.23")
    clicks: Optional[int] = None
    ctor: Optional[float] = Field(None, description="Click-to-order rate as a percent, e.g. 2.74")
    shop_performance_score: Optional[float] = Field(None, description="Shop performance score, e.g. 4.60")

    affiliate_gmv: Optional[float] = Field(None, description="GMV attributed to affiliate/creator content")
    videos_posted: Optional[int] = Field(None, description="Affiliate videos posted in the period")
    samples_sent: Optional[int] = Field(
        None,
        description="Free samples shipped. Read from the Orders tab filtered by "
                    "Order Tag = the free-sample options, which shows a total like "
                    "'47 orders'. Only report this when the screenshot clearly shows "
                    "that free-sample order-tag filter applied AND the correct date "
                    "range; an unfiltered order count is NOT the sample count.",
    )

    gmv_max_cost: Optional[float] = Field(None, description="PAID ADS spend (GMV Max) only")
    gmv_max_orders: Optional[int] = Field(None, description="PAID ADS attributed orders only")
    gmv_max_revenue: Optional[float] = Field(None, description="PAID ADS attributed gross revenue only")
    gmv_max_roi: Optional[float] = Field(None, description="PAID ADS ROI/ROAS, e.g. 1.33")

    sources: list[str] = Field(default_factory=list,
                               description="Which screenshot each figure came from")
    unreadable: list[str] = Field(default_factory=list,
                                  description="Requested metrics that could not be read, and why")

    def to_weekly(self) -> WeeklyMetrics:
        shared = set(WeeklyMetrics.model_fields) & set(self.model_fields)
        return WeeklyMetrics(**{f: getattr(self, f) for f in shared})


def find_screenshots(directory: Path) -> list[Path]:
    """Every image in `directory`, newest last. Not recursive by accident --
    subfolders are searched too, so screenshots can be filed per week."""
    if not directory.exists():
        return []
    files = [p for p in sorted(directory.rglob("*"))
             if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES]
    return files


def _image_block(path: Path) -> dict:
    media_type = mimetypes.guess_type(path.name)[0] or "image/png"
    data = base64.standard_b64encode(path.read_bytes()).decode("ascii")
    return {"type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": data}}


def extract_metrics(
    screenshots: list[Path],
    week: Week,
    *,
    api_key: str = "",
    model: str = "claude-opus-5",
) -> ExtractedMetrics:
    """Send the week's screenshots to Claude and get typed metrics back."""
    if not screenshots:
        raise ValueError("no screenshots to read")
    if len(screenshots) > MAX_IMAGES:
        raise ValueError(
            f"{len(screenshots)} screenshots exceeds the {MAX_IMAGES}-image limit. "
            "Split them across runs or prune the folder -- they are not truncated, "
            "because a silently dropped image means a silently missing metric."
        )

    import anthropic

    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()

    content: list[dict] = []
    for path in screenshots:
        content.append({"type": "text", "text": f"Screenshot: {path.name}"})
        content.append(_image_block(path))
    content.append({"type": "text", "text": (
        f"Reporting period: {week.start:%d %B %Y} to {week.end:%d %B %Y} "
        f"(the week labelled {week.label}).\n\n"
        "Extract the metrics for this period only. Return null for anything you "
        "cannot read with certainty, and list it in `unreadable`."
    )})

    response = client.messages.parse(
        model=model,
        max_tokens=16000,
        system=SYSTEM,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": content}],
        output_format=ExtractedMetrics,
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(f"Claude declined to read the screenshots: {response.stop_details}")
    return response.parsed_output

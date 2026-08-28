"""Build the weekly digest: what landed, what moved, and what needs a human.

The flags section is the part that earns the bot its place. Anyone can read
numbers off a dashboard; the value is in being told, every week and without
being asked, which cells are still empty and which ones disagree with
themselves.
"""

from __future__ import annotations

import html
from dataclasses import dataclass, field
from typing import Optional

from .derive import Discrepancy
from .models import ALL_ROWS, SECTIONS, WeeklyMetrics, format_value
from .samples import SampleCount
from .weeks import Week

# The handful worth leading with, in the order a human reads them.
HEADLINE = ("gmv", "orders", "aov", "affiliate_gmv", "videos_posted",
            "gmv_max_cost", "gmv_max_roi")

_LABELS = {row.field: row.label for row in ALL_ROWS}
_KINDS = {row.field: row.kind for row in ALL_ROWS}


def _arrow(pct: Optional[float]) -> str:
    if pct is None:
        return ""
    if pct > 0.05:
        return f"  (+{pct:.1f}% WoW)"
    if pct < -0.05:
        return f"  ({pct:.1f}% WoW)"
    return "  (flat WoW)"


@dataclass
class Report:
    week: Week
    metrics: WeeklyMetrics
    deltas: dict[str, float] = field(default_factory=dict)
    discrepancies: list[Discrepancy] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    unreadable: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    samples: Optional[SampleCount] = None
    samples_source: str = ""
    sheet_url: str = ""
    screenshots: int = 0
    dry_run: bool = False

    # ------------------------------------------------------------- assembling

    NO_INPUT = ("No screenshots were in the inbox, so almost nothing could be "
                "filled in. Drop this week's TikTok Shop analytics screenshots in "
                "the inbox folder and re-run: python -m folqs_tracker run")

    @property
    def no_input(self) -> bool:
        return self.screenshots == 0

    @property
    def needs_attention(self) -> bool:
        return bool(self.discrepancies or self.missing or self.skipped
                    or self.unreadable or self.notes or self.no_input)

    def subject(self) -> str:
        prefix = "[DRY RUN] " if self.dry_run else ""
        flag = " - needs attention" if self.needs_attention else ""
        return f"{prefix}Folqs weekly performance {self.week.label}{flag}"

    def _headline_lines(self) -> list[str]:
        lines = []
        for field_name in HEADLINE:
            value = self.metrics.get(field_name)
            if value is None:
                continue
            rendered = format_value(value, _KINDS.get(field_name, "ratio"))
            lines.append(f"{_LABELS.get(field_name, field_name)}: {rendered}"
                         f"{_arrow(self.deltas.get(field_name))}")
        return lines

    def _flag_lines(self) -> list[str]:
        lines = []
        for d in self.discrepancies:
            lines.append(f"CHECK  {d}")
        for item in self.unreadable:
            lines.append(f"UNREAD {item}")
        for item in self.notes:
            lines.append(f"NOTE   {item}")
        for label in self.missing:
            lines.append(f"EMPTY  {label} - no value found, cell left blank")
        for item in self.skipped:
            lines.append(f"KEPT   {item} - existing value left as-is")
        return lines

    # -------------------------------------------------------------- rendering

    def text(self) -> str:
        out = [f"Folqs weekly performance - {self.week.label}",
               f"({self.week.start:%a %d %b} to {self.week.end:%a %d %b %Y})", ""]

        if self.dry_run:
            out += ["DRY RUN - nothing was written to the sheet.", ""]
        if self.no_input:
            out += [self.NO_INPUT, ""]

        headline = self._headline_lines()
        out += (["HEADLINE"] + headline) if headline else ["No metrics could be read."]
        out.append("")

        if self.samples:
            out += ["SAMPLES",
                    f"Used: {self.metrics.samples_sent if self.metrics.samples_sent is not None else 'not set'}"
                    f"  ({self.samples_source})",
                    f"Tracker shows: {self.samples.describe()}",
                    "The tracker only sees warehouse POs, so confirm before relying on it.",
                    ""]

        flags = self._flag_lines()
        if flags:
            out += [f"NEEDS ATTENTION ({len(flags)})"] + flags + [""]
        else:
            out += ["Nothing needs attention - every metric read cleanly.", ""]

        out.append(f"Screenshots read: {self.screenshots}")
        if self.sheet_url:
            out.append(f"Sheet: {self.sheet_url}")
        return "\n".join(out)

    def html_body(self) -> str:
        def esc(text: str) -> str:
            return html.escape(str(text))

        parts = [
            "<div style=\"font-family:-apple-system,Segoe UI,Roboto,sans-serif;"
            "max-width:640px;color:#111\">",
            f"<h2 style=\"margin:0 0 4px\">Folqs weekly performance</h2>",
            f"<p style=\"margin:0 0 16px;color:#666\">{esc(self.week.label)} "
            f"({self.week.start:%a %d %b} to {self.week.end:%a %d %b %Y})</p>",
        ]
        if self.dry_run:
            parts.append("<p style=\"background:#fef3c7;padding:8px 12px;border-radius:6px\">"
                         "<b>Dry run</b> - nothing was written to the sheet.</p>")
        if self.no_input:
            parts.append("<p style=\"background:#fee2e2;padding:8px 12px;border-radius:6px\">"
                         f"<b>No screenshots found.</b> {esc(self.NO_INPUT)}</p>")

        rows = []
        for section in SECTIONS:
            cells = [(r.label, self.metrics.get(r.field), r.kind, r.field) for r in section.rows]
            if not any(v is not None for _, v, _, _ in cells):
                continue
            rows.append(f"<tr><td colspan=3 style=\"padding:14px 8px 4px;font-weight:600;"
                        f"color:#374151\">{esc(section.header)}</td></tr>")
            for label, value, kind, field_name in cells:
                shown = format_value(value, kind) if value is not None else "&mdash;"
                delta = self.deltas.get(field_name)
                trend = "" if delta is None else (
                    f"<span style=\"color:{'#047857' if delta > 0 else '#b91c1c' if delta < 0 else '#6b7280'}\">"
                    f"{delta:+.1f}%</span>")
                rows.append(
                    "<tr>"
                    f"<td style=\"padding:3px 8px;border-top:1px solid #eee\">{esc(label)}</td>"
                    f"<td style=\"padding:3px 8px;border-top:1px solid #eee;text-align:right\">{shown}</td>"
                    f"<td style=\"padding:3px 8px;border-top:1px solid #eee;text-align:right\">{trend}</td>"
                    "</tr>")
        parts.append("<table style=\"border-collapse:collapse;width:100%;font-size:14px\">"
                     + "".join(rows) + "</table>")

        if self.samples:
            used = (self.metrics.samples_sent
                    if self.metrics.samples_sent is not None else "not set")
            parts.append(
                "<p style=\"margin:16px 0 0;font-size:13px;color:#374151\"><b>Samples:</b> "
                f"used {esc(used)} ({esc(self.samples_source)}). "
                f"Tracker shows {esc(self.samples.describe())}. "
                "The tracker only sees warehouse POs &mdash; confirm before relying on it.</p>")

        flags = self._flag_lines()
        if flags:
            items = "".join(f"<li style=\"margin:3px 0\">{esc(f)}</li>" for f in flags)
            parts.append(
                "<div style=\"margin-top:16px;background:#fff7ed;border-left:3px solid #ea580c;"
                "padding:10px 14px\">"
                f"<b>Needs attention ({len(flags)})</b>"
                f"<ul style=\"margin:6px 0 0;padding-left:18px;font-size:13px\">{items}</ul></div>")
        else:
            parts.append("<p style=\"margin-top:16px;color:#047857\">"
                         "Nothing needs attention &mdash; every metric read cleanly.</p>")

        parts.append(f"<p style=\"margin-top:16px;font-size:12px;color:#6b7280\">"
                     f"Screenshots read: {self.screenshots}")
        if self.sheet_url:
            parts.append(f" &middot; <a href=\"{esc(self.sheet_url)}\">Open the tracker</a>")
        parts.append("</p></div>")
        return "".join(parts)

    def telegram(self) -> str:
        """Short enough to read on a lock screen; Telegram caps at 4096 chars."""
        lines = [f"Folqs weekly performance - {self.week.label}"]
        if self.dry_run:
            lines.append("(dry run - sheet not updated)")
        if self.no_input:
            lines.append(self.NO_INPUT)
        lines.append("")
        lines += self._headline_lines() or ["No metrics could be read."]

        flags = self._flag_lines()
        if flags:
            lines += ["", f"Needs attention ({len(flags)}):"]
            lines += [f"- {f}" for f in flags[:6]]
            if len(flags) > 6:
                lines.append(f"- ...and {len(flags) - 6} more (see the email)")
        else:
            lines += ["", "Everything read cleanly."]

        if self.sheet_url:
            lines += ["", self.sheet_url]
        return "\n".join(lines)[:4000]

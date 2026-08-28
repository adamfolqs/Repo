"""Weekly performance tracker: week math, derivations, sheet layout, digest.

No network. The sheet fixture below is a faithful copy of the real
"Weekly Performance (1)" tab -- real labels, real values from July 2026 --
because the bugs that matter here are layout bugs, and a fixture invented from
the same constants it is testing would not catch one.
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from folqs_tracker.derive import derive, deltas
from folqs_tracker.models import ALL_ROWS, WeeklyMetrics, coerce, format_value
from folqs_tracker.report import Report
from folqs_tracker.samples import count_from_rows, parse_date
from folqs_tracker.sheets import WeeklyTrackerSheet, parse_cell
from folqs_tracker.weeks import last_complete_week, parse_label, week_containing

W1, W2 = "03/07–09/07", "10/07–16/07"

# A real slice of the tracker. Note "Orders" appears twice -- once under
# OVERALL METRICS (84) and once under GMV MAX (51).
GRID = [
    ["Weekly Performance Tracker", "", "", ""],
    ["", "", "", ""],
    ["", "", "", ""],
    ["OVERALL METRICS", "", "", ""],
    ["", "", "", ""],
    ["Metric", W1, W2, ""],
    ["GMV", "$4,061.21", "$770.93", ""],
    ["Orders", "84", "20", ""],
    ["Items Sold", "90", "21", ""],
    ["Customers", "83", "20", ""],
    ["AOV", "$48.35", "$38.55", ""],
    ["Refunds", "$34.44", "$0.00", ""],
    ["Impressions", "58,747", "21,088", ""],
    ["CTR", "5.23%", "4.10%", ""],
    ["Clicks", "3,070", "865", ""],
    ["CTOR", "2.74%", "2.31%", ""],
    ["Shop Performance Score", "4.60", "4.60", ""],
    ["", "", "", ""],
    ["AFFILIATE PERFORMANCE", "", "", ""],
    ["", "", "", ""],
    ["Metric", W1, W2, ""],
    ["Affiliate GMV", "$1,632.77", "$195.91", ""],
    ["Samples Sent", "13", "112", ""],
    ["Videos Posted", "8", "45", ""],
    ["GMV Per Video", "$204.10", "$4.35", ""],
    ["", "", "", ""],
    ["GMV MAX", "", "", ""],
    ["", "", "", ""],
    ["Metric", W1, W2, ""],
    ["Cost", "$1,824.39", "$904.33", ""],
    ["Orders", "51", "19", ""],
    ["Cost Per Order", "$35.77", "$47.60", ""],
    ["ROI", "1.33", "0.83", ""],
    ["", "", "", ""],
    ["EXPENSES", "", "", ""],
    ["", "", "", ""],
    ["Metric", W1, W2, ""],
    ["Retainer & Whitelisting Payments", "$0.00", "$515.00", ""],
    ["Sample COGS Estimate ($15/sample)", "$195.00", "$1,680.00", ""],
]


class FakeWorksheet:
    """Just enough of gspread's Worksheet to plan and apply a write."""

    def __init__(self, values):
        self._values = [list(r) for r in values]
        self.col_count = max(len(r) for r in values)
        self.applied = []
        self.added_cols = 0

    def get_all_values(self):
        return [list(r) for r in self._values]

    def batch_update(self, updates, value_input_option=None):
        self.applied.extend(updates)

    def add_cols(self, count):
        self.added_cols += count


def _sheet():
    ws = FakeWorksheet(GRID)
    return ws, WeeklyTrackerSheet(ws, ws.get_all_values())


# ------------------------------------------------------------------- weeks

def test_weeks_match_the_trackers_own_history():
    # Every label below is copied from the real tab; the generator must agree.
    assert week_containing(date(2026, 5, 22)).label == "22/05–28/05"
    assert week_containing(date(2026, 7, 17)).label == "17/07–23/07"
    assert week_containing(date(2026, 7, 23)).label == "17/07–23/07"

    # Run on Friday, report the week that just closed -- never the live one.
    assert last_complete_week(date(2026, 8, 28)).label == "21/08–27/08"
    assert last_complete_week(date(2026, 8, 27)).label == "14/08–20/08"

    assert parse_label(W1, 2026).start == date(2026, 7, 3)
    assert parse_label("26/12–01/01", 2026).end == date(2027, 1, 1), "year must roll over"
    assert parse_label("not a week", 2026) is None
    print("weeks OK")


# -------------------------------------------------------------- derivations

def test_derivations_reproduce_the_sheet():
    """Replay a real week; every derived cell must match what is in the tab."""
    week = WeeklyMetrics(gmv=4061.21, orders=84, clicks=3070, impressions=58747,
                         affiliate_gmv=1632.77, videos_posted=8, samples_sent=13,
                         gmv_max_cost=1824.39, gmv_max_orders=51)
    filled, problems = derive(week)
    assert not problems, problems
    assert filled.aov == 48.35
    assert filled.ctr == 5.23
    assert filled.ctor == 2.74
    assert filled.gmv_per_video == 204.10
    assert filled.gmv_max_cost_per_order == 35.77
    assert filled.sample_cogs == 195.00
    print("derivations OK")


def test_a_misread_number_is_caught_not_silently_kept():
    misread, problems = derive(WeeklyMetrics(gmv=4061.21, orders=84, aov=57.22))
    assert len(problems) == 1 and problems[0].field == "aov"
    assert misread.aov == 57.22, "the read value is reported, never overwritten"
    print("cross-check OK")


def test_unknown_metrics_stay_empty_never_zero():
    filled, _ = derive(WeeklyMetrics(gmv=100.0))
    assert filled.orders is None and filled.aov is None
    assert format_value(None, "money") == "", "an unknown must render as blank"
    assert format_value(0, "money") == "$0.00", "a real zero still renders"
    assert "Orders" in filled.missing()
    print("empty-not-zero OK")


def test_deltas_skip_undefined_growth():
    now = WeeklyMetrics(gmv=770.93, orders=20)
    before = WeeklyMetrics(gmv=4061.21, orders=0)
    changes = deltas(now, before)
    assert changes["gmv"] == -81.0
    assert "orders" not in changes, "growth from zero is undefined, not infinite"
    assert deltas(now, None) == {}
    print("deltas OK")


# ------------------------------------------------------------------- sheet

def test_sections_scope_duplicate_row_labels():
    _, sheet = _sheet()
    assert not sheet.validate(), sheet.validate()

    read = sheet.read_week(W1)
    assert read.orders == 84, "shop orders"
    assert read.gmv_max_orders == 51, "ad orders -- a global label search returns 84 here"
    assert read.gmv == 4061.21
    assert read.ctr == 5.23
    assert read.retainer_payments == 0.0
    print("section scoping OK")


def test_missing_row_is_reported_not_guessed():
    broken = [list(r) for r in GRID]
    broken[16][0] = "Shop Score"  # renamed upstream
    ws = FakeWorksheet(broken)
    problems = WeeklyTrackerSheet(ws, ws.get_all_values()).validate()
    assert any("Shop Performance Score" in p for p in problems), problems
    print("layout validation OK")


def test_new_week_appends_a_column_and_labels_every_section():
    ws, sheet = _sheet()
    assert sheet.find_column("17/07–23/07") is None
    assert sheet.next_free_column() == 3

    metrics, _ = derive(WeeklyMetrics(gmv=1000.0, orders=25, samples_sent=10))
    updates, skipped, col = sheet.plan_write("17/07–23/07", metrics)
    assert col == 3 and not skipped
    cells = {u["range"]: u["values"][0][0] for u in updates}

    # All four "Metric" header rows must carry the new label (rows 6/21/29/37 in A1).
    for a1 in ("D6", "D21", "D29", "D37"):
        assert cells[a1] == "17/07–23/07", f"{a1} missing the week label"
    assert cells["D7"] == "$1,000.00"
    assert cells["D8"] == "25"
    assert cells["D11"] == "$40.00", "AOV derived"
    assert cells["D23"] == "10"
    assert cells["D39"] == "$150.00", "sample COGS derived"
    assert "D9" not in cells, "Items Sold was unknown, so its cell is left untouched"

    sheet.apply(updates, col)
    assert len(ws.applied) == len(updates)
    print("new column OK")


def test_rerun_is_idempotent_and_protects_manual_edits():
    _, sheet = _sheet()
    same = WeeklyMetrics(gmv=4061.21, orders=84)
    updates, skipped, col = sheet.plan_write(W1, same)
    assert col == 1 and not updates and not skipped, "an unchanged re-run writes nothing"

    changed = WeeklyMetrics(gmv=9999.99)
    updates, skipped, _ = sheet.plan_write(W1, changed)
    assert not updates and len(skipped) == 1, "a differing value is kept, not clobbered"
    assert "GMV" in skipped[0]

    updates, skipped, _ = sheet.plan_write(W1, changed, overwrite=True)
    assert {u["range"] for u in updates} == {"B7"} and not skipped
    print("idempotency OK")


# ----------------------------------------------------------------- samples

def test_sample_counting_from_the_po_tracker():
    grid = [
        ["Date", "PO #", "Shipping Address", "Product ", "QTY ", "Order Link "],
        ["08/24/26", "PO-S0001", "A", "FLQS-1004", "1", "x"],
        ["8/25/26", "PO-S0002", "B", "FLQS-1004", "2", "x"],
        ["9/04/26", "PO-S0003", "next week", "FLQS-1004", "5", "x"],
        ["", "", "", "", "", ""],
        ["whenever", "PO-S0404", "bad date", "FLQS-1004", "1", "x"],
    ]
    count = count_from_rows(grid, week_containing(date(2026, 8, 26)))
    assert (count.rows, count.units, count.unparsed) == (2, 3, 1)
    assert parse_date("08/24/26") == date(2026, 8, 24)
    assert parse_date("") is None
    print("samples OK")


# ------------------------------------------------------------------ digest

def test_digest_renders_and_flags_what_needs_a_human():
    metrics, problems = derive(WeeklyMetrics(gmv=4061.21, orders=84, aov=57.22))
    report = Report(week=week_containing(date(2026, 7, 5)), metrics=metrics,
                    discrepancies=problems, missing=metrics.missing(),
                    unreadable=["Impressions: chart was cropped"],
                    sheet_url="https://example.com/sheet")
    text, telegram, html = report.text(), report.telegram(), report.html_body()

    assert report.needs_attention
    assert W1 in text and "$4,061.21" in text
    assert "CHECK" in text and "UNREAD" in text
    assert len(telegram) <= 4000 and "Needs attention" in telegram
    assert "<table" in html and "&amp;" not in report.subject()
    assert report.subject().endswith("needs attention")

    clean, _ = derive(WeeklyMetrics(**{r.field: 1 for r in ALL_ROWS}))
    assert not Report(week=week_containing(date(2026, 7, 5)), metrics=clean,
                      missing=clean.missing(), screenshots=4).needs_attention
    print("digest OK")


def test_cross_source_note_reaches_the_digest():
    """A samples figure that disagrees with the PO tracker must be surfaced."""
    report = Report(week=week_containing(date(2026, 7, 5)),
                    metrics=WeeklyMetrics(gmv=1.0), screenshots=2,
                    notes=["Samples Sent is 47, but the sample tracker shows 12"])
    assert report.needs_attention
    assert "NOTE" in report.text() and "47" in report.telegram()
    print("cross-source note OK")


def test_an_empty_inbox_is_flagged_loudly():
    """A scheduled run can fire before anyone drops the screenshots in."""
    report = Report(week=week_containing(date(2026, 7, 5)),
                    metrics=WeeklyMetrics(), screenshots=0)
    assert report.no_input and report.needs_attention
    assert "No screenshots" in report.text()
    assert "re-run" in report.telegram()
    assert "No screenshots found" in report.html_body()
    print("empty inbox OK")


def test_cell_parsing_and_coercion_round_trip():
    assert parse_cell("$4,061.21") == 4061.21
    assert parse_cell("5.23%") == 5.23
    assert parse_cell("") is None and parse_cell("N/A") is None
    assert coerce("orders", 48.0) == 48 and isinstance(coerce("orders", 48.0), int)
    assert isinstance(coerce("gmv", 48), float)
    print("parsing OK")


TESTS = [
    test_weeks_match_the_trackers_own_history,
    test_derivations_reproduce_the_sheet,
    test_a_misread_number_is_caught_not_silently_kept,
    test_unknown_metrics_stay_empty_never_zero,
    test_deltas_skip_undefined_growth,
    test_sections_scope_duplicate_row_labels,
    test_missing_row_is_reported_not_guessed,
    test_new_week_appends_a_column_and_labels_every_section,
    test_rerun_is_idempotent_and_protects_manual_edits,
    test_sample_counting_from_the_po_tracker,
    test_digest_renders_and_flags_what_needs_a_human,
    test_cross_source_note_reaches_the_digest,
    test_an_empty_inbox_is_flagged_loudly,
    test_cell_parsing_and_coercion_round_trip,
]

if __name__ == "__main__":
    for test in TESTS:
        test()
    print(f"\nALL {len(TESTS)} TRACKER TESTS PASSED")

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

from folqs_tracker.capture import (DEFAULT_PLAN, CaptureTarget, load_plan,
                                   import_calibration, looks_logged_out,
                                   save_plan, templatize_dates)
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
        import gspread.utils as gutils
        self.applied.extend(updates)
        for update in updates:
            row, col = gutils.a1_to_rowcol(update["range"])
            while len(self._values) < row:
                self._values.append([])
            line = self._values[row - 1]
            while len(line) < col:
                line.append("")
            line[col - 1] = update["values"][0][0]
        self.col_count = max(self.col_count, max(len(r) for r in self._values))

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


# ----------------------------------------------------------------- capture

def test_login_pages_are_recognised():
    """A logged-out Seller Center still screenshots perfectly -- so detect it."""
    for url in ("https://seller-us.tiktok.com/account/login",
                "https://seller-us.tiktok.com/passport/web/login",
                "https://accounts.tiktok.com/x"):
        assert looks_logged_out(url), url
    assert not looks_logged_out("https://seller-us.tiktok.com/compass/shop-analysis")
    print("login detection OK")


def test_capture_urls_carry_the_reporting_week():
    target = CaptureTarget("x", "X", url="https://e.com?from={start}&to={end}")
    assert target.resolve_url(week_containing(date(2026, 8, 26))) == \
        "https://e.com?from=2026-08-21&to=2026-08-27"
    assert CaptureTarget("y", "Y", actions=[{"click": "a"}]).resolve_url(
        week_containing(date(2026, 8, 26))) == ""
    print("capture urls OK")


def test_capture_plan_validates_and_round_trips(tmp=None):
    import tempfile
    bad = [({"key": "a", "name": "A"}, "neither a url nor actions"),
           ({"name": "no key", "url": "x"}, "needs a 'key'"),
           ({"key": "a", "name": "A", "url": "x", "nope": 1}, "unknown key")]
    for raw, expected in bad:
        try:
            CaptureTarget.from_dict(raw)
            assert False, f"should have rejected {raw}"
        except ValueError as exc:
            assert expected in str(exc), f"{exc} != {expected}"

    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "plan.json"
        save_plan(list(DEFAULT_PLAN), path)
        assert [t.key for t in load_plan(path)] == [t.key for t in DEFAULT_PLAN]
    assert [t.key for t in load_plan(Path("does-not-exist.json"))] == \
        [t.key for t in DEFAULT_PLAN], "missing plan falls back to defaults"
    print("capture plan OK")


def test_every_url_target_asserts_its_own_content():
    """Without an expect_text, an error page would be saved as if it were data."""
    for target in DEFAULT_PLAN:
        if target.url and not target.actions:
            assert target.expect_text, f"{target.key} has no content assertion"
    print("content assertions OK")


# ------------------------------------------------- regressions (code review)

def test_recorded_urls_keep_their_date_range_parameterised():
    """Calibration bakes one week into the URL; it must come back out.

    Left verbatim, every run would photograph the calibration week while
    telling the extractor it was a different one -- right-looking numbers for
    the wrong seven days, invisible on the screenshot.
    """
    url, fmt, found = templatize_dates(
        "https://seller-us.tiktok.com/compass?start_date=2026-07-03&end_date=2026-07-09")
    assert found and fmt == "%Y-%m-%d"
    assert CaptureTarget("k", "K", url=url, date_format=fmt).resolve_url(
        week_containing(date(2026, 8, 26))
    ) == "https://seller-us.tiktok.com/compass?start_date=2026-08-21&end_date=2026-08-27"

    epoch_url, fmt, found = templatize_dates("https://x.com?s=1751500800&e=1752105600")
    assert found and "{start}" in epoch_url and "{end}" in epoch_url

    _, _, found = templatize_dates("https://x.com/compass")
    assert not found, "a URL with no dates must be reported, not silently accepted"
    print("date parameterisation OK")


def test_literal_braces_in_a_url_do_not_kill_the_run():
    """Real Seller Center URLs carry JSON-ish query values."""
    target = CaptureTarget("k", "K", url='https://x.com?filter={"tag":1}&s={start}')
    assert target.resolve_url(week_containing(date(2026, 8, 26))) == \
        'https://x.com?filter={"tag":1}&s=2026-08-21'
    print("brace-safe urls OK")


def test_a_hyphen_week_label_is_not_a_new_column():
    """The tab is hand-edited; a typed hyphen must still match the en dash."""
    grid = [list(r) for r in GRID]
    grid[5][1] = "03/07-09/07"      # hyphen, not en dash
    ws = FakeWorksheet(grid)
    sheet = WeeklyTrackerSheet(ws, ws.get_all_values())
    assert sheet.find_column(W1) == 1, "must update the existing column, not append"
    print("dash folding OK")


def test_a_fractional_count_cell_does_not_abandon_the_write():
    grid = [list(r) for r in GRID]
    grid[7][1] = "20.5"             # Orders is declared int
    ws = FakeWorksheet(grid)
    read = WeeklyTrackerSheet(ws, ws.get_all_values()).read_week(W1)
    assert read.orders == 20 and isinstance(read.orders, int)
    print("count coercion OK")


def test_capture_filenames_come_from_the_full_plan():
    """`--only` must not renumber a screen into a collision with a stale file."""
    positions = {t.key: i for i, t in enumerate(DEFAULT_PLAN, 1)}
    assert positions["samples"] == 4 and positions["ads"] == 5
    assert len(set(positions.values())) == len(DEFAULT_PLAN)
    print("capture numbering OK")


def test_archiving_the_same_week_three_times_loses_nothing():
    import tempfile
    from folqs_tracker.cli import _archive
    from folqs_tracker.config import TrackerSettings

    week = week_containing(date(2026, 8, 26))
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        settings = TrackerSettings(archive_dir=root / "archive")
        for _ in range(3):
            shot = root / "01_shop.png"
            shot.write_bytes(b"png")
            _archive([shot], settings, week)
        archived = list((settings.archive_dir).rglob("*.png"))
        assert len(archived) == 3, f"expected 3 kept files, found {len(archived)}"
    print("archive collisions OK")


# ---------------------------------------------------------------- backfill

def test_backfill_walks_weeks_in_order_and_appends_columns():
    """Catching up must produce chronological columns and skip finished weeks."""
    import folqs_tracker.cli as cli
    from folqs_tracker.sheets import WeeklyTrackerSheet

    ws = FakeWorksheet(GRID)
    WeeklyTrackerSheet.open = classmethod(
        lambda cls, *a, **k: cls(ws, ws.get_all_values()))

    produced = {
        "17/07–23/07": WeeklyMetrics(gmv=770.93, orders=20),
        "24/07–30/07": WeeklyMetrics(gmv=900.00, orders=25),
        "31/07–06/08": WeeklyMetrics(gmv=1100.00, orders=30),
    }

    def fake_collect(week, args, settings, *_):
        if week.label not in produced:
            raise RuntimeError("no screenshots for this week")
        metrics, _ = derive(produced[week.label])
        return metrics

    cli._collect_week = fake_collect
    cli._snapshot = lambda *a, **k: Path("x")
    cli._deliver = lambda *a, **k: []

    args = cli.build_parser().parse_args(
        ["backfill", "--from", "17/07-23/07", "--to", "07/08-13/08",
         "--year", "2026", "--no-notify"])
    rc = cli.cmd_backfill(args, cli.TrackerSettings.load())

    sheet = WeeklyTrackerSheet(ws, ws.get_all_values())
    labels = sheet.week_labels()
    assert labels == [W1, W2, "17/07–23/07", "24/07–30/07", "31/07–06/08"], labels
    assert sheet.read_week("24/07–30/07").gmv == 900.00
    assert sheet.read_week("31/07–06/08").orders == 30
    # W1 and W2 were already complete and must be untouched.
    assert sheet.read_week(W1).gmv == 4061.21
    # The fourth week had no data; it fails without stopping the earlier three.
    assert rc == 1, "a failed week should surface as a non-zero exit"
    print("backfill ordering OK")


def test_backfill_skips_weeks_that_are_already_complete():
    import folqs_tracker.cli as cli
    from folqs_tracker.sheets import WeeklyTrackerSheet

    ws = FakeWorksheet(GRID)
    sheet = WeeklyTrackerSheet(ws, ws.get_all_values())
    filled, total = sheet.completeness(W1)
    assert filled >= cli.COMPLETE_ENOUGH, f"{filled}/{total} should count as complete"
    assert sheet.completeness("31/12–06/01") == (0, total)

    # The first incomplete week before a complete one is found by walking back.
    from folqs_tracker.weeks import parse_label
    first = cli._first_incomplete(sheet, parse_label("31/07–06/08", 2026))
    assert first.label == "17/07–23/07", first.label
    print("backfill skipping OK")


def test_browser_recon_json_becomes_a_capture_plan():
    """The Chrome session reports what it saw; this folds it into the plan."""
    import tempfile

    recon = {
        "targets": [
            {"key": "shop_analytics",
             "url": "https://s.tiktok.com/compass?start_date=2026-07-03&end_date=2026-07-09",
             "dates_in_url": True, "expect_text": "Items Sold"},
            {"key": "account_health", "url": "https://s.tiktok.com/account-health",
             "dates_in_url": False, "expect_text": "Shop Performance Score"},
        ],
        "samples_click_sequence": ["Filter", "Order Tag", "Free Sample from Seller", "Apply"],
        "samples_applied_filter_text": "Order Tag: Free Sample from Seller",
    }

    with tempfile.TemporaryDirectory() as d:
        path, warnings = import_calibration(recon, Path(d) / "plan.json")
        plan = {t.key: t for t in load_plan(path)}

    # Dates are re-parameterised, so the plan can be pointed at any week.
    assert plan["shop_analytics"].calibrated
    assert plan["shop_analytics"].resolve_url(week_containing(date(2026, 8, 26))) == \
        "https://s.tiktok.com/compass?start_date=2026-08-21&end_date=2026-08-27"
    assert plan["shop_analytics"].expect_text == "Items Sold"

    # The samples filter becomes a click script guarded by the applied-filter chip.
    assert [a["click"] for a in plan["samples"].actions if "click" in a] == [
        "text=Filter", "text=Order Tag", "text=Free Sample from Seller", "text=Apply"]
    assert plan["samples"].expect_text == "Order Tag: Free Sample from Seller"

    # Screens that cannot be pointed at a past week must be called out.
    assert any("account_health" in w and "not in its URL" in w for w in warnings), warnings
    assert any("creator" in w for w in warnings), "an unreported screen must warn"
    print("calibration import OK")


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
    test_login_pages_are_recognised,
    test_capture_urls_carry_the_reporting_week,
    test_capture_plan_validates_and_round_trips,
    test_every_url_target_asserts_its_own_content,
    test_recorded_urls_keep_their_date_range_parameterised,
    test_literal_braces_in_a_url_do_not_kill_the_run,
    test_a_hyphen_week_label_is_not_a_new_column,
    test_a_fractional_count_cell_does_not_abandon_the_write,
    test_capture_filenames_come_from_the_full_plan,
    test_archiving_the_same_week_three_times_loses_nothing,
    test_backfill_walks_weeks_in_order_and_appends_columns,
    test_backfill_skips_weeks_that_are_already_complete,
    test_browser_recon_json_becomes_a_capture_plan,
]

if __name__ == "__main__":
    for test in TESTS:
        test()
    print(f"\nALL {len(TESTS)} TRACKER TESTS PASSED")

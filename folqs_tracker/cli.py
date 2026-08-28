"""Command line entry point for the weekly performance tracker.

    python -m folqs_tracker run --dry-run     # read + report, touch nothing
    python -m folqs_tracker run               # the scheduled weekly job
    python -m folqs_tracker check             # validate config and tab layout
    python -m folqs_tracker notify-test       # prove email + Telegram work
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import traceback
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from .capture import (CaptureError, SessionExpired, calibrate, capture_all,
                      load_plan, save_session)
from .config import TrackerSettings
from .derive import derive, deltas
from .models import ALL_ROWS, WeeklyMetrics, coerce
from .report import Report
from .samples import SampleCount, count_samples
from .weeks import Week, last_complete_week, parse_label, week_containing

SHEET_URL = "https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
_FIELDS = {row.field for row in ALL_ROWS} | {"gmv_max_revenue"}


# --------------------------------------------------------------------- helpers

def _resolve_week(args) -> Week:
    if args.week:
        parsed = parse_label(args.week, args.year or date.today().year)
        if not parsed:
            raise ValueError(f"could not parse --week {args.week!r}; expected DD/MM-DD/MM")
        return parsed
    if args.week_ending:
        try:
            day = datetime.strptime(args.week_ending, "%Y-%m-%d").date()
        except ValueError as exc:
            raise ValueError("--week-ending must be YYYY-MM-DD") from exc
        return week_containing(day)
    return last_complete_week()


def _parse_overrides(pairs: list[str]) -> dict[str, float]:
    out: dict[str, float] = {}
    for pair in pairs or []:
        if "=" not in pair:
            raise ValueError(f"--set expects field=value, got {pair!r}")
        key, raw = pair.split("=", 1)
        key = key.strip()
        if key not in _FIELDS:
            raise ValueError(
                f"unknown metric {key!r}. Valid: {', '.join(sorted(_FIELDS))}"
            )
        cleaned = raw.strip().replace("$", "").replace(",", "").replace("%", "")
        try:
            out[key] = coerce(key, float(cleaned))
        except ValueError as exc:
            raise ValueError(f"--set {key}: {raw!r} is not a number") from exc
    return out


def _snapshot(settings: TrackerSettings, week: Week, metrics: WeeklyMetrics,
              report: Report) -> Path:
    """Write the week's numbers to disk before touching anything remote.

    Cheap insurance: if the sheet write or the notifications fail, the extracted
    numbers still exist and the run does not have to be repeated (or re-billed).
    """
    settings.snapshot_dir.mkdir(parents=True, exist_ok=True)
    path = settings.snapshot_dir / f"{week.start:%Y-%m-%d}_{week.end:%Y-%m-%d}.json"
    path.write_text(json.dumps({
        "week": week.label,
        "week_start": week.start.isoformat(),
        "week_end": week.end.isoformat(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "metrics": metrics.model_dump(),
        "missing": report.missing,
        "discrepancies": [str(d) for d in report.discrepancies],
        "unreadable": report.unreadable,
    }, indent=2), encoding="utf-8")
    return path


def _archive(screenshots: list[Path], settings: TrackerSettings, week: Week) -> int:
    """Move processed screenshots out of the inbox.

    Without this, next week's unattended run re-reads this week's images and
    reports last week's numbers as current -- the failure mode nobody notices.
    """
    if not screenshots:
        return 0
    destination = settings.archive_dir / f"{week.start:%Y-%m-%d}_{week.end:%Y-%m-%d}"
    destination.mkdir(parents=True, exist_ok=True)
    moved = 0
    for path in screenshots:
        target = destination / path.name
        if target.exists():
            target = destination / f"{path.stem}_{moved}{path.suffix}"
        shutil.move(str(path), str(target))
        moved += 1
    return moved


def _deliver(report: Report, settings: TrackerSettings, *, quiet: bool) -> list[str]:
    """Send the digest. Never raises -- a delivery failure must not lose the run."""
    problems: list[str] = []
    if quiet:
        return problems

    if settings.email_configured:
        try:
            from .notify.email_digest import send_email
            to = send_email(
                host=settings.smtp_host, port=settings.smtp_port,
                username=settings.smtp_user, password=settings.smtp_password,
                sender=settings.email_from, recipients=settings.email_to,
                subject=report.subject(), text=report.text(), html=report.html_body(),
            )
            print(f"  email sent to {', '.join(to)}")
        except Exception as exc:
            problems.append(f"email failed: {exc}")
    else:
        problems.append("email skipped: SMTP_HOST / REPORT_EMAIL_FROM / REPORT_EMAIL_TO not set")

    if settings.telegram_configured:
        try:
            from .notify.telegram import send_telegram
            send_telegram(token=settings.telegram_bot_token,
                          chat_id=settings.telegram_chat_id, text=report.telegram())
            print("  telegram sent")
        except Exception as exc:
            problems.append(f"telegram failed: {exc}")
    else:
        problems.append("telegram skipped: TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set")

    for problem in problems:
        print(f"  {problem}", file=sys.stderr)
    return problems


# ------------------------------------------------------------------- commands

def cmd_run(args, settings: TrackerSettings) -> int:
    week = _resolve_week(args)
    print(f"Week {week.label}  ({week.start:%d %b} to {week.end:%d %b %Y})")

    capture_notes: list[str] = []

    # ---- 0. take the screenshots ourselves, if asked
    if args.capture:
        print("  capturing screens from Seller Center")
        result = capture_all(
            week, settings.screenshot_dir, settings.session_file,
            plan=load_plan(settings.capture_plan),
            headless=settings.capture_headless and not args.headed,
        )
        for name, why in result.failed:
            capture_notes.append(f"could not capture {name}: {why}")
        print(f"  captured {len(result.saved)} screen(s), {len(result.failed)} failed")

    # ---- 1. read the screenshots
    from .extract import find_screenshots

    screenshots = [] if args.no_extract else find_screenshots(settings.screenshot_dir)
    metrics = WeeklyMetrics()
    unreadable: list[str] = []

    if screenshots:
        print(f"  reading {len(screenshots)} screenshot(s) with {settings.model}")
        from .extract import extract_metrics
        extracted = extract_metrics(screenshots, week,
                                    api_key=settings.anthropic_api_key,
                                    model=settings.model)
        metrics = extracted.to_weekly()
        unreadable = list(extracted.unreadable)
        for note in extracted.sources:
            print(f"    {note}")
    elif not args.no_extract:
        print(f"  no screenshots in {settings.screenshot_dir} -- "
              "reporting only what --set provides", file=sys.stderr)

    # ---- 2. manual values (retainer payments never appear in a TikTok screenshot)
    for key, value in _parse_overrides(args.set).items():
        setattr(metrics, key, value)

    # ---- 3. samples sent
    samples: Optional[SampleCount] = None
    samples_source = ""
    if args.samples_sent is not None:
        metrics.samples_sent = args.samples_sent
        samples_source = "--samples-sent"
    if not args.no_samples and settings.samples_sheet_id:
        try:
            samples = count_samples(settings.service_account_json,
                                    settings.samples_sheet_id,
                                    settings.samples_tab, week)
            print(f"  samples: {samples.describe()}")
            if metrics.samples_sent is None:
                metrics.samples_sent = samples.suggestion
                samples_source = "counted from the sample tracker"
        except Exception as exc:
            print(f"  sample tracker unavailable: {exc}", file=sys.stderr)
    if metrics.samples_sent is not None and not samples_source:
        samples_source = "read from the Orders tab (free-sample tag)"

    # The authoritative count is the free-sample-tagged order total in Seller
    # Center. The PO tracker is a second, partial view of the same thing, so a
    # disagreement is worth surfacing rather than silently preferring either.
    notes: list[str] = list(capture_notes)
    if (samples is not None and metrics.samples_sent is not None
            and samples_source != "counted from the sample tracker"
            and metrics.samples_sent != samples.units):
        notes.append(
            f"Samples Sent is {metrics.samples_sent} ({samples_source}), but the "
            f"sample tracker shows {samples.units} units across {samples.rows} POs. "
            "The tracker only sees warehouse POs, so a gap is expected -- worth a "
            "glance if it is large."
        )

    # ---- 4. derive + cross-check
    metrics, discrepancies = derive(metrics)
    for d in discrepancies:
        print(f"  CHECK {d}", file=sys.stderr)

    # ---- 5. the sheet
    previous: Optional[WeeklyMetrics] = None
    skipped: list[str] = []
    write_error = ""
    sheet = None
    if not args.no_sheet:
        from .sheets import WeeklyTrackerSheet
        try:
            sheet = WeeklyTrackerSheet.open(settings.service_account_json,
                                            settings.wiki_sheet_id, settings.weekly_tab)
            problems = sheet.validate()
            if problems:
                raise RuntimeError("the tab does not have the expected shape: "
                                   + "; ".join(problems))
            previous = sheet.read_week(week.previous().label)
            updates, skipped, column = sheet.plan_write(week.label, metrics,
                                                        overwrite=args.overwrite)
            if args.dry_run:
                print(f"  DRY RUN: would write {len(updates)} cell(s) to column {column + 1}")
            else:
                sheet.apply(updates, column)
                print(f"  wrote {len(updates)} cell(s) to column {column + 1}")
            for item in skipped:
                print(f"  KEPT {item}", file=sys.stderr)
        except Exception as exc:
            write_error = str(exc)
            print(f"  sheet update FAILED: {exc}", file=sys.stderr)

    # ---- 6. report
    report = Report(
        week=week, metrics=metrics, deltas=deltas(metrics, previous),
        discrepancies=discrepancies,
        missing=metrics.missing(), skipped=skipped, unreadable=unreadable,
        notes=notes,
        samples=samples, samples_source=samples_source or "not set",
        sheet_url=SHEET_URL.format(sheet_id=settings.wiki_sheet_id),
        screenshots=len(screenshots), dry_run=args.dry_run,
    )
    if write_error:
        report.skipped.append(f"sheet was NOT updated: {write_error}")

    snapshot = _snapshot(settings, week, metrics, report)
    print(f"  snapshot -> {snapshot}")

    if args.print_report:
        print("\n" + report.text() + "\n")

    _deliver(report, settings, quiet=args.no_notify)

    if screenshots and not args.dry_run and not args.keep_screenshots:
        moved = _archive(screenshots, settings, week)
        print(f"  archived {moved} screenshot(s) to {settings.archive_dir}")

    return 1 if write_error else 0


def cmd_check(args, settings: TrackerSettings) -> int:
    """Validate everything the scheduled run depends on, without writing."""
    ok = True

    def line(good: bool, text: str) -> None:
        nonlocal ok
        ok = ok and good
        print(f"  [{'OK ' if good else 'FAIL'}] {text}")

    print("Configuration")
    line(bool(settings.anthropic_api_key) or bool(__import__("os").getenv("ANTHROPIC_API_KEY")),
         "ANTHROPIC_API_KEY set")
    line(Path(settings.service_account_json).exists(),
         f"service account key at {settings.service_account_json}")
    line(settings.email_configured, f"email digest -> {settings.email_to}")
    line(settings.telegram_configured, "telegram configured")
    line(settings.screenshot_dir.exists(), f"screenshot inbox {settings.screenshot_dir}")

    print("\nAutomated capture")
    line(settings.session_file.exists(),
         f"saved TikTok session at {settings.session_file}"
         + ("" if settings.session_file.exists() else "  -- run: folqs_tracker login"))
    try:
        plan = load_plan(settings.capture_plan)
        uncalibrated = [t.key for t in plan if not t.calibrated]
        line(not uncalibrated,
             f"{len(plan)} capture target(s) calibrated"
             if not uncalibrated
             else f"uncalibrated: {', '.join(uncalibrated)}  -- run: folqs_tracker calibrate")
    except Exception as exc:
        line(False, f"capture plan unreadable: {exc}")

    week = last_complete_week()
    print(f"\nWeek to report: {week.label}")
    from .extract import find_screenshots
    found = find_screenshots(settings.screenshot_dir)
    print(f"  {len(found)} screenshot(s) waiting")

    print("\nSheet")
    try:
        from .sheets import WeeklyTrackerSheet
        sheet = WeeklyTrackerSheet.open(settings.service_account_json,
                                        settings.wiki_sheet_id, settings.weekly_tab)
        problems = sheet.validate()
        for problem in problems:
            line(False, problem)
        if not problems:
            line(True, f"tab {settings.weekly_tab!r} has all "
                       f"{len(ALL_ROWS)} expected metric rows")
        labels = sheet.week_labels()
        print(f"  {len(labels)} week column(s); most recent: {labels[-1] if labels else 'none'}")
        existing = sheet.find_column(week.label)
        print(f"  column for {week.label}: "
              f"{'exists (would update)' if existing is not None else 'new (would append)'}")
    except Exception as exc:
        line(False, f"cannot open the tracker tab: {exc}")

    print("\n" + ("All checks passed." if ok else "Some checks failed -- see above."))
    return 0 if ok else 1


def cmd_notify_test(args, settings: TrackerSettings) -> int:
    """Send a sample digest so delivery is proven before a real Friday run."""
    week = last_complete_week()
    metrics, _ = derive(WeeklyMetrics(gmv=1234.56, orders=25, clicks=900,
                                      impressions=30000, affiliate_gmv=400.0,
                                      videos_posted=12, samples_sent=14,
                                      gmv_max_cost=500.0, gmv_max_orders=18))
    report = Report(week=week, metrics=metrics, missing=metrics.missing(),
                    sheet_url=SHEET_URL.format(sheet_id=settings.wiki_sheet_id),
                    dry_run=True)
    print(report.text())
    print()
    problems = _deliver(report, settings, quiet=False)
    return 1 if problems else 0


# --------------------------------------------------------------------- parser

def cmd_login(args, settings: TrackerSettings) -> int:
    """Log in once, by hand, and save the session for later runs."""
    path = save_session(settings.session_file)
    print(f"\nSession saved to {path} (owner-readable only).")
    print("It is a credential -- it is gitignored, and must not be shared.")
    print("When it expires, run this again.")
    return 0


def cmd_calibrate(args, settings: TrackerSettings) -> int:
    """Record the real Seller Center URLs from your own account."""
    calibrate(settings.session_file, settings.capture_plan)
    return 0


def cmd_capture(args, settings: TrackerSettings) -> int:
    """Take the screenshots without doing anything else."""
    week = _resolve_week(args)
    print(f"Week {week.label}")
    result = capture_all(
        week, settings.screenshot_dir, settings.session_file,
        plan=load_plan(settings.capture_plan),
        headless=settings.capture_headless and not args.headed,
        only=args.only.split(",") if args.only else None,
    )
    print(f"\n{len(result.saved)} screen(s) saved to {settings.screenshot_dir}")
    for name, why in result.failed:
        print(f"  FAILED {name}: {why}", file=sys.stderr)
    return 1 if result.failed and not result.saved else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="folqs_tracker",
        description="Weekly TikTok Shop performance tracking for the Folqs wiki.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Read screenshots, update the tracker, send the digest")
    run.add_argument("--week", help="Week label, e.g. '21/08-27/08' (default: last complete week)")
    run.add_argument("--week-ending", help="Any date YYYY-MM-DD inside the week to report")
    run.add_argument("--year", type=int, help="Year for --week (default: this year)")
    run.add_argument("--set", action="append", default=[], metavar="FIELD=VALUE",
                     help="Set a metric by hand, e.g. --set retainer_payments=2050")
    run.add_argument("--samples-sent", type=int, help="Override the sample count")
    run.add_argument("--no-samples", action="store_true", help="Skip the sample tracker lookup")
    run.add_argument("--no-extract", action="store_true", help="Skip Claude; use --set only")
    run.add_argument("--no-sheet", action="store_true", help="Do not touch the Google Sheet")
    run.add_argument("--no-notify", action="store_true", help="Do not send email or Telegram")
    run.add_argument("--dry-run", action="store_true",
                     help="Read and report, but write nothing and keep the screenshots")
    run.add_argument("--overwrite", action="store_true",
                     help="Replace existing cell values instead of keeping them")
    run.add_argument("--keep-screenshots", action="store_true",
                     help="Leave the inbox alone instead of archiving what was read")
    run.add_argument("--print-report", action="store_true", help="Print the digest to stdout")
    run.add_argument("--capture", action="store_true",
                     help="Take the screenshots first, instead of using the inbox")
    run.add_argument("--headed", action="store_true",
                     help="Show the browser window while capturing")
    run.set_defaults(func=cmd_run)

    login = sub.add_parser("login", help="Log in to Seller Center once and save the session")
    login.set_defaults(func=cmd_login)

    cal = sub.add_parser("calibrate", help="Record the real Seller Center URLs for your account")
    cal.set_defaults(func=cmd_calibrate)

    cap = sub.add_parser("capture", help="Take this week's screenshots and stop")
    cap.add_argument("--week", help="Week label, e.g. '21/08-27/08'")
    cap.add_argument("--week-ending", help="Any date YYYY-MM-DD inside the week")
    cap.add_argument("--year", type=int)
    cap.add_argument("--only", help="Comma-separated target keys, e.g. samples,ads")
    cap.add_argument("--headed", action="store_true", help="Show the browser window")
    cap.set_defaults(func=cmd_capture)

    check = sub.add_parser("check", help="Validate config, credentials and tab layout")
    check.set_defaults(func=cmd_check)

    notify = sub.add_parser("notify-test", help="Send a sample digest to prove delivery works")
    notify.set_defaults(func=cmd_notify_test)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = TrackerSettings.load()
    try:
        return args.func(args, settings)
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 130
    except SessionExpired as exc:
        print(f"\nTikTok login needed: {exc}", file=sys.stderr)
        return 2
    except CaptureError as exc:
        print(f"capture error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        if __import__("os").getenv("TRACKER_DEBUG"):
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

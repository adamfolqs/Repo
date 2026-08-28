"""Command line entry point.

    python -m tiktok_scraper creators --input data/input/creators.csv
    python -m tiktok_scraper search   --query "colostrum" --limit 50
    python -m tiktok_scraper creators --handles nasa,bbc --sink both
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from .config import Settings
from .inputs import normalize_handle, read_handles
from .models import CREATOR_COLUMNS, VIDEO_COLUMNS, Creator, Video
from .providers.base import BlockedError, ProviderError, get_provider
from .sinks.files import write_csv, write_xlsx


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _emit(records, columns, label: str, settings: Settings, args) -> None:
    """Write one record set to every sink the user asked for."""
    if not records:
        print(f"  [{label}] nothing to write")
        return

    out = Path(args.output_dir or settings.output_dir)

    if args.sink in ("files", "both"):
        base = out / f"{label}_{_stamp()}"
        csv_path = write_csv(records, columns, base.with_suffix(".csv"))
        xlsx_path = write_xlsx(records, columns, base.with_suffix(".xlsx"), label.title())
        print(f"  [{label}] wrote {len(records)} rows -> {csv_path}")
        print(f"  [{label}] wrote {len(records)} rows -> {xlsx_path}")

    if args.sink in ("sheets", "both"):
        sheet_id = args.sheet_id or settings.google_sheet_id
        if not sheet_id:
            print(
                f"  [{label}] SKIPPED Google Sheets: no GOOGLE_SHEET_ID set "
                "(files were still written)",
                file=sys.stderr,
            )
            return
        try:
            from .sinks.sheets import SheetsSink
            sink = SheetsSink(settings.google_service_account_json, sheet_id)
            count = sink.write(records, columns, worksheet_name=label.title(),
                               mode=args.sheet_mode)
            print(f"  [{label}] appended {count} rows to Google Sheet tab '{label.title()}'")
        except Exception as exc:
            print(f"  [{label}] Google Sheets write FAILED: {exc}", file=sys.stderr)
            if args.sink == "both":
                print("  [{}] local files above are still valid".format(label), file=sys.stderr)
            else:
                raise


def _resolve_handles(args) -> list[str]:
    handles: list[str] = []
    if args.input:
        handles.extend(read_handles(args.input, args.column))
    if args.handles:
        for raw in args.handles.split(","):
            handle = normalize_handle(raw)
            if handle:
                handles.append(handle)
    seen, ordered = set(), []
    for handle in handles:
        if handle.lower() not in seen:
            seen.add(handle.lower())
            ordered.append(handle)
    return ordered


def cmd_creators(args, settings: Settings) -> int:
    handles = _resolve_handles(args)
    if not handles:
        print("No handles found. Pass --input <sheet> or --handles a,b,c", file=sys.stderr)
        return 2

    print(f"Provider: {settings.provider} | {len(handles)} creator(s), "
          f"up to {args.limit} videos each")

    provider = get_provider(settings.provider,
                            delay_seconds=settings.request_delay_seconds,
                            api_token=settings.brightdata_token,
                            headless=not args.headed)
    creators: list[Creator] = []
    videos: list[Video] = []
    failures: list[tuple[str, str]] = []

    try:
        for i, handle in enumerate(handles, 1):
            print(f"[{i}/{len(handles)}] @{handle}")
            try:
                if not args.videos_only:
                    creators.append(provider.fetch_creator(handle))
                if not args.profiles_only:
                    got = provider.fetch_creator_videos(handle, limit=args.limit)
                    videos.extend(got)
                    print(f"    {len(got)} videos")
            except BlockedError as exc:
                # Blocking is terminal: every later request fails the same way.
                print(f"    BLOCKED: {exc}", file=sys.stderr)
                failures.append((handle, "blocked"))
                break
            except ProviderError as exc:
                print(f"    skipped: {exc}", file=sys.stderr)
                failures.append((handle, str(exc)[:80]))
    finally:
        provider.close()

    _emit(creators, CREATOR_COLUMNS, "creators", settings, args)
    _emit(videos, VIDEO_COLUMNS, "videos", settings, args)

    if failures:
        print(f"\n{len(failures)} handle(s) failed:", file=sys.stderr)
        for handle, why in failures:
            print(f"  @{handle}: {why}", file=sys.stderr)
    return 1 if failures and not (creators or videos) else 0


def cmd_search(args, settings: Settings) -> int:
    queries = [q.strip() for q in args.query.split(",") if q.strip()]
    print(f"Provider: {settings.provider} | {len(queries)} query(ies)")

    provider = get_provider(settings.provider,
                            delay_seconds=settings.request_delay_seconds,
                            api_token=settings.brightdata_token,
                            headless=not args.headed)
    videos: list[Video] = []
    try:
        for query in queries:
            print(f"  searching {query!r}")
            try:
                found = provider.search_videos(query, limit=args.limit)
                videos.extend(found)
                print(f"    {len(found)} videos")
            except NotImplementedError as exc:
                print(f"    {exc}", file=sys.stderr)
                return 2
            except ProviderError as exc:
                print(f"    failed: {exc}", file=sys.stderr)
    finally:
        provider.close()

    _emit(videos, VIDEO_COLUMNS, "videos", settings, args)
    return 0


def _read_links(path: str) -> list[str]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("#")]


def cmd_shop(args, settings: Settings) -> int:
    """Pull creator videos off TikTok Shop product pages."""
    from .providers.shop import ShopProductProvider

    urls = _read_links(args.links) if args.links else []
    if args.url:
        urls.extend(u.strip() for u in args.url.split(",") if u.strip())
    if not urls:
        print("No product links. Pass --links <file> or --url <url>", file=sys.stderr)
        return 2

    print(f"{len(urls)} product page(s)")
    provider = ShopProductProvider(
        delay_seconds=settings.request_delay_seconds, headless=not args.headed
    )

    videos: list[Video] = []
    try:
        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] {url[:70]}")
            try:
                found = provider.fetch_product_videos(
                    url, limit=args.limit,
                    dump_dir=(args.dump_raw and Path(args.dump_raw)) or None,
                )
                videos.extend(found)
                creators = len({v.handle for v in found})
                print(f"    {len(found)} videos from {creators} creators")
            except BlockedError as exc:
                print(f"    BLOCKED: {exc}", file=sys.stderr)
                break
            except ProviderError as exc:
                print(f"    skipped: {exc}", file=sys.stderr)
    finally:
        provider.close()

    if videos:
        handles = sorted({v.handle for v in videos})
        print(f"\n{len(videos)} videos, {len(handles)} unique creators")

    _emit(videos, VIDEO_COLUMNS, "videos", settings, args)

    # The handles are the point of this command -- they feed the next step.
    if videos and args.handles_out:
        out = Path(args.handles_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("handle\n" + "\n".join(sorted({v.handle for v in videos})) + "\n")
        print(f"  [handles] wrote {len(set(v.handle for v in videos))} handles -> {out}")

    return 0 if videos else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tiktok_scraper",
        description="Scrape TikTok videos + creators into a spreadsheet.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p):
        p.add_argument("--limit", type=int, default=30,
                       help="Max videos per creator/query (default 30)")
        p.add_argument("--sink", choices=["files", "sheets", "both"], default="files",
                       help="Where results go (default files)")
        p.add_argument("--sheet-id", help="Google Sheet ID; overrides GOOGLE_SHEET_ID")
        p.add_argument("--sheet-mode", choices=["append", "replace"], default="append")
        p.add_argument("--output-dir", help="Directory for csv/xlsx (default data/output)")
        p.add_argument("--provider", choices=["playwright", "brightdata"],
                       help="Override TIKTOK_PROVIDER for this run")
        p.add_argument("--headed", action="store_true",
                       help="Show the browser window (playwright only; useful for debugging)")

    creators = sub.add_parser("creators", help="Scrape specific creators by handle")
    creators.add_argument("--input", help="CSV/XLSX to read handles from")
    creators.add_argument("--column", help="Which column holds the handle (auto-detected otherwise)")
    creators.add_argument("--handles", help="Comma-separated handles, e.g. nasa,bbc")
    creators.add_argument("--profiles-only", action="store_true")
    creators.add_argument("--videos-only", action="store_true")
    common(creators)
    creators.set_defaults(func=cmd_creators)

    search = sub.add_parser("search", help="Discover videos by keyword or #hashtag")
    search.add_argument("--query", required=True, help="Comma-separated keywords/hashtags")
    common(search)
    search.set_defaults(func=cmd_search)

    shop = sub.add_parser(
        "shop", help="Pull creator videos from TikTok Shop product pages"
    )
    shop.add_argument("--links", help="Text file of product URLs, one per line")
    shop.add_argument("--url", help="Comma-separated product URLs")
    shop.add_argument("--handles-out", default="data/output/handles.csv",
                      help="Also write the unique creator handles here")
    shop.add_argument("--dump-raw", help="Directory to save raw intercepted JSON (for debugging)")
    common(shop)
    shop.set_defaults(func=cmd_shop)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = Settings.load()
    if getattr(args, "provider", None):
        settings.provider = args.provider
    try:
        return args.func(args, settings)
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 130
    except (ProviderError, ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

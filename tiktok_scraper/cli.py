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
from .enrich import enrich_creators, enrich_videos, filter_videos
from .inputs import normalize_handle, read_handles
from . import store
from .models import CREATOR_COLUMNS, VIDEO_COLUMNS, Creator, Video
from .providers.base import BlockedError, ProviderError, get_provider
from .sinks.files import write_csv, write_xlsx


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _prepare(videos, creators, args):
    """Enrich then filter, so every sink sees the same finished rows."""
    enrich_creators(creators)
    enrich_videos(videos, creators)
    before = len(videos)
    videos = filter_videos(
        videos,
        min_likes=getattr(args, "min_likes", 0),
        colostrum_only=getattr(args, "colostrum_only", False),
        product_only=getattr(args, "product_only", False),
        language=getattr(args, "language", None),
    )
    if before != len(videos):
        print(f"  filtered {before} -> {len(videos)} videos")
    return videos, creators


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

    videos, creators = _prepare(videos, creators, args)
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

    videos, _ = _prepare(videos, [], args)
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

    videos, _ = _prepare(videos, [], args)
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


def _read_lines(path: str) -> list[str]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("#")]


def cmd_discover(args, settings: Settings) -> int:
    """Stage 1: turn keywords into video URLs, via /discover/ landing pages.

    Writes URLs to a file rather than resolving them here, because discovery
    needs a browser and resolution does not -- keeping them apart means the
    slow browser stage runs once and the cheap stage can be re-run freely.
    """
    from .providers.discover import DiscoverProvider

    keywords = [k.strip() for k in (args.keywords or "").split(",") if k.strip()]
    if args.keyword_file:
        keywords.extend(_read_lines(args.keyword_file))
    if not keywords:
        print("No keywords. Pass --keywords a,b or --keyword-file <file>", file=sys.stderr)
        return 2

    out = Path(args.urls_out)
    known: dict[str, str] = {}
    if out.exists():
        for handle, video_id in _read_url_rows(out):
            known[video_id] = handle
    print(f"{len(keywords)} keyword(s); {len(known)} URL(s) already on file")

    provider = DiscoverProvider(
        delay_seconds=settings.request_delay_seconds, headless=not args.headed
    )
    added_total = 0
    # Worklist rather than a plain loop: a discover page links to related
    # keyword pages, and following the on-topic ones is where most of the
    # breadth comes from -- a single grid stops at ~60 videos however hard you
    # scroll it, so more keywords beats more scrolling.
    from .providers.discover import slugify

    queue = [(k, 0) for k in keywords]
    seen_slugs: set[str] = set()
    index = 0
    try:
        while index < len(queue):
            keyword, depth = queue[index]
            index += 1
            slug = slugify(keyword)
            if not slug or slug in seen_slugs:
                continue
            seen_slugs.add(slug)

            try:
                pairs, related = provider.fetch_discover_page(
                    keyword, limit=args.per_keyword
                )
            except BlockedError as exc:
                print(f"[{index}/{len(queue)}] {keyword!r} BLOCKED: {exc}", file=sys.stderr)
                break
            except ProviderError as exc:
                print(f"[{index}/{len(queue)}] {keyword!r} failed: {exc}", file=sys.stderr)
                continue

            added = 0
            for handle, video_id in pairs:
                if video_id not in known:
                    known[video_id] = handle
                    added += 1
            added_total += added

            queued = 0
            if depth < args.crawl_depth:
                for candidate in related:
                    if candidate not in seen_slugs:
                        queue.append((candidate, depth + 1))
                        queued += 1

            print(f"[{index}/{len(queue)}] {keyword!r} (d{depth}): {len(pairs)} found, "
                  f"{added} new, +{queued} related (total {len(known)})", flush=True)
            _write_urls(out, known)
    finally:
        provider.close()

    _write_urls(out, known)
    print(f"\n{len(known)} unique video URLs ({added_total} new this run) -> {out}")
    return 0


def _read_url_rows(path) -> list[tuple[str, str]]:
    """(handle, video_id) rows from the discovered-URL file.

    Skips the header and any row whose id is not a TikTok video id, so a
    malformed line can never be re-fetched as if it were a video.
    """
    rows = []
    for line in _read_lines(str(path)):
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 2 and parts[1].isdigit() and len(parts[1]) >= 15:
            rows.append((parts[0], parts[1]))
    return rows


def _write_urls(path: Path, known: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = ["handle,video_id"]
    rows += [f"{handle},{video_id}" for video_id, handle in known.items()]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def cmd_resolve(args, settings: Settings) -> int:
    """Stage 2: turn video URLs into full rows, reading each video's own page.

    Every number here is the one TikTok served for that video. Anything that
    cannot be resolved is recorded as a failure and left out, never estimated.
    """
    from .providers.http_ssr import HttpSSRProvider

    pairs = _read_url_rows(args.urls)

    already = store.done_keys(args.store, "video_id")
    todo = [(h, v) for h, v in pairs if v not in already]
    print(f"{len(pairs)} URLs on file, {len(already)} already resolved, "
          f"{len(todo)} to fetch")
    if args.max_items:
        todo = todo[: args.max_items]
        print(f"  limited to {len(todo)} this run")

    provider = HttpSSRProvider(delay_seconds=settings.request_delay_seconds)
    ok = fail = 0
    try:
        for i, (handle, video_id) in enumerate(todo, 1):
            url = f"https://www.tiktok.com/@{handle}/video/{video_id}"
            try:
                video = provider.fetch_video(url, matched_query=args.matched_query)
                store.append(args.store, [video])
                ok += 1
            except BlockedError as exc:
                print(f"  BLOCKED after {ok} ok: {exc}", file=sys.stderr)
                break
            except ProviderError as exc:
                fail += 1
                print(f"  [{i}] @{handle}/{video_id}: {exc}", file=sys.stderr)
            if i % 25 == 0:
                print(f"  [{i}/{len(todo)}] {ok} resolved, {fail} unavailable", flush=True)
    finally:
        provider.close()

    print(f"\n{ok} resolved, {fail} unavailable -> {args.store}")
    return 0


def cmd_profiles(args, settings: Settings) -> int:
    """Stage 3: follower count and bio (hence contact email) per creator."""
    from .providers.http_ssr import HttpSSRProvider

    handles: list[str] = []
    if args.from_store:
        handles = sorted({
            record["handle"] for record in store.read(args.from_store)
            if record.get("handle")
        })
    handles.extend(_resolve_handles(args))

    seen, ordered = set(), []
    for handle in handles:
        if handle.lower() not in seen:
            seen.add(handle.lower())
            ordered.append(handle)

    already = {h.lower() for h in store.done_keys(args.store, "handle")}
    todo = [h for h in ordered if h.lower() not in already]
    print(f"{len(ordered)} creators, {len(already)} already done, {len(todo)} to fetch")
    if args.max_items:
        todo = todo[: args.max_items]

    provider = HttpSSRProvider(delay_seconds=settings.request_delay_seconds)
    ok = fail = 0
    try:
        for i, handle in enumerate(todo, 1):
            try:
                creator = provider.fetch_creator(handle)
                store.append(args.store, [creator])
                ok += 1
            except BlockedError as exc:
                print(f"  BLOCKED after {ok} ok: {exc}", file=sys.stderr)
                break
            except ProviderError as exc:
                fail += 1
                print(f"  [{i}] @{handle}: {exc}", file=sys.stderr)
            if i % 25 == 0:
                print(f"  [{i}/{len(todo)}] {ok} ok, {fail} failed", flush=True)
    finally:
        provider.close()

    print(f"\n{ok} profiles, {fail} failed -> {args.store}")
    return 0


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
        p.add_argument("--min-likes", type=int, default=0,
                       help="Drop videos below this like count (e.g. 50)")
        p.add_argument("--colostrum-only", action="store_true",
                       help="Keep only videos about colostrum (EN + ES terms)")
        p.add_argument("--product-only", action="store_true",
                       help="Keep only videos that tag/sell a product")
        p.add_argument("--language", choices=["English", "Spanish"],
                       help="Keep only videos in this language")

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

    discover = sub.add_parser(
        "discover",
        help="Source video URLs from /discover/ keyword pages (needs a browser)",
    )
    discover.add_argument("--keywords", help="Comma-separated keywords")
    discover.add_argument("--keyword-file", help="File of keywords, one per line")
    discover.add_argument("--per-keyword", type=int, default=120,
                          help="Max video URLs per keyword (default 120)")
    discover.add_argument("--urls-out", default="data/output/discovered_urls.csv",
                          help="Where the deduped handle,video_id list accumulates")
    discover.add_argument("--crawl-depth", type=int, default=0,
                          help="Follow on-topic related keyword pages this many "
                               "hops deep (default 0, i.e. seed keywords only)")
    common(discover)
    discover.set_defaults(func=cmd_discover)

    resolve = sub.add_parser(
        "resolve",
        help="Fetch each discovered video's real stats from its own page",
    )
    resolve.add_argument("--urls", default="data/output/discovered_urls.csv")
    resolve.add_argument("--store", default="data/output/videos.jsonl",
                         help="Append-only store; a re-run skips what it holds")
    resolve.add_argument("--matched-query", help="Attribution tag for this batch")
    resolve.add_argument("--max-items", type=int, help="Stop after N this run")
    common(resolve)
    resolve.set_defaults(func=cmd_resolve)

    profiles = sub.add_parser(
        "profiles", help="Follower count + bio email for each creator"
    )
    profiles.add_argument("--from-store", default="data/output/videos.jsonl",
                          help="Take the handle list from this video store")
    profiles.add_argument("--input", help="CSV/XLSX to read extra handles from")
    profiles.add_argument("--column", help="Which column holds the handle")
    profiles.add_argument("--handles", help="Comma-separated extra handles")
    profiles.add_argument("--store", default="data/output/creators.jsonl")
    profiles.add_argument("--max-items", type=int, help="Stop after N this run")
    common(profiles)
    profiles.set_defaults(func=cmd_profiles)

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

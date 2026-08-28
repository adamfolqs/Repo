"""Read the creator videos listed on a TikTok Shop product page.

Why this exists: sourcing creators by *display name* is unreliable -- names are
not unique on TikTok and OCR'd names are often wrong or truncated. A Shop
product page ("popular videos" / creator content section) lists the real
creators for that exact product, so we get canonical @handles and video ids
instead of guessing.

shop.tiktok.com is noticeably less defended than the main site -- it serves
product pages without a captcha wall. But the video section is rendered
client-side, so a real browser is required; plain HTTP returns the shell only.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Iterable

from ..models import Video
from .base import BlockedError, ProviderError
from .playwright_provider import _CAPTCHA_MARKERS, UA, PlaywrightProvider, _int, _ts

# Short share links (tiktok.com/t/XXXX) and full PDP urls both appear in the
# wild; normalize to a product id.
_PDP_ID_RE = re.compile(r"/pdp/(\d+)")
_SHORT_RE = re.compile(r"tiktok\.com/t/([A-Za-z0-9_-]+)")

# The XHRs that carry creator content on a PDP. TikTok renames these
# occasionally, so match loosely and filter on payload shape instead.
_VIDEO_XHR_HINTS = ("video", "content", "review", "showcase", "feed")


class ShopProductProvider(PlaywrightProvider):
    """Scrapes creator videos off TikTok Shop product pages."""

    name = "shop"

    def resolve_product_url(self, url: str) -> str:
        """Follow a short share link to its canonical PDP url."""
        if _PDP_ID_RE.search(url):
            return url
        if not _SHORT_RE.search(url):
            return url

        page = self._ctx.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45_000)
            time.sleep(1.5)
            return page.url
        finally:
            page.close()

    def fetch_product_videos(
        self,
        url: str,
        limit: int = 60,
        dump_dir: str | Path | None = None,
    ) -> list[Video]:
        """Every creator video listed on one product page.

        dump_dir: if set, raw intercepted JSON is written there. TikTok's
        internal payload shapes change; having the raw capture makes a broken
        run diagnosable without re-scraping.
        """
        final_url = self.resolve_product_url(url)
        product_id_match = _PDP_ID_RE.search(final_url)
        product_id = product_id_match.group(1) if product_id_match else None

        captured: list[dict] = []
        raw_payloads: list[dict] = []

        page = self._ctx.new_page()

        def on_response(resp):
            target = resp.url.lower()
            if not any(hint in target for hint in _VIDEO_XHR_HINTS):
                return
            try:
                payload = resp.json()
            except Exception:
                return
            raw_payloads.append({"url": resp.url, "body": payload})
            captured.extend(_harvest_videos(payload))

        page.on("response", on_response)
        try:
            page.goto(final_url, wait_until="domcontentloaded", timeout=60_000)
            time.sleep(self._delay)

            html = page.content()
            # Reuse the shared narrow marker set: matching a bare "/captcha/"
            # here reported a wall on every product page, because the captcha
            # SDK's asset URL is bundled into all of them.
            if any(marker in html for marker in _CAPTCHA_MARKERS):
                raise BlockedError(
                    "TikTok Shop served a captcha. Wait a few minutes, or run "
                    "with --headed and solve it once."
                )

            # The creator section is well down the page and lazy-loads.
            stalls = 0
            while len(captured) < limit and stalls < 4:
                before = len(captured)
                page.mouse.wheel(0, 3000)
                time.sleep(self._delay)
                stalls = stalls + 1 if len(captured) == before else 0
        finally:
            page.close()

        if dump_dir:
            dump_path = Path(dump_dir)
            dump_path.mkdir(parents=True, exist_ok=True)
            target = dump_path / f"raw_{product_id or 'unknown'}.json"
            target.write_text(json.dumps(raw_payloads, indent=2)[:5_000_000])

        videos, seen = [], set()
        for item in captured:
            video = _to_video(item, product_id)
            if video and video.video_id not in seen:
                seen.add(video.video_id)
                videos.append(video)
        return videos[:limit]


def _harvest_videos(payload: Any, depth: int = 0) -> list[dict]:
    """Walk an arbitrary JSON payload and collect anything video-shaped.

    Written structurally rather than against fixed key paths, so a TikTok
    response reshuffle degrades into fewer results instead of a hard crash.
    """
    found: list[dict] = []
    if depth > 8:
        return found

    if isinstance(payload, dict):
        looks_like_video = (
            any(k in payload for k in ("video_id", "item_id", "aweme_id", "id"))
            and any(k in payload for k in ("author", "creator", "statistics", "stats", "desc", "title"))
        )
        if looks_like_video:
            found.append(payload)
        for value in payload.values():
            found.extend(_harvest_videos(value, depth + 1))
    elif isinstance(payload, list):
        for value in payload:
            found.extend(_harvest_videos(value, depth + 1))
    return found


def _to_video(item: dict, product_id: str | None) -> Video | None:
    video_id = str(
        item.get("video_id") or item.get("aweme_id") or item.get("item_id") or item.get("id") or ""
    )
    if not video_id.isdigit() or len(video_id) < 15:
        return None  # not a real TikTok video id

    author = item.get("author") or item.get("creator") or {}
    if isinstance(author, str):
        author = {"unique_id": author}
    handle = str(
        author.get("unique_id") or author.get("uniqueId")
        or author.get("nickname") or author.get("handle") or ""
    ).lstrip("@")
    if not handle:
        return None

    stats = item.get("statistics") or item.get("stats") or {}
    return Video(
        video_id=video_id,
        handle=handle,
        description=item.get("desc") or item.get("title") or item.get("description"),
        created_at=_ts(item.get("create_time") or item.get("createTime")),
        views=_int(stats.get("play_count") or stats.get("playCount")),
        likes=_int(stats.get("digg_count") or stats.get("diggCount") or item.get("like_count")),
        comments=_int(stats.get("comment_count") or stats.get("commentCount")),
        shares=_int(stats.get("share_count") or stats.get("shareCount")),
        matched_query=f"product:{product_id}" if product_id else None,
        source="shop",
    )

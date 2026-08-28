"""Source video URLs from TikTok's keyword landing pages.

`/search?q=` is login-walled for logged-out users -- the grid renders as
skeleton placeholders and the results XHR is never issued. `/tag/<hashtag>`
gives nothing either. But `/discover/<keyword>` still renders a real video
grid, and it is the one keyword-driven surface that does.

So discovery is: ask a discover page for its grid, scroll it, and read the
`<a href=".../@handle/video/id">` anchors. That yields URLs and handles only --
the grid carries no engagement numbers. Those come from HttpSSRProvider,
which reads each video's own page. Splitting it that way is deliberate:
nothing here has to estimate a like count, and a video we cannot resolve ends
up with empty cells rather than invented ones.
"""

from __future__ import annotations

import re
import time

from .base import BlockedError, ProviderError
from .playwright_provider import _CAPTCHA_MARKERS, PlaywrightProvider

_VIDEO_HREF_RE = re.compile(r"/@([A-Za-z0-9_.-]+)/video/(\d{15,})")

# TikTok slugifies discover keywords: spaces and '#' become hyphens.
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(keyword: str) -> str:
    return _SLUG_RE.sub("-", keyword.strip().lower().lstrip("#")).strip("-")


class DiscoverProvider(PlaywrightProvider):
    """Harvests (handle, video_id) pairs off /discover/<keyword> pages."""

    name = "discover"

    def fetch_discover_urls(
        self, keyword: str, limit: int = 120, max_scrolls: int = 25
    ) -> list[tuple[str, str]]:
        """Unique (handle, video_id) pairs for one keyword, newest grid first."""
        slug = slugify(keyword)
        if not slug:
            return []

        page = self._ctx.new_page()
        found: dict[str, str] = {}   # video_id -> handle, dedupes as we scroll
        try:
            page.goto(
                f"https://www.tiktok.com/discover/{slug}",
                wait_until="domcontentloaded",
                timeout=60_000,
            )
            time.sleep(self._delay)

            html = page.content()
            if any(marker in html for marker in _CAPTCHA_MARKERS):
                raise BlockedError(
                    f"captcha wall on /discover/{slug} — back off and retry later"
                )

            stalls = 0
            for _ in range(max_scrolls):
                for handle, video_id in _VIDEO_HREF_RE.findall(page.content()):
                    found.setdefault(video_id, handle)
                if len(found) >= limit:
                    break
                before = len(found)
                page.mouse.wheel(0, 4000)
                time.sleep(self._delay)
                # Two dry scrolls in a row means the grid is exhausted; a
                # single one just means that batch had no new ids yet.
                stalls = stalls + 1 if len(found) == before else 0
                if stalls >= 3:
                    break
        finally:
            page.close()

        return [(handle, vid) for vid, handle in list(found.items())[:limit]]

    def fetch_creator(self, handle: str):
        raise NotImplementedError("discover provider only sources video URLs")

    def fetch_creator_videos(self, handle: str, limit: int = 30):
        raise NotImplementedError("discover provider only sources video URLs")

"""Read TikTok's server-rendered page data over plain HTTP.

Every TikTok page ships a `__UNIVERSAL_DATA_FOR_REHYDRATION__` <script> blob.
For profile pages and video pages that blob contains the real record --
follower counts, and exact like/view/comment/share/save numbers -- with no
signed request params and no browser.

Which pages actually serve it (measured, not assumed):

| Page                | SSR blob | Notes                                    |
|---------------------|----------|------------------------------------------|
| `/@handle`          | yes      | profile + stats                          |
| `/@handle/video/id` | yes      | full stats, hashtags, product anchors    |
| `/search?q=`        | no       | login-walled, renders skeletons only     |
| `/tag/<hashtag>`    | no       | client-rendered                          |
| `/discover/<word>`  | no       | client-rendered -- see discover.py       |

So this module is the *enrichment* half: something else finds video URLs, and
this turns each one into a fully populated row. It is much faster than driving
a browser, which matters when there are hundreds of URLs to resolve.
"""

from __future__ import annotations

import json
import re
import time
from typing import Optional

import httpx

from ..models import Creator, Video
from .base import BlockedError, Provider, ProviderError
from .playwright_provider import UA, _CAPTCHA_MARKERS, _int, _ts

_REHYDRATION_RE = re.compile(
    r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>',
    re.DOTALL,
)

# https://www.tiktok.com/@handle/video/1234  ->  (handle, id)
VIDEO_URL_RE = re.compile(r"tiktok\.com/@([A-Za-z0-9_.-]+)/video/(\d{15,})")


def parse_video_url(url: str) -> Optional[tuple[str, str]]:
    """(handle, video_id) from a canonical video URL, or None."""
    match = VIDEO_URL_RE.search(url or "")
    return (match.group(1), match.group(2)) if match else None


class HttpSSRProvider(Provider):
    """Fetches profile and video records straight out of the page's SSR blob."""

    name = "http_ssr"

    def __init__(self, delay_seconds: float = 2.5, retries: int = 2, **_):
        self._delay = delay_seconds
        self._retries = retries
        self._client = httpx.Client(
            headers={
                "User-Agent": UA,
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            follow_redirects=True,
            timeout=45.0,
        )
        self._last_request = 0.0

    # ---------------------------------------------------------------- helpers

    def _get(self, url: str) -> str:
        # Self-throttle: callers loop over hundreds of URLs, and the delay has
        # to hold across every one of them, not per call site.
        wait = self._delay - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        try:
            response = self._client.get(url)
        except httpx.HTTPError as exc:
            raise ProviderError(f"request failed: {exc}") from exc
        finally:
            self._last_request = time.monotonic()

        if response.status_code == 404:
            raise ProviderError("404 — deleted or never existed")
        if not response.text:
            # A 200 with an empty body is TikTok's quiet way of refusing.
            raise BlockedError("empty body — this IP looks rate-limited")
        return response.text

    def _scope(self, html: str) -> dict:
        match = _REHYDRATION_RE.search(html)
        if not match:
            if any(marker in html for marker in _CAPTCHA_MARKERS):
                raise BlockedError("captcha wall instead of page data")
            return {}
        try:
            return json.loads(match.group(1)).get("__DEFAULT_SCOPE__", {})
        except json.JSONDecodeError:
            return {}

    # ---------------------------------------------------------------- fetching

    def fetch_creator(self, handle: str) -> Creator:
        handle = handle.lstrip("@")
        html = self._get(f"https://www.tiktok.com/@{handle}")
        info = self._scope(html).get("webapp.user-detail", {}).get("userInfo", {})
        if not info:
            raise ProviderError(
                f"no profile data for @{handle} — private, banned, or renamed"
            )

        user = info.get("user", {}) or {}
        stats = info.get("stats", {}) or info.get("statsV2", {}) or {}
        return Creator(
            handle=user.get("uniqueId") or handle,
            user_id=user.get("id"),
            nickname=user.get("nickname"),
            bio=user.get("signature"),
            verified=user.get("verified"),
            followers=_int(stats.get("followerCount")),
            following=_int(stats.get("followingCount")),
            total_likes=_int(stats.get("heartCount") or stats.get("heart")),
            video_count=_int(stats.get("videoCount")),
            avatar_url=user.get("avatarLarger"),
            bio_link=(user.get("bioLink") or {}).get("link"),
            region=user.get("region"),
            source=self.name,
        )

    def fetch_video(self, url: str, matched_query: str | None = None) -> Video:
        """One video URL -> a fully populated row, with real numbers only."""
        parsed = parse_video_url(url)
        if not parsed:
            raise ProviderError(f"not a TikTok video URL: {url!r}")
        handle, video_id = parsed

        # TikTok intermittently serves a page whose SSR blob is missing the
        # video record entirely. It is transient -- the same URL resolves on a
        # retry -- so retrying here is the difference between a real row and a
        # blank one. Measured at roughly one page in five on a first pass.
        detail: dict = {}
        for attempt in range(self._retries + 1):
            detail = self._scope(self._get(url)).get("webapp.video-detail") or {}
            if detail:
                break
            if attempt < self._retries:
                time.sleep(self._delay * (attempt + 1))
        if not detail:
            raise ProviderError("no video-detail in page after retries")
        if detail.get("statusCode"):
            raise ProviderError(
                f"unavailable ({detail.get('statusCode')}): "
                f"{detail.get('statusMsg') or 'removed or private'}"
            )

        item = (detail.get("itemInfo") or {}).get("itemStruct") or {}
        if not item:
            raise ProviderError("empty itemStruct")
        return self._to_video(item, handle, video_id, matched_query)

    def _to_video(
        self, item: dict, handle: str, video_id: str, matched_query: str | None
    ) -> Video:
        stats = item.get("statsV2") or item.get("stats") or {}
        music = item.get("music") or {}
        author = item.get("author") or {}

        # Captions live in item["desc"], but a video with several text segments
        # keeps them in contents[]; concatenate so hashtags in later segments
        # still count towards brand/product matching.
        parts = [item.get("desc") or ""]
        for content in item.get("contents") or []:
            text = content.get("desc")
            if text and text not in parts:
                parts.append(text)
        description = " ".join(p for p in parts if p).strip() or None

        hashtags = []
        for extra in item.get("textExtra") or []:
            tag = extra.get("hashtagName")
            if tag and tag not in hashtags:
                hashtags.append(tag)
        for content in item.get("contents") or []:
            for extra in content.get("textExtra") or []:
                tag = extra.get("hashtagName")
                if tag and tag not in hashtags:
                    hashtags.append(tag)

        return Video(
            video_id=video_id,
            handle=author.get("uniqueId") or handle,
            description=description,
            created_at=_ts(item.get("createTime")),
            duration_seconds=_int((item.get("video") or {}).get("duration")),
            views=_int(stats.get("playCount")),
            likes=_int(stats.get("diggCount")),
            comments=_int(stats.get("commentCount")),
            shares=_int(stats.get("shareCount")),
            saves=_int(stats.get("collectCount")),
            hashtags=hashtags,
            music_title=music.get("title"),
            music_author=music.get("authorName"),
            cover_url=(item.get("video") or {}).get("cover"),
            has_product_tag=_has_commerce_anchor(item) or None,
            matched_query=matched_query,
            source=self.name,
        )

    def fetch_creator_video_ids(self, handle: str, limit: int = 10) -> list[str]:
        """Recent video ids for one creator, from their oEmbed profile page.

        The profile page's own grid is login-walled and `/api/post/item_list/`
        needs signed params, but `/embed/@handle` is built to be rendered by
        logged-out third parties and ships a `videoList` in its state blob.

        It holds the 10 most recent posts and does not paginate, so this is a
        recent-catalogue sample, not a creator's full history -- enough to find
        the other colostrum posts of someone who posts about it regularly.
        """
        handle = handle.lstrip("@")
        html = self._get(f"https://www.tiktok.com/embed/@{handle}")

        match = re.search(
            r'id="__FRONTITY_CONNECT_STATE__"[^>]*>(.*?)</script>', html, re.DOTALL
        )
        if not match:
            raise ProviderError(f"no embed state for @{handle}")
        try:
            state = json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            raise ProviderError(f"unparseable embed state for @{handle}") from exc

        data = (state.get("source") or {}).get("data") or {}
        for key, payload in data.items():
            if not isinstance(payload, dict) or "videoList" not in payload:
                continue
            ids = []
            for item in payload.get("videoList") or []:
                video_id = str(item.get("id") or "")
                # Guard against a shared/duetted post from another account
                # being read as this creator's own.
                author = (item.get("authorUniqueId") or handle).lower()
                if video_id.isdigit() and author == handle.lower():
                    ids.append(video_id)
            return ids[:limit]
        raise ProviderError(f"no videoList in embed for @{handle}")

    def fetch_creator_videos(self, handle: str, limit: int = 30) -> list[Video]:
        """Recent videos for one creator, fully resolved."""
        videos = []
        for video_id in self.fetch_creator_video_ids(handle, limit=limit):
            url = f"https://www.tiktok.com/@{handle}/video/{video_id}"
            try:
                videos.append(self.fetch_video(url, matched_query=f"catalogue:{handle}"))
            except ProviderError:
                continue
        return videos

    def close(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass


def _has_commerce_anchor(item: dict) -> bool:
    """Whether TikTok itself says this post carries a shopping tag.

    Structural, so it beats reading the caption: a video can sell a product
    without saying 'link in bio', and can say it while selling nothing. Text
    signals still run in enrich.py and are OR'd in as a fallback -- this only
    ever turns a False into a True.
    """
    if item.get("isAd"):
        return True
    for anchor in item.get("anchors") or []:
        keyword = f"{anchor.get('keyword', '')}{anchor.get('type', '')}".lower()
        if any(hint in keyword for hint in ("shop", "product", "commerce", "anchor")):
            return True
    commerce = item.get("commerceInfo") or (item.get("author") or {}).get("commerceUserInfo") or {}
    if isinstance(commerce, dict):
        if commerce.get("hasCommerceEntry") or commerce.get("commerceUser"):
            return True
        if commerce.get("adv_promotable") or commerce.get("auction_ad_invited"):
            return True
    return False

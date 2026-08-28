"""Free backend: drive a real Chromium and read what TikTok's own page loads.

Strategy: rather than reverse-engineering TikTok's signed request params
(X-Bogus / msToken, which rotate and break), we let the page make its own
authenticated XHRs and intercept the JSON responses. That survives signature
changes; it does not survive IP-reputation blocks.

Setup:  pip install playwright && playwright install chromium
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Optional

from ..models import Creator, Video
from .base import BlockedError, Provider, ProviderError

_REHYDRATION_RE = re.compile(
    r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>',
    re.DOTALL,
)
_CAPTCHA_MARKERS = ("captcha-verify", "verify-bar", "/captcha/", "Access Denied")

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


def _int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _ts(value: Any) -> Optional[datetime]:
    ts = _int(value)
    if not ts:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc)


class PlaywrightProvider(Provider):
    name = "playwright"

    def __init__(
        self,
        headless: bool = True,
        delay_seconds: float = 2.5,
        executable_path: str | None = None,
        proxy_server: str | None = None,
        **_,
    ):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "The playwright provider needs:\n"
                "    pip install playwright && playwright install chromium"
            ) from exc

        self._delay = delay_seconds
        self._pw = sync_playwright().start()
        launch_kwargs: dict = {
            "headless": headless,
            "args": ["--disable-blink-features=AutomationControlled"],
        }
        # Use a pre-installed Chromium when one is provided (some sandboxes ship
        # a browser whose build number does not match the pip-installed
        # playwright, which otherwise refuses to launch).
        chrome = executable_path or os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
        if chrome:
            launch_kwargs["executable_path"] = chrome

        # Honour an egress proxy if one is configured. Chromium ignores the
        # HTTPS_PROXY env var, so it has to be passed explicitly -- without
        # this, every navigation dies with ERR_CONNECTION_RESET in sandboxes
        # that route all outbound traffic through a proxy.
        proxy = proxy_server or os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
        if proxy:
            launch_kwargs["proxy"] = {"server": proxy}
            # The proxy terminates TLS with its own CA, so the browser must not
            # reject the resulting certificates.
            launch_kwargs["args"].append("--ignore-certificate-errors")

        self._browser = self._pw.chromium.launch(**launch_kwargs)
        self._ctx = self._browser.new_context(
            user_agent=UA,
            viewport={"width": 1280, "height": 900},
            locale="en-US",
        )
        # Hide the most-checked automation tell.
        self._ctx.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
        )

    # ---------------------------------------------------------------- helpers

    def _guard_blocked(self, html: str, handle: str) -> None:
        if any(marker in html for marker in _CAPTCHA_MARKERS):
            raise BlockedError(
                f"TikTok served a captcha wall for @{handle}. "
                "This IP is flagged. Switch to TIKTOK_PROVIDER=brightdata, "
                "or run this from a residential IP."
            )

    def _rehydration(self, html: str) -> dict:
        match = _REHYDRATION_RE.search(html)
        if not match:
            return {}
        try:
            return json.loads(match.group(1)).get("__DEFAULT_SCOPE__", {})
        except json.JSONDecodeError:
            return {}

    # ---------------------------------------------------------------- fetching

    def fetch_creator(self, handle: str) -> Creator:
        handle = handle.lstrip("@")
        page = self._ctx.new_page()
        try:
            page.goto(f"https://www.tiktok.com/@{handle}",
                      wait_until="domcontentloaded", timeout=45_000)
            time.sleep(self._delay)
            html = page.content()
        finally:
            page.close()

        self._guard_blocked(html, handle)

        info = self._rehydration(html).get("webapp.user-detail", {}).get("userInfo", {})
        if not info:
            raise ProviderError(
                f"No profile data in page for @{handle} — the account may be "
                "private, banned, or nonexistent."
            )

        user = info.get("user", {})
        stats = info.get("stats", {})
        return Creator(
            handle=user.get("uniqueId") or handle,
            user_id=user.get("id"),
            nickname=user.get("nickname"),
            bio=user.get("signature"),
            verified=user.get("verified"),
            followers=_int(stats.get("followerCount")),
            following=_int(stats.get("followingCount")),
            total_likes=_int(stats.get("heartCount")),
            video_count=_int(stats.get("videoCount")),
            avatar_url=user.get("avatarLarger"),
            bio_link=(user.get("bioLink") or {}).get("link"),
            region=user.get("region"),
            source=self.name,
        )

    def fetch_creator_videos(self, handle: str, limit: int = 30) -> list[Video]:
        handle = handle.lstrip("@")
        captured: list[dict] = []

        page = self._ctx.new_page()

        def on_response(resp):
            if "/api/post/item_list" not in resp.url:
                return
            try:
                captured.extend(resp.json().get("itemList", []) or [])
            except Exception:
                pass  # non-JSON or torn-down response; other pages may still land

        page.on("response", on_response)
        try:
            page.goto(f"https://www.tiktok.com/@{handle}",
                      wait_until="domcontentloaded", timeout=45_000)
            time.sleep(self._delay)
            self._guard_blocked(page.content(), handle)

            # Scroll to pull further pages of item_list until we have enough.
            stalls = 0
            while len(captured) < limit and stalls < 3:
                before = len(captured)
                page.mouse.wheel(0, 4000)
                time.sleep(self._delay)
                stalls = stalls + 1 if len(captured) == before else 0
        finally:
            page.close()

        return [self._to_video(item, handle) for item in captured[:limit]]

    def _to_video(self, item: dict, handle: str) -> Video:
        stats = item.get("stats", {}) or {}
        music = item.get("music", {}) or {}
        author = item.get("author", {}) or {}
        return Video(
            video_id=str(item.get("id")),
            handle=author.get("uniqueId") or handle,
            description=item.get("desc"),
            created_at=_ts(item.get("createTime")),
            duration_seconds=_int((item.get("video") or {}).get("duration")),
            views=_int(stats.get("playCount")),
            likes=_int(stats.get("diggCount")),
            comments=_int(stats.get("commentCount")),
            shares=_int(stats.get("shareCount")),
            saves=_int(stats.get("collectCount")),
            hashtags=[
                c.get("hashtagName") for c in (item.get("textExtra") or [])
                if c.get("hashtagName")
            ],
            music_title=music.get("title"),
            music_author=music.get("authorName"),
            cover_url=(item.get("video") or {}).get("cover"),
            source=self.name,
        )

    def close(self) -> None:
        for closer in (getattr(self, "_ctx", None), getattr(self, "_browser", None)):
            try:
                closer and closer.close()
            except Exception:
                pass
        try:
            self._pw.stop()
        except Exception:
            pass

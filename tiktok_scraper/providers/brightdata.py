"""Paid backend: Bright Data.

Two mechanisms, used for different jobs:

1. Web Scraper API datasets — you submit URLs, they run a *maintained* TikTok
   extractor and hand back structured JSON. Async: trigger -> poll -> fetch.
2. Web Unlocker — a proxy that returns raw HTML with the bot-wall solved. Used
   as a fallback for pages no dataset covers.

Dataset IDs are account/catalog specific, so they are configuration, not
constants. Copy them from your Bright Data dashboard
(Web Scraper API -> the TikTok scraper you want -> the gd_... id) into .env.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any, Iterable, Optional

import httpx

from ..models import Creator, Video
from .base import Provider, ProviderError

API_ROOT = "https://api.brightdata.com/datasets/v3"
POLL_INTERVAL_SECONDS = 10
POLL_TIMEOUT_SECONDS = 900  # TikTok jobs are slow; 15 min is a realistic ceiling


def _int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _dt(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _first(record: dict, *keys: str) -> Any:
    """Bright Data field names drift between dataset versions; accept aliases."""
    for key in keys:
        if record.get(key) not in (None, ""):
            return record[key]
    return None


class BrightDataProvider(Provider):
    name = "brightdata"

    def __init__(
        self,
        api_token: str | None = None,
        profile_dataset_id: str | None = None,
        post_dataset_id: str | None = None,
        **_,
    ):
        self._token = api_token or os.getenv("BRIGHTDATA_API_TOKEN", "")
        if not self._token:
            raise ProviderError(
                "BRIGHTDATA_API_TOKEN is not set. Add it to .env, or switch to "
                "TIKTOK_PROVIDER=playwright to run without a paid backend."
            )
        self._profile_dataset = profile_dataset_id or os.getenv("BRIGHTDATA_TIKTOK_PROFILE_DATASET", "")
        self._post_dataset = post_dataset_id or os.getenv("BRIGHTDATA_TIKTOK_POST_DATASET", "")
        self._client = httpx.Client(
            headers={"Authorization": f"Bearer {self._token}",
                     "Content-Type": "application/json"},
            timeout=60.0,
        )

    # ------------------------------------------------------------ dataset flow

    def _require_dataset(self, dataset_id: str, what: str) -> str:
        if not dataset_id:
            raise ProviderError(
                f"No Bright Data dataset id configured for {what}. Copy it from your "
                "dashboard (Web Scraper API -> TikTok -> the gd_... id) into .env as "
                f"BRIGHTDATA_TIKTOK_{'PROFILE' if what == 'profiles' else 'POST'}_DATASET."
            )
        return dataset_id

    def _run_dataset(self, dataset_id: str, payload: list[dict]) -> list[dict]:
        """Trigger a scrape job, wait for it, return its rows."""
        trigger = self._client.post(
            f"{API_ROOT}/trigger",
            params={"dataset_id": dataset_id, "include_errors": "true"},
            json=payload,
        )
        if trigger.status_code >= 400:
            raise ProviderError(
                f"Bright Data rejected the job ({trigger.status_code}): {trigger.text[:300]}"
            )
        snapshot_id = trigger.json().get("snapshot_id")
        if not snapshot_id:
            raise ProviderError(f"No snapshot_id in trigger response: {trigger.text[:300]}")

        deadline = time.time() + POLL_TIMEOUT_SECONDS
        while time.time() < deadline:
            progress = self._client.get(f"{API_ROOT}/progress/{snapshot_id}").json()
            status = progress.get("status")
            if status == "ready":
                break
            if status == "failed":
                raise ProviderError(f"Bright Data job failed: {progress}")
            time.sleep(POLL_INTERVAL_SECONDS)
        else:
            raise ProviderError(
                f"Bright Data job {snapshot_id} still running after "
                f"{POLL_TIMEOUT_SECONDS}s. It may finish later — check the dashboard."
            )

        rows = self._client.get(
            f"{API_ROOT}/snapshot/{snapshot_id}", params={"format": "json"}
        ).json()
        return rows if isinstance(rows, list) else [rows]

    # ---------------------------------------------------------------- mapping

    def _to_creator(self, rec: dict, fallback_handle: str = "") -> Creator:
        handle = str(_first(rec, "account_id", "username", "nickname") or fallback_handle).lstrip("@")
        return Creator(
            handle=handle,
            user_id=_first(rec, "id", "user_id"),
            nickname=_first(rec, "nickname", "name"),
            bio=_first(rec, "biography", "signature", "bio"),
            verified=_first(rec, "is_verified", "verified"),
            followers=_int(_first(rec, "followers", "follower_count")),
            following=_int(_first(rec, "following", "following_count")),
            total_likes=_int(_first(rec, "likes", "heart_count", "total_likes")),
            video_count=_int(_first(rec, "videos_count", "video_count")),
            avatar_url=_first(rec, "profile_pic_url", "avatar"),
            bio_link=_first(rec, "bio_link", "website"),
            region=_first(rec, "region", "country"),
            source=self.name,
        )

    def _to_video(self, rec: dict, fallback_handle: str = "", query: str | None = None) -> Video:
        url = str(_first(rec, "url", "post_url") or "")
        video_id = str(
            _first(rec, "post_id", "video_id", "id")
            or (url.rstrip("/").split("/")[-1] if url else "")
        )
        handle = str(
            _first(rec, "profile_username", "account_id", "username") or fallback_handle
        ).lstrip("@")
        hashtags = _first(rec, "hashtags") or []
        if isinstance(hashtags, str):
            hashtags = [h.strip() for h in hashtags.split(",") if h.strip()]
        hashtags = [
            (h.get("name") if isinstance(h, dict) else str(h)).lstrip("#")
            for h in hashtags
        ]

        return Video(
            video_id=video_id,
            handle=handle,
            description=_first(rec, "description", "desc", "caption"),
            created_at=_dt(_first(rec, "create_time", "date_posted", "created_at")),
            duration_seconds=_int(_first(rec, "video_duration", "duration")),
            views=_int(_first(rec, "play_count", "views", "play_count_number")),
            likes=_int(_first(rec, "digg_count", "likes", "like_count")),
            comments=_int(_first(rec, "comment_count", "comments")),
            shares=_int(_first(rec, "share_count", "shares")),
            saves=_int(_first(rec, "collect_count", "saves")),
            hashtags=[h for h in hashtags if h],
            music_title=_first(rec, "music_title", "original_sound"),
            music_author=_first(rec, "music_author"),
            cover_url=_first(rec, "preview_image", "cover"),
            matched_query=query,
            source=self.name,
        )

    # ------------------------------------------------------------ public API

    def fetch_creator(self, handle: str) -> Creator:
        handle = handle.lstrip("@")
        dataset = self._require_dataset(self._profile_dataset, "profiles")
        rows = self._run_dataset(dataset, [{"url": f"https://www.tiktok.com/@{handle}"}])
        if not rows:
            raise ProviderError(f"Bright Data returned no profile rows for @{handle}")
        return self._to_creator(rows[0], handle)

    def fetch_creator_videos(self, handle: str, limit: int = 30) -> list[Video]:
        handle = handle.lstrip("@")
        dataset = self._require_dataset(self._post_dataset, "posts")
        rows = self._run_dataset(
            dataset,
            [{"url": f"https://www.tiktok.com/@{handle}", "num_of_posts": limit}],
        )
        videos = [self._to_video(r, handle) for r in rows if not r.get("error")]
        return videos[:limit]

    def fetch_videos_by_url(self, urls: Iterable[str]) -> list[Video]:
        dataset = self._require_dataset(self._post_dataset, "posts")
        payload = [{"url": u} for u in urls]
        if not payload:
            return []
        rows = self._run_dataset(dataset, payload)
        return [self._to_video(r) for r in rows if not r.get("error")]

    def search_videos(self, query: str, limit: int = 30) -> list[Video]:
        dataset = self._require_dataset(self._post_dataset, "posts")
        tag = query.lstrip("#")
        rows = self._run_dataset(
            dataset,
            [{"url": f"https://www.tiktok.com/tag/{tag}", "num_of_posts": limit}],
        )
        return [self._to_video(r, query=query) for r in rows if not r.get("error")][:limit]

    def close(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass

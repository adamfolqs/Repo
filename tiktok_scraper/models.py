"""Normalized data schema.

Every provider (playwright, brightdata, ...) must emit these shapes, so the
sink layer and the resulting spreadsheet stay identical no matter what is
doing the fetching underneath.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, computed_field


class Creator(BaseModel):
    """A TikTok account."""

    handle: str = Field(description="Unique @name, without the @")
    user_id: Optional[str] = None
    nickname: Optional[str] = Field(default=None, description="Display name")
    bio: Optional[str] = None
    verified: Optional[bool] = None
    followers: Optional[int] = None
    following: Optional[int] = None
    total_likes: Optional[int] = None
    video_count: Optional[int] = None
    avatar_url: Optional[str] = None
    bio_link: Optional[str] = Field(default=None, description="Link in bio, often their storefront")
    region: Optional[str] = None

    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: Optional[str] = Field(default=None, description="Which provider produced this row")

    @computed_field
    @property
    def profile_url(self) -> str:
        return f"https://www.tiktok.com/@{self.handle}"


class Video(BaseModel):
    """A single TikTok post."""

    video_id: str
    handle: str = Field(description="Creator's @name, without the @")
    description: Optional[str] = Field(default=None, description="Caption text")
    created_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None

    # Engagement
    views: Optional[int] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    saves: Optional[int] = None

    # Context
    hashtags: list[str] = Field(default_factory=list)
    music_title: Optional[str] = None
    music_author: Optional[str] = None
    cover_url: Optional[str] = None

    # Provenance — how this row entered the dataset
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: Optional[str] = None
    matched_query: Optional[str] = Field(
        default=None,
        description="The keyword/hashtag/handle that surfaced this video, for attribution",
    )

    @computed_field
    @property
    def video_url(self) -> str:
        return f"https://www.tiktok.com/@{self.handle}/video/{self.video_id}"

    @computed_field
    @property
    def engagement_rate(self) -> Optional[float]:
        """(likes + comments + shares) / views, as a percentage.

        The headline number for judging whether a creator is worth contacting —
        a 5k-view video at 12% often beats a 500k-view video at 0.8%.
        """
        if not self.views:
            return None
        interactions = (self.likes or 0) + (self.comments or 0) + (self.shares or 0)
        return round(interactions / self.views * 100, 2)


# Column order for the spreadsheet. Explicit, so the sheet is stable across
# runs and safe to append to.
VIDEO_COLUMNS = [
    "video_url", "handle", "description", "created_at", "duration_seconds",
    "views", "likes", "comments", "shares", "saves", "engagement_rate",
    "hashtags", "music_title", "music_author",
    "matched_query", "video_id", "cover_url", "scraped_at", "source",
]

CREATOR_COLUMNS = [
    "handle", "profile_url", "nickname", "followers", "following",
    "total_likes", "video_count", "verified", "bio", "bio_link",
    "region", "user_id", "avatar_url", "scraped_at", "source",
]
